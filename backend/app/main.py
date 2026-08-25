import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .database.models import init_db
from .routers.prediction import router as prediction_router
from .routers.admin import router as admin_router
from .routers.auth_router import router as auth_router
from .schemas.prediction import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    logger.info("Using GPT VLM only (HF models disabled)")
    yield
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
        "https://benhcay.tuaf.edu.vn",
        "https://tuaf.edu.vn",
        "https://lms.tuaf.edu.vn",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8081",
    ],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trust Caddy proxy headers & allow LAN / local mobile hosts
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

app.include_router(prediction_router)
app.include_router(admin_router)
app.include_router(auth_router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        gpu_available=False,
        models_loaded=["gpt55_vision"],
    )
