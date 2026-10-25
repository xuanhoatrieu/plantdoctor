from typing import Literal, Optional
from pydantic import BaseModel, Field


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
    status: str = "success"  # "success" | "needs_clarification" | "low_quality"
    candidate_plants: list[CandidatePlant] = []
    clarification_message: Optional[str] = None
    preliminary_symptoms: Optional[str] = None
    session_token: Optional[str] = None
    quality_issues: list[str] = []  # low_resolution | too_dark | overexposed | blurry


class ClarifyRequest(BaseModel):
    session_token: str = Field(..., min_length=8, max_length=64)
    selected_plant: str = Field(..., min_length=1, max_length=100)
    lang: str = "vi"


FeedbackReason = Literal["", "wrong_plant", "wrong_disease", "wrong_severity", "wrong_treatment", "other"]


class FeedbackCreate(BaseModel):
    is_correct: bool
    reason: FeedbackReason = ""
    correct_plant: str = Field("", max_length=100)
    correct_disease: str = Field("", max_length=200)
    comment: str = Field("", max_length=1000)
    platform: Literal["web", "ios", "android", ""] = ""
    predicted_name: str = Field("", max_length=300)
    predicted_label: str = Field("", max_length=200)
    predicted_confidence: float = Field(0, ge=0, le=100)
    plant_hint: str = Field("", max_length=100)
    image_count: int = Field(1, ge=1, le=3)
    was_clarified: bool = False


class FeedbackReview(BaseModel):
    reviewed: bool = True
    expert_note: str = Field("", max_length=2000)


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
