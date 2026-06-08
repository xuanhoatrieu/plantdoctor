from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..auth import require_admin
from ..database.models import get_db, Disease, Pesticide, User, Setting

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


# --- Settings ---
@router.get("/settings")
def get_settings(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    db_settings = db.query(Setting).all()
    settings_dict = {s.key: s.value for s in db_settings}
    
    # Defaults
    defaults = {
        "llm_provider": "cliproxy",
        "llm_api_url": "http://152.67.112.145:8317/v1/chat/completions",
        "llm_api_key": "ai-teaching-assistant-prod",
        "llm_model_name": "gpt-5.5",
    }
    for k, v in defaults.items():
        if k not in settings_dict:
            settings_dict[k] = v
            
    # Mask API key for security
    raw_key = settings_dict.get("llm_api_key", "")
    if raw_key:
        if len(raw_key) > 8:
            masked_key = raw_key[:4] + "•" * (len(raw_key) - 8) + raw_key[-4:]
        else:
            masked_key = "•" * len(raw_key)
        settings_dict["llm_api_key"] = masked_key
        
    return settings_dict


@router.put("/settings")
def update_settings(data: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    for k, v in data.items():
        if k in ("llm_provider", "llm_api_url", "llm_api_key", "llm_model_name"):
            # Avoid overwriting with masked key
            if k == "llm_api_key" and v and "•" in str(v):
                continue
            
            setting = db.query(Setting).filter(Setting.key == k).first()
            if not setting:
                setting = Setting(key=k, value=str(v))
                db.add(setting)
            else:
                setting.value = str(v)
    db.commit()
    return {"ok": True}


@router.post("/settings/models")
def test_connection_and_list_models(
    data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    import urllib.request
    import json
    
    provider = data.get("llm_provider", "cliproxy")
    api_url = data.get("llm_api_url", "")
    api_key = data.get("llm_api_key", "")
    
    # Resolve masked key
    if api_key and "•" in str(api_key):
        db_key = db.query(Setting).filter(Setting.key == "llm_api_key").first()
        if db_key:
            api_key = db_key.value
        else:
            if provider == "cliproxy":
                api_key = "ai-teaching-assistant-prod"
            else:
                api_key = ""
                
    if provider == "cliproxy" and not api_key:
        api_key = "ai-teaching-assistant-prod"
        
    try:
        models = []
        if provider in ("cliproxy", "openai"):
            # Compute models endpoint URL
            if not api_url:
                if provider == "cliproxy":
                    api_url = "http://152.67.112.145:8317/v1/chat/completions"
                else:
                    api_url = "https://api.openai.com/v1/chat/completions"
                    
            models_url = api_url.replace("/chat/completions", "/models")
            
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            req = urllib.request.Request(models_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode())
                
            models = [m["id"] for m in resp_data.get("data", []) if "id" in m]
            
        elif provider == "google":
            if not api_key:
                raise ValueError("API Key is required for Google Gemini")
                
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode())
                
            for m in resp_data.get("models", []):
                name = m.get("name", "")
                if name.startswith("models/"):
                    name = name[7:]
                if "gemini" in name:
                    models.append(name)
        else:
            raise ValueError(f"Unknown provider: {provider}")
            
        # Fallback list if no models returned
        if not models:
            if provider == "cliproxy":
                models = ["gpt-5.5"]
            elif provider == "openai":
                models = ["gpt-4o", "gpt-4o-mini", "o1-mini", "gpt-4-turbo"]
            elif provider == "google":
                models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-pro-exp"]
                
        return {"ok": True, "models": models}
        
    except Exception as e:
        if hasattr(e, 'read'):
            try:
                err_detail = json.loads(e.read().decode())
                detail_msg = err_detail.get("error", {}).get("message", str(e))
            except:
                detail_msg = str(e)
        else:
            detail_msg = str(e)
        raise HTTPException(status_code=400, detail=f"Connection failed: {detail_msg}")
