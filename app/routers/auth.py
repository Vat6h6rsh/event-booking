from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app import auth, schemas

router = APIRouter(tags=["auth"])

@router.post("/signup", response_model=schemas.UserOut, status_code=201)
def signup(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=body.email,
        hashed_password=auth.hash_pw(body.password),
        role=body.role,
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=form.username).first()
    if not user or not auth.verify_pw(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": auth.create_token(user), "token_type": "bearer", "user": user}
