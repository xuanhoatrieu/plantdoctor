import logging
from contextlib import asynccontextmanager

import torch
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .database.models import init_db
from .models.inference import registry
from .routers.prediction import router as prediction_router
from .routers.admin import router as admin_router
from .routers.auth_router import router as auth_router
from .schemas.prediction import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init database
    init_db()
    logger.info("Database initialized")

    # Startup: load models
    logger.info("Loading AI models...")
    logger.info("CUDA available: %s", torch.cuda.is_available())
    if torch.cuda.is_available():
        logger.info("GPU: %s", torch.cuda.get_device_name(0))

    try:
        registry.load_resnet50()
    except Exception as e:
        logger.error("Failed to load ResNet50: %s", e)

    try:
        registry.load_mobilenetv2()
    except Exception as e:
        logger.error("Failed to load MobileNetV2: %s", e)

    try:
        registry.load_rice_disease()
    except Exception as e:
        logger.error("Failed to load Rice Disease model: %s", e)

    logger.info("Models loaded: %d", len(registry.available_models))
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="LeafDoctor API",
    description="Plant Disease Detection API - Phát hiện bệnh cây trồng",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://plant.tuaf.edu.vn",
        "https://tuaf.edu.vn",
        "https://lms.tuaf.edu.vn",
    ],
    allow_origin_regex=r"https://([a-z0-9-]+\.)?tuaf\.edu\.vn(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trust Caddy proxy headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["plant.tuaf.edu.vn", "localhost", "127.0.0.1"])

app.include_router(prediction_router)
app.include_router(admin_router)
app.include_router(auth_router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        gpu_available=torch.cuda.is_available(),
        models_loaded=[m["id"] for m in registry.available_models],
    )
