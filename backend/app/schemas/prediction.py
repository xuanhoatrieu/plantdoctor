from typing import Optional
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


class CandidatePlant(BaseModel):
    id: str
    name: str
    icon: str = "🌿"


class PredictionResponse(BaseModel):
    model_id: str
    model_name: str
    predictions: list[PredictionResult]
    image_quality_warnings: list[str] = []
    voting_used: bool = False
    cached: bool = False
    status: str = "success"  # "success" | "needs_clarification"
    candidate_plants: list[CandidatePlant] = []
    clarification_message: Optional[str] = None
    preliminary_symptoms: Optional[str] = None
    session_token: Optional[str] = None


class ClarifyRequest(BaseModel):
    session_token: str
    selected_plant: str
    lang: str = "vi"


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
