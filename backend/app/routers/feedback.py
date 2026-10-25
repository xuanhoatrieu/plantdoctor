"""User feedback on diagnosis results (thumbs up/down) + expert review endpoints for admins.

Public:  POST /api/v1/feedback                 (guests allowed, rate-limited per client IP)
Admin:   GET  /api/v1/admin/feedback           (filter + pagination)
         GET  /api/v1/admin/feedback/stats
         PUT  /api/v1/admin/feedback/{id}      (mark reviewed + expert note)
"""
import logging
import threading
from datetime import datetime, timedelta
from typing import Literal, Optional

from cachetools import TTLCache
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_optional_user, require_admin
from ..database.models import DiagnosisFeedback, User, get_db
from ..rate_limit import client_ip
from ..schemas.prediction import FeedbackCreate, FeedbackReview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["feedback"])
admin_router = APIRouter(prefix="/api/v1/admin/feedback", tags=["admin"])

# --- Simple in-memory rate limit: max N feedback submissions per client IP per window ---
# TODO(security): this is per-process memory. If the API is scaled to several workers/instances,
# move the counter to a shared store (e.g. Redis) or enforce the limit at the reverse proxy.
FEEDBACK_RATE_LIMIT = 20
FEEDBACK_RATE_WINDOW_SECONDS = 600
_rate_counter: TTLCache = TTLCache(maxsize=10000, ttl=FEEDBACK_RATE_WINDOW_SECONDS)
_rate_lock = threading.Lock()


_client_ip = client_ip  # shared helper (see app/rate_limit.py for the X-Forwarded-For reasoning)


def _check_rate_limit(ip: str) -> None:
    with _rate_lock:
        count = _rate_counter.get(ip, 0)
        if count >= FEEDBACK_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Bạn gửi phản hồi quá nhanh. Vui lòng thử lại sau ít phút.")
        _rate_counter[ip] = count + 1


# Feedback must never fail only because a stored mobile token has expired -> invalid token = guest.
_optional_user = get_optional_user


def _mask_phone(phone: str) -> str:
    if not phone:
        return ""
    if len(phone) <= 4:
        return "*" * len(phone)
    return f"{phone[:2]}{'*' * (len(phone) - 4)}{phone[-2:]}"


def _serialize(fb: DiagnosisFeedback, user: Optional[User]) -> dict:
    return {
        "id": fb.id,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
        "platform": fb.platform or "",
        "is_correct": bool(fb.is_correct),
        "reason": fb.reason or "",
        "correct_plant": fb.correct_plant or "",
        "correct_disease": fb.correct_disease or "",
        "comment": fb.comment or "",
        "predicted_name": fb.predicted_name or "",
        "predicted_label": fb.predicted_label or "",
        "predicted_confidence": fb.predicted_confidence or 0,
        "plant_hint": fb.plant_hint or "",
        "image_count": fb.image_count or 1,
        "was_clarified": bool(fb.was_clarified),
        "reviewed": bool(fb.reviewed),
        "expert_note": fb.expert_note or "",
        "reviewed_at": fb.reviewed_at.isoformat() if fb.reviewed_at else None,
        # PII: only a display name and a masked phone are exposed to admins
        "user": {"name": user.name or "", "phone": _mask_phone(user.phone)} if user else None,
    }


@router.post("/feedback")
def submit_feedback(
    payload: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(_optional_user),
):
    _check_rate_limit(_client_ip(request))

    # A positive vote carries no correction fields; keep the stored row clean.
    is_correct = payload.is_correct
    fb = DiagnosisFeedback(
        user_id=user.id if user else None,
        platform=payload.platform,
        is_correct=is_correct,
        reason="" if is_correct else payload.reason,
        correct_plant="" if is_correct else payload.correct_plant.strip(),
        correct_disease="" if is_correct else payload.correct_disease.strip(),
        comment=payload.comment.strip(),
        predicted_name=payload.predicted_name.strip(),
        predicted_label=payload.predicted_label.strip(),
        predicted_confidence=int(round(payload.predicted_confidence)),
        plant_hint=payload.plant_hint.strip(),
        image_count=payload.image_count,
        was_clarified=payload.was_clarified,
    )
    try:
        db.add(fb)
        db.commit()
        db.refresh(fb)
    except Exception:
        db.rollback()
        logger.exception("Failed to store diagnosis feedback")
        raise HTTPException(status_code=500, detail="Không thể lưu phản hồi lúc này. Vui lòng thử lại sau.")
    logger.info("Stored diagnosis feedback id=%s correct=%s reason=%s", fb.id, fb.is_correct, fb.reason)
    return {"ok": True, "id": fb.id}


@admin_router.get("")
def list_feedback(
    verdict: Literal["all", "correct", "incorrect"] = "all",
    reviewed: Literal["all", "yes", "no"] = "all",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(DiagnosisFeedback)
    if verdict == "correct":
        q = q.filter(DiagnosisFeedback.is_correct.is_(True))
    elif verdict == "incorrect":
        q = q.filter(DiagnosisFeedback.is_correct.is_(False))
    if reviewed == "yes":
        q = q.filter(DiagnosisFeedback.reviewed.is_(True))
    elif reviewed == "no":
        q = q.filter(DiagnosisFeedback.reviewed.is_(False))

    total = q.count()
    rows = (
        q.order_by(DiagnosisFeedback.created_at.desc(), DiagnosisFeedback.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    user_ids = {r.user_id for r in rows if r.user_id}
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize(r, users.get(r.user_id)) for r in rows],
    }


@admin_router.get("/stats")
def feedback_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    total = db.query(func.count(DiagnosisFeedback.id)).scalar() or 0
    correct = db.query(func.count(DiagnosisFeedback.id)).filter(DiagnosisFeedback.is_correct.is_(True)).scalar() or 0
    unreviewed_incorrect = (
        db.query(func.count(DiagnosisFeedback.id))
        .filter(DiagnosisFeedback.is_correct.is_(False), DiagnosisFeedback.reviewed.is_(False))
        .scalar()
        or 0
    )
    since = datetime.utcnow() - timedelta(days=30)
    total_30d = db.query(func.count(DiagnosisFeedback.id)).filter(DiagnosisFeedback.created_at >= since).scalar() or 0
    correct_30d = (
        db.query(func.count(DiagnosisFeedback.id))
        .filter(DiagnosisFeedback.created_at >= since, DiagnosisFeedback.is_correct.is_(True))
        .scalar()
        or 0
    )
    reason_rows = (
        db.query(DiagnosisFeedback.reason, func.count(DiagnosisFeedback.id))
        .filter(DiagnosisFeedback.is_correct.is_(False))
        .group_by(DiagnosisFeedback.reason)
        .all()
    )
    return {
        "total": total,
        "correct": correct,
        "incorrect": total - correct,
        "user_reported_accuracy": round(correct * 100 / total, 1) if total else None,
        "unreviewed_incorrect": unreviewed_incorrect,
        "last_30_days": {
            "total": total_30d,
            "correct": correct_30d,
            "user_reported_accuracy": round(correct_30d * 100 / total_30d, 1) if total_30d else None,
        },
        "by_reason": {(reason or "unspecified"): count for reason, count in reason_rows},
    }


@admin_router.put("/{feedback_id}")
def review_feedback(
    feedback_id: int,
    payload: FeedbackReview,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    fb = db.query(DiagnosisFeedback).filter(DiagnosisFeedback.id == feedback_id).first()
    if fb is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi")
    fb.reviewed = payload.reviewed
    fb.expert_note = payload.expert_note.strip()
    fb.reviewed_at = datetime.utcnow() if payload.reviewed else None
    fb.reviewed_by = admin.id if payload.reviewed else None
    db.commit()
    user = db.query(User).filter(User.id == fb.user_id).first() if fb.user_id else None
    return _serialize(fb, user)
