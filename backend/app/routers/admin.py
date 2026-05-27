from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..auth import require_admin
from ..database.models import get_db, Disease, Pesticide, User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# --- Diseases CRUD ---
@router.get("/diseases")
def list_diseases(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(Disease).order_by(Disease.crop, Disease.name_vi).all()


@router.post("/diseases")
def create_disease(data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    disease = Disease(**{k: v for k, v in data.items() if hasattr(Disease, k)})
    disease.updated_by = admin.id
    db.add(disease)
    db.commit()
    db.refresh(disease)
    return disease


@router.put("/diseases/{disease_id}")
def update_disease(disease_id: int, data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.items():
        if hasattr(disease, k) and k != "id":
            setattr(disease, k, v)
    disease.updated_by = admin.id
    db.commit()
    return disease


@router.delete("/diseases/{disease_id}")
def delete_disease(disease_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(disease)
    db.commit()
    return {"ok": True}


# --- Pesticides CRUD ---
@router.get("/pesticides")
def list_pesticides(
    q: Optional[str] = None, category: Optional[str] = None,
    page: int = 0, size: int = 50,
    db: Session = Depends(get_db), admin: User = Depends(require_admin),
):
    query = db.query(Pesticide)
    if q:
        query = query.filter(Pesticide.name.ilike(f"%{q}%") | Pesticide.active_ingredient.ilike(f"%{q}%") | Pesticide.company.ilike(f"%{q}%"))
    if category:
        query = query.filter(Pesticide.category == category)
    total = query.count()
    items = query.offset(page * size).limit(size).all()
    return {"total": total, "items": items}


@router.post("/pesticides")
def create_pesticide(data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p = Pesticide(**{k: v for k, v in data.items() if hasattr(Pesticide, k)})
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/pesticides/{pid}")
def update_pesticide(pid: int, data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p = db.query(Pesticide).filter(Pesticide.id == pid).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.items():
        if hasattr(p, k) and k != "id":
            setattr(p, k, v)
    db.commit()
    return p


@router.delete("/pesticides/{pid}")
def delete_pesticide(pid: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p = db.query(Pesticide).filter(Pesticide.id == pid).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(p)
    db.commit()
    return {"ok": True}


# --- Users ---
@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users")
def create_user(data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..auth import hash_password
    phone = data.get("phone", "")
    password = data.get("password", "")
    if len(phone) < 9 or len(password) < 6:
        raise HTTPException(status_code=400, detail="Invalid phone or password")
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="Phone already exists")
    user = User(phone=phone, password_hash=hash_password(password), name=data.get("name", ""), role=data.get("role", "user"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/role")
def set_role(user_id: int, data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    user.role = data.get("role", "user")
    db.commit()
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"ok": True}
