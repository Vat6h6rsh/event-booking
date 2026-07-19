from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, User
from app import auth, schemas

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[schemas.NotificationOut])
def my_notifications(unread_only: bool = False,
                    db: Session = Depends(get_db),
                    user: User = Depends(auth.get_current_user)):
    """In-app notifications for the current user (own only) — newest first.

    These are written by the background tasks, so this endpoint is the UI-visible
    proof that Background Task 2 (event-update notification) actually ran.
    """
    q = db.query(Notification).filter_by(user_id=user.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    return q.order_by(Notification.created_at.desc()).all()


@router.post("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(notification_id: int, db: Session = Depends(get_db),
             user: User = Depends(auth.get_current_user)):
    n = db.get(Notification, notification_id)
    if not n:
        raise HTTPException(404, "Notification not found")
    if n.user_id != user.id:
        raise HTTPException(403, "Access denied")
    n.is_read = True
    db.commit(); db.refresh(n)
    return n


@router.post("/read-all", status_code=204)
def mark_all_read(db: Session = Depends(get_db),
                 user: User = Depends(auth.get_current_user)):
    (db.query(Notification)
       .filter_by(user_id=user.id, is_read=False)
       .update({Notification.is_read: True}))
    db.commit()
