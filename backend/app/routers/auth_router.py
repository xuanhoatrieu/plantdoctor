from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.models import get_db, User
from ..auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    phone: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    phone: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.phone) < 9:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    existing = db.query(User).filter(User.phone == req.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = User(phone=req.phone, password_hash=hash_password(req.password), name=req.name, role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.role)
    return {"token": token, "user": {"id": user.id, "phone": user.phone, "name": user.name, "role": user.role}}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    token = create_token(user.id, user.role)
    return {"token": token, "user": {"id": user.id, "phone": user.phone, "name": user.name, "role": user.role}}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": user.id, "phone": user.phone, "name": user.name, "role": user.role}
