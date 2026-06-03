from pydantic import BaseModel


class PredictionResult(BaseModel):
    label: str
    confidence: float
    name: str
    description: str
    treatment: str
    medicines: list[str]
    severity: str = ""
    matched_products: list = []
    banned_warning: list = []


class PredictionResponse(BaseModel):
    model_id: str
    model_name: str
    predictions: list[PredictionResult]
    image_quality_warnings: list[str] = []
    voting_used: bool = False
    cached: bool = False


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    classes: int


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    models_loaded: list[str]
