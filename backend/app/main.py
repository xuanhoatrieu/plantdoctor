import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .database.models import init_db
from .routers.prediction import router as prediction_router
from .routers.admin import router as admin_router
from .routers.auth_router import router as auth_router
from .routers.feedback import router as feedback_router, admin_router as feedback_admin_router
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

def _cors_origins() -> list:
    origins = [
        "https://benhcay.tuaf.edu.vn",
        "https://tuaf.edu.vn",
        "https://lms.tuaf.edu.vn",
    ]
    # Extra trusted origins, comma-separated (e.g. a LAN dev URL like http://192.168.1.10:3000)
    extra = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    return origins + [o for o in extra if o != "*"]  # a wildcard is never accepted


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    # Local development only (Vite dev server, Expo web). Anchored so "localhost.evil.com" does not match.
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d{1,5})?$",
    # The web and mobile clients authenticate with an "Authorization: Bearer" header, not cookies,
    # so browsers never need to send credentials cross-origin.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Accept-Language"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/admin"):
        response.headers.setdefault("Cache-Control", "no-store")
    # TODO(security): the HTML app is served by the frontend nginx container; its CSP / HSTS headers
    # belong in frontend/nginx.conf or the Caddy config, not here.
    return response

app.include_router(prediction_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(feedback_router)
app.include_router(feedback_admin_router)

_kb_images_dir = os.path.join(os.path.dirname(__file__), "data", "kb_images")
os.makedirs(_kb_images_dir, exist_ok=True)
app.mount("/api/v1/kb_images", StaticFiles(directory=_kb_images_dir), name="kb_images")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        gpu_available=False,
        models_loaded=["gpt55_vision"],
    )
