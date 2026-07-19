from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app import auth, schemas

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.UserOut)
def get_me(user: User = Depends(auth.get_current_user)):
    return user

@router.put("/me", response_model=schemas.UserOut)
def update_me(body: schemas.UserUpdate, db: Session = Depends(get_db),
              user: User = Depends(auth.get_current_user)):
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit(); db.refresh(user)
    return user
