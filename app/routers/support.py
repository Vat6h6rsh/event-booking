from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SupportTicket, ChatMessage, User
from app import auth, schemas

router = APIRouter(prefix="/support", tags=["support"])

@router.post("/tickets", response_model=schemas.SupportTicketOut, status_code=201)
def create_ticket(body: schemas.SupportTicketCreate, db: Session = Depends(get_db),
                  user: User = Depends(auth.get_current_user)):
    t = SupportTicket(user_id=user.id, **body.model_dump())
    db.add(t); db.commit(); db.refresh(t)
    return t

@router.get("/tickets", response_model=list[schemas.SupportTicketOut])
def list_tickets(db: Session = Depends(get_db),
                 user: User = Depends(auth.get_current_user)):
    return (db.query(SupportTicket)
              .filter_by(user_id=user.id)
              .order_by(SupportTicket.created_at.desc())
              .all())

@router.get("/tickets/{ticket_id}", response_model=schemas.SupportTicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db),
               user: User = Depends(auth.get_current_user)):
    t = db.get(SupportTicket, ticket_id)
    if not t: raise HTTPException(404, "Support ticket not found")
    if t.user_id != user.id and user.role != "organizer":
        raise HTTPException(403, "Access denied")
    return t

@router.put("/tickets/{ticket_id}", response_model=schemas.SupportTicketOut)
def update_ticket(ticket_id: int, body: schemas.SupportTicketUpdate,
                  db: Session = Depends(get_db),
                  user: User = Depends(auth.get_current_user)):
    t = db.get(SupportTicket, ticket_id)
    if not t: raise HTTPException(404, "Support ticket not found")
    if t.user_id != user.id and user.role != "organizer":
        raise HTTPException(403, "Access denied")
    if body.status:
        if body.status == "resolved":
            t.resolved_at = datetime.now(timezone.utc)
        t.status = body.status
    if body.priority:
        t.priority = body.priority
    db.commit(); db.refresh(t)
    return t

@router.post("/tickets/{ticket_id}/messages", response_model=schemas.ChatMessageOut, status_code=201)
def add_message(ticket_id: int, body: schemas.ChatMessageCreate,
                db: Session = Depends(get_db),
                user: User = Depends(auth.get_current_user)):
    t = db.get(SupportTicket, ticket_id)
    if not t: raise HTTPException(404, "Support ticket not found")
    if t.user_id != user.id and user.role != "organizer":
        raise HTTPException(403, "Access denied")
    if t.status == "closed":
        raise HTTPException(409, "Cannot reply to a closed ticket")
    msg = ChatMessage(ticket_id=ticket_id, sender_id=user.id,
                      message=body.message, is_staff=(user.role == "organizer"))
    db.add(msg)
    if t.status == "open" and user.role == "organizer":
        t.status = "in_progress"
    db.commit(); db.refresh(msg)
    result = schemas.ChatMessageOut.model_validate(msg)
    result.sender_email = user.email
    return result

@router.get("/tickets/{ticket_id}/messages", response_model=list[schemas.ChatMessageOut])
def get_messages(ticket_id: int, db: Session = Depends(get_db),
                 user: User = Depends(auth.get_current_user)):
    t = db.get(SupportTicket, ticket_id)
    if not t: raise HTTPException(404, "Support ticket not found")
    if t.user_id != user.id and user.role != "organizer":
        raise HTTPException(403, "Access denied")
    msgs = (db.query(ChatMessage)
              .filter_by(ticket_id=ticket_id)
              .order_by(ChatMessage.created_at)
              .all())
    results = []
    for m in msgs:
        r = schemas.ChatMessageOut.model_validate(m)
        r.sender_email = m.sender.email if m.sender else None
        results.append(r)
        if m.sender_id != user.id:
            m.is_read = True
    db.commit()
    return results
