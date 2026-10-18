import os
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db, DATABASE_URL
from app.models import User

def validate_secret():
    configured = os.getenv("SECRET_KEY", "").strip()
    if DATABASE_URL.startswith("postgresql") and len(configured) < 32:
        raise RuntimeError("SECRET_KEY must contain at least 32 characters when using PostgreSQL")
    return configured


SECRET_KEY = validate_secret()
if len(SECRET_KEY) < 32:
    SECRET_KEY = secrets.token_urlsafe(48)
    logging.getLogger("jtickets.auth").warning("Using a random per-process development JWT key; tokens expire on restart")
ALGORITHM  = "HS256"
TOKEN_TTL  = 24  # hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer renders a plain "Value" field in Swagger — paste your token directly.
bearer_scheme = HTTPBearer(auto_error=False)


def hash_pw(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_pw(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user: User) -> str:
    payload = {
        "sub":   str(user.id),
        "role":  user.role,
        "email": user.email,
        "exp":   datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode(token: str, db: Session) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token — get a fresh one from POST /login",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, TypeError, ValueError, KeyError):
        raise exc
    user = db.get(User, user_id)
    if not user:
        raise exc
    return user


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db:    Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — click Authorize and paste your Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode(creds.credentials, db)


def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db:    Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    try:
        return _decode(creds.credentials, db)
    except HTTPException:
        return None


def require_role(role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied — '{role}' role required",
            )
        return user
    return checker
