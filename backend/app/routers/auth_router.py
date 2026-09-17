from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from ..database.models import get_db, User
from ..auth import hash_password, verify_password, create_token, get_current_user, require_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    phone: str
    password: str
    name: str = ""
    email: Optional[str] = None


class LoginRequest(BaseModel):
    phone: str
    password: str


class AppleLoginRequest(BaseModel):
    identity_token: str
    name: str = ""


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: Optional[str] = None
    reason: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    phone: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.phone) < 9:
        raise HTTPException(status_code=400, detail="Số điện thoại không hợp lệ (tối thiểu 9 số)")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có tối thiểu 6 ký tự")
    existing = db.query(User).filter(User.phone == req.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Số điện thoại này đã được đăng ký")
    user = User(
        phone=req.phone,
        password_hash=hash_password(req.password),
        name=req.name,
        email=req.email,
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.role)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "phone": user.phone,
            "name": user.name or "",
            "email": user.email or "",
            "avatar_url": user.avatar_url or "",
            "role": user.role,
        },
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Số điện thoại hoặc mật khẩu không chính xác")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Số điện thoại hoặc mật khẩu không chính xác")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa bởi quản trị viên. Vui lòng liên hệ hỗ trợ.")
    token = create_token(user.id, user.role)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "phone": user.phone,
            "name": user.name or "",
            "email": user.email or "",
            "avatar_url": user.avatar_url or "",
            "role": user.role,
        },
    }


@router.get("/me")
def me(user: User = Depends(require_user)):
    return {
        "id": user.id,
        "phone": user.phone,
        "name": user.name or "",
        "email": user.email or "",
        "avatar_url": user.avatar_url or "",
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if req.name is not None:
        user.name = req.name.strip()
    if req.email is not None:
        user.email = req.email.strip()
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url.strip()
    db.commit()
    db.refresh(user)
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "phone": user.phone,
            "name": user.name or "",
            "email": user.email or "",
            "avatar_url": user.avatar_url or "",
            "role": user.role,
        },
    }


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if user.password_hash:
        if not verify_password(req.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có tối thiểu 6 ký tự")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"ok": True, "message": "Đổi mật khẩu thành công"}


@router.delete("/me")
def delete_account(
    req: Optional[DeleteAccountRequest] = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    # Apple App Store & Google Play requirement: Users must be able to delete their account in-app
    if user.password_hash and not user.phone.startswith("apple_"):
        if not req or not req.password:
            raise HTTPException(status_code=400, detail="Vui lòng nhập mật khẩu để xác nhận xóa tài khoản")
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Mật khẩu xác nhận không chính xác")

    user_id = user.id
    db.delete(user)
    db.commit()
    return {"ok": True, "message": f"Tài khoản ID {user_id} đã được xóa thành công"}


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Support hotline / email for password reset
    return {
        "ok": True,
        "message": "Vui lòng liên hệ bộ phận hỗ trợ kỹ thuật PlantDoctor (TUAF) qua hotline 0944550007 hoặc email trieuxuanhoa@tuaf.edu.vn để được xác minh danh tính và đặt lại mật khẩu.",
        "support_phone": "0944550007",
        "support_email": "trieuxuanhoa@tuaf.edu.vn",
    }


@router.post("/apple")
def apple_login(req: AppleLoginRequest, db: Session = Depends(get_db)):
    import jwt as pyjwt

    try:
        # Decode without verification to get the subject (Apple user ID)
        payload = pyjwt.decode(req.identity_token, options={"verify_signature": False})
        apple_sub = payload.get("sub")
        email = payload.get("email", "")
        if not apple_sub:
            raise HTTPException(status_code=400, detail="Invalid Apple token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Apple token")

    # Find or create user by apple ID (stored in firebase_uid field)
    user = db.query(User).filter(User.firebase_uid == f"apple_{apple_sub}").first()
    if not user:
        # Create new user
        user = User(
            phone=f"apple_{apple_sub[:8]}",
            firebase_uid=f"apple_{apple_sub}",
            name=req.name or (email.split("@")[0] if email else "Apple User"),
            email=email if email else None,
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị tạm khóa. Vui lòng liên hệ hỗ trợ.")

    token = create_token(user.id, user.role)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "phone": user.phone,
            "name": user.name or "",
            "email": user.email or "",
            "avatar_url": user.avatar_url or "",
            "role": user.role,
        },
    }
