from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image
import io

from ..models.vlm import predict_vlm
from ..schemas.prediction import ModelsResponse, PredictionResponse

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    models = [{"id": "gpt55_vision", "name": "PlantDoctor AI", "description": "PlantDoctor AI engine", "classes": 0}]
    return ModelsResponse(models=models)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    model_id: str = Form("gpt55_vision"),
    lang: str = Form("vi"),
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

    result = predict_vlm(image, lang)

    if result is None:
        raise HTTPException(status_code=500, detail="Prediction failed")

    return PredictionResponse(**result)
