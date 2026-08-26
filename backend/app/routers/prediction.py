from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from PIL import Image
import io

from ..models.vlm import predict_vlm
from ..schemas.prediction import ModelsResponse, PredictionResponse
from ..database.models import get_db, Setting

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.get("/config")
async def get_public_config(db: Session = Depends(get_db)):
    ios_setting = db.query(Setting).filter(Setting.key == "app_ios_url").first()
    android_setting = db.query(Setting).filter(Setting.key == "app_android_url").first()
    return {
        "app_ios_url": ios_setting.value if ios_setting is not None else "https://apps.apple.com/app/plantdoctor",
        "app_android_url": android_setting.value if android_setting is not None else "https://benhcay.tuaf.edu.vn/plantdoctor.apk",
    }


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    models = [{"id": "gpt55_vision", "name": "PlantDoctor AI", "description": "PlantDoctor AI engine", "classes": 0}]
    return ModelsResponse(models=models)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    model_id: str = Form("gpt55_vision"),
    lang: str = Form("vi"),
    db: Session = Depends(get_db),
):
    if lang not in ("vi", "en"):
        lang = "vi"

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    result = predict_vlm(image, lang, db)

    if result is None:
        raise HTTPException(status_code=500, detail="Prediction failed")

    return PredictionResponse(**result)
