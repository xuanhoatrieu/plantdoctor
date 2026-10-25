import io
from typing import Optional, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from ..auth import get_optional_user
from ..models.vlm import predict_vlm, clarify_vlm, assess_image_quality
from ..rate_limit import SlidingWindowLimiter, client_ip, env_int
from ..schemas.prediction import ModelsResponse, PredictionResponse, ClarifyRequest
from ..database.models import get_db, Setting, User, Disease

router = APIRouter(prefix="/api/v1", tags=["prediction"])

# --- AI cost / abuse protection -------------------------------------------------------------
# Each diagnosis may trigger up to 3 paid AI calls (self-consistency voting), so it is limited per caller.
# Logged-in users are keyed by account (cannot be spoofed). Guests are keyed by IP; their limit is higher
# because a whole school lab or farm cooperative can share one public IP behind NAT.
# /predict and /predict/clarify share the same bucket. Tune with env vars without a rebuild.
PREDICT_RATE_WINDOW_SECONDS = env_int("PREDICT_RATE_WINDOW_SECONDS", 600)
PREDICT_RATE_LIMIT_USER = env_int("PREDICT_RATE_LIMIT_USER", 40)
PREDICT_RATE_LIMIT_GUEST = env_int("PREDICT_RATE_LIMIT_GUEST", 60)
user_limiter = SlidingWindowLimiter(PREDICT_RATE_LIMIT_USER, PREDICT_RATE_WINDOW_SECONDS)
guest_limiter = SlidingWindowLimiter(PREDICT_RATE_LIMIT_GUEST, PREDICT_RATE_WINDOW_SECONDS)


def _enforce_predict_limit(request: Request, user: Optional[User], lang: str) -> None:
    message = (
        "Bạn đã chẩn đoán quá nhiều ảnh trong thời gian ngắn. Vui lòng thử lại sau ít phút."
        if lang != "en"
        else "Too many diagnoses in a short time. Please try again in a few minutes."
    )
    if user is not None:
        user_limiter.enforce(f"user:{user.id}", message)
    else:
        guest_limiter.enforce(f"ip:{client_ip(request)}", message)


@router.get("/config")
async def get_public_config(db: Session = Depends(get_db)):
    ios_setting = db.query(Setting).filter(Setting.key == "app_ios_url").first()
    android_setting = db.query(Setting).filter(Setting.key == "app_android_url").first()
    return {
        "app_ios_url": ios_setting.value if ios_setting is not None else "https://apps.apple.com/vn/app/tuaf-plantdoctor/id6773555310",
        "app_android_url": android_setting.value if android_setting is not None else "https://play.google.com/store/apps/details?id=com.trieuxuanhoa.plantdoctor&pcampaignid=web_share",
    }


@router.get("/diseases")
async def get_public_diseases(crop: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Disease).order_by(Disease.crop, Disease.name_vi)
    if crop and crop.strip():
        query = query.filter(Disease.crop.ilike(f"%{crop.strip()}%"))
    return query.all()


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    models = [{"id": "gpt55_vision", "name": "PlantDoctor AI", "description": "PlantDoctor AI engine", "classes": 0}]
    return ModelsResponse(models=models)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    model_id: str = Form("gpt55_vision"),
    plant_hint: Optional[str] = Form(None),
    lang: str = Form("vi"),
    # Opt-in: only new clients send quality_gate=true. Old store builds never send it and would not
    # understand a "low_quality" response with empty predictions, so they keep the old behaviour.
    quality_gate: bool = Form(False),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if lang not in ("vi", "en"):
        lang = "vi"
    _enforce_predict_limit(request, user, lang)

    # Normalize plant_hint if empty string
    if plant_hint and not plant_hint.strip():
        plant_hint = None
    elif plant_hint:
        # The hint is interpolated into the AI prompt: keep it short.
        plant_hint = plant_hint.strip()[:100]

    # Collect all uploaded files (supports single file or multiple files)
    all_files: List[UploadFile] = []
    if files:
        all_files.extend(files)
    if file:
        all_files.append(file)

    if not all_files:
        raise HTTPException(status_code=400, detail="Không tìm thấy tệp ảnh tải lên")

    images: List[Image.Image] = []
    for f in all_files[:3]:  # Max 3 images
        contents = await f.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Dung lượng tệp quá lớn (tối đa 10MB mỗi ảnh)")

        try:
            img = Image.open(io.BytesIO(contents)).convert("RGB")
            images.append(img)
        except Exception:
            raise HTTPException(status_code=400, detail="Tệp ảnh không hợp lệ")

    # Quality gate runs BEFORE the AI call, so a rejected photo costs nothing.
    # The client can override by re-sending the same photos with quality_gate=false.
    if quality_gate:
        codes: List[str] = []
        messages: List[str] = []
        multi = len(images) > 1
        for idx, img in enumerate(images):
            q = assess_image_quality(img, lang)
            for code, msg in zip(q["issues"], q["messages"]):
                if code not in codes:
                    codes.append(code)
                if multi:
                    prefix = f"Ảnh {idx + 1}: " if lang == "vi" else f"Image {idx + 1}: "
                    msg = prefix + msg
                messages.append(msg)
        if codes:
            return PredictionResponse(
                model_id="plantdoctor_ai",
                model_name="PlantDoctor AI",
                predictions=[],
                status="low_quality",
                image_quality_warnings=messages,
                quality_issues=codes,
            )

    result = predict_vlm(images=images, lang=lang, db=db, plant_hint=plant_hint)

    if result is None:
        raise HTTPException(status_code=500, detail="Quá trình chẩn đoán AI gặp sự cố")

    return PredictionResponse(**result)


@router.post("/predict/clarify", response_model=PredictionResponse)
async def clarify(
    req: ClarifyRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    lang = req.lang if req.lang in ("vi", "en") else "vi"
    _enforce_predict_limit(request, user, lang)
    result = clarify_vlm(
        session_token=req.session_token,
        selected_plant=req.selected_plant,
        lang=lang,
        db=db,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Phiên làm rõ đã hết hạn hoặc không tìm thấy. Vui lòng thử chụp lại ảnh.",
        )
    return PredictionResponse(**result)
