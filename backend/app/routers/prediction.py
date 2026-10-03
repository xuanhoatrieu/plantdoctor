import io
from typing import Optional, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from ..models.vlm import predict_vlm, clarify_vlm
from ..schemas.prediction import ModelsResponse, PredictionResponse, ClarifyRequest
from ..database.models import get_db, Setting

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.get("/config")
async def get_public_config(db: Session = Depends(get_db)):
    ios_setting = db.query(Setting).filter(Setting.key == "app_ios_url").first()
    android_setting = db.query(Setting).filter(Setting.key == "app_android_url").first()
    return {
        "app_ios_url": ios_setting.value if ios_setting is not None else "https://apps.apple.com/vn/app/tuaf-plantdoctor/id6773555310",
        "app_android_url": android_setting.value if android_setting is not None else "https://play.google.com/store/apps/details?id=com.trieuxuanhoa.plantdoctor&pcampaignid=web_share",
    }


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    models = [{"id": "gpt55_vision", "name": "PlantDoctor AI", "description": "PlantDoctor AI engine", "classes": 0}]
    return ModelsResponse(models=models)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    model_id: str = Form("gpt55_vision"),
    plant_hint: Optional[str] = Form(None),
    lang: str = Form("vi"),
    db: Session = Depends(get_db),
):
    if lang not in ("vi", "en"):
        lang = "vi"

    # Normalize plant_hint if empty string
    if plant_hint and not plant_hint.strip():
        plant_hint = None
    elif plant_hint:
        plant_hint = plant_hint.strip()

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

    result = predict_vlm(images=images, lang=lang, db=db, plant_hint=plant_hint)

    if result is None:
        raise HTTPException(status_code=500, detail="Quá trình chẩn đoán AI gặp sự cố")

    return PredictionResponse(**result)


@router.post("/predict/clarify", response_model=PredictionResponse)
async def clarify(
    req: ClarifyRequest,
    db: Session = Depends(get_db),
):
    lang = req.lang if req.lang in ("vi", "en") else "vi"
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
