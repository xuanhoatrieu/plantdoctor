from fastapi import Depends, HTTPException, Header
from typing import Optional
import hashlib
import jwt
import os

from .database.models import get_db, User
from sqlalchemy.orm import Session

SECRET_KEY = os.getenv("SECRET_KEY", "plantdoctor-secret-key-change-in-production")


def hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def create_token(user_id: int, role: str) -> str:
    return jwt.encode({"user_id": user_id, "role": role}, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    data = decode_token(token)
    user = db.query(User).filter(User.id == data["user_id"]).first()
    return user


async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user


async def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
