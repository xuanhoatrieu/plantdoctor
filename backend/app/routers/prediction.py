from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image
import io

from ..models.inference import registry
from ..models.vlm import predict_vlm
from ..schemas.prediction import ModelsResponse, PredictionResponse

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    models = registry.available_models
    models.append({"id": "gpt55_vision", "name": "PlantDoctor AI", "description": "PlantDoctor AI engine", "classes": 0})
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

    if model_id == "gpt55_vision":
        result = predict_vlm(image, lang)
    else:
        if not registry.is_loaded(model_id):
            raise HTTPException(status_code=400, detail=f"Model '{model_id}' not loaded")
        result = registry.predict(model_id, image, lang)

    if result is None:
        raise HTTPException(status_code=500, detail="Prediction failed")

    return PredictionResponse(**result)
