"""SatQuery AI — FastAPI Backend."""
from __future__ import annotations
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("satquery")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    from app.services.history_service import init_db
    await init_db()

    mode = os.getenv("AI_MODE", "demo")
    api_key = os.getenv("LIVE_AI_API_KEY", "")
    provider = os.getenv("LIVE_AI_PROVIDER", "")

    if mode == "live" and api_key and provider:
        logger.info(f"SatQuery AI started — LIVE AI mode (provider: {provider})")
    else:
        logger.info("SatQuery AI started — DEMO MODE (no API key required)")

    yield
    logger.info("SatQuery AI shutting down.")


app = FastAPI(
    title="SatQuery AI",
    description="Satellite imagery intelligence platform — ask questions, get structured analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        # Vercel deployments
        f"https://{os.getenv('VERCEL_URL', '')}" if os.getenv("VERCEL_URL") else "",
        "https://*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
from app.api.routes import router
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "SatQuery AI Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "/api/status",
    }
