"""FastAPI routes — all API endpoints for SatQuery AI."""
from __future__ import annotations
import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from app.models.schemas import (
    AnalysisResponse, CompareResponse, StatusResponse, HistoryEntry, GeoMetadata, DemoScene,
)
from app.services import analysis_service, history_service, geo_service, report_service
from app.services.intent_service import classify_intent
from app.utils.image_utils import get_image_info

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/tiff"}
MAX_SIZE = 20 * 1024 * 1024  # 20 MB


def _check_image(file: UploadFile):
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        # Also allow by extension
        ext = (file.filename or "").lower().split(".")[-1]
        if ext not in ("png", "jpg", "jpeg", "webp", "tif", "tiff", "geotiff"):
            raise HTTPException(400, f"Unsupported file type: {file.content_type}")


# ──────────────── Health & Status ────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "satquery-ai"}


@router.get("/status", response_model=StatusResponse)
async def status():
    ai_mode = os.getenv("AI_MODE", "demo").lower()
    api_key = os.getenv("LIVE_AI_API_KEY", "").strip()
    provider = os.getenv("LIVE_AI_PROVIDER", "").strip()

    live_available = ai_mode == "live" and bool(api_key) and bool(provider)
    return StatusResponse(
        mode="live" if live_available else "demo",
        live_ai_available=live_available,
        provider=provider if live_available else None,
        demo_available=True,
    )


# ──────────────── Analyze ────────────────

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    image: UploadFile = File(...),
    query: str = Form(...),
    session_id: str = Form(""),
):
    if not query.strip():
        raise HTTPException(400, "Query cannot be empty.")
    _check_image(image)

    image_bytes = await image.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(400, "Image too large. Maximum 20 MB.")
    if len(image_bytes) == 0:
        raise HTTPException(400, "Empty image file.")

    if not session_id:
        session_id = str(uuid.uuid4())

    result = await analysis_service.analyze_image(
        image_bytes, query.strip(), session_id, image.filename or "uploaded_image"
    )

    # Save to history
    try:
        await history_service.init_db()
        await history_service.add_entry(
            image.filename or "uploaded_image",
            query.strip(),
            result.answer,
            result.intent,
            result.confidence,
            result.mode,
        )
    except Exception as e:
        logger.warning(f"Failed to save history: {e}")

    return result


# ──────────────── Follow-up ────────────────

@router.post("/followup", response_model=AnalysisResponse)
async def followup(
    query: str = Form(...),
    session_id: str = Form(...),
):
    if not query.strip():
        raise HTTPException(400, "Query cannot be empty.")
    if not session_id:
        raise HTTPException(400, "session_id required for follow-up.")

    result = await analysis_service.follow_up(query.strip(), session_id)

    try:
        await history_service.init_db()
        await history_service.add_entry(
            "follow-up",
            query.strip(),
            result.answer,
            result.intent,
            result.confidence,
            result.mode,
        )
    except Exception as e:
        logger.warning(f"Failed to save history: {e}")

    return result


# ──────────────── Compare ────────────────

@router.post("/compare", response_model=CompareResponse)
async def compare(
    before_image: UploadFile = File(...),
    after_image: UploadFile = File(...),
    query: str = Form("What has changed between these two images?"),
    session_id: str = Form(""),
):
    _check_image(before_image)
    _check_image(after_image)

    before_bytes = await before_image.read()
    after_bytes = await after_image.read()

    if len(before_bytes) == 0 or len(after_bytes) == 0:
        raise HTTPException(400, "Empty image file.")
    if len(before_bytes) > MAX_SIZE or len(after_bytes) > MAX_SIZE:
        raise HTTPException(400, "Image too large. Maximum 20 MB each.")

    if not session_id:
        session_id = str(uuid.uuid4())

    result = await analysis_service.compare_images(
        before_bytes, after_bytes, query.strip(), session_id
    )

    try:
        await history_service.init_db()
        await history_service.add_entry(
            f"compare: {before_image.filename} vs {after_image.filename}",
            query.strip(),
            f"Comparison: {len(result.changes)} changes detected, overall change: {result.overall_change:.0%}",
            "CHANGE_ANALYSIS",
            result.overall_change,
            result.mode,
        )
    except Exception as e:
        logger.warning(f"Failed to save history: {e}")

    return result


# ──────────────── GeoTIFF Metadata ────────────────

@router.post("/geo-metadata", response_model=GeoMetadata)
async def geo_metadata(
    image: UploadFile = File(...),
):
    image_bytes = await image.read()
    return await geo_service.extract_geo_metadata(image_bytes, image.filename or "")


# ──────────────── History ────────────────

@router.get("/history")
async def get_history(limit: int = 50):
    entries = await history_service.get_history(limit)
    return {"entries": [e.model_dump() for e in entries]}


# ──────────────── Report ────────────────

@router.post("/report")
async def generate_report(
    query: str = Form(...),
    analysis_json: str = Form(...),
    image_name: str = Form(""),
    heatmap_base64: str = Form(""),
):
    import json
    try:
        analysis = json.loads(analysis_json)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid analysis JSON.")

    pdf_bytes = await report_service.generate_report(
        query, analysis, image_name, heatmap_base64
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=satquery_report.pdf"},
    )


# ──────────────── Demo Scenes ────────────────

DEMO_SCENES = [
    DemoScene(id="urban", name="Urban Area", description="Dense urban settlement with buildings, roads, and infrastructure", image_url="/api/demo/image/urban", category="urban"),
    DemoScene(id="flood_before", name="Pre-Flood", description="Area before flooding event", image_url="/api/demo/image/flood_before", category="flood"),
    DemoScene(id="flood_after", name="Post-Flood", description="Same area after flooding event", image_url="/api/demo/image/flood_after", category="flood"),
    DemoScene(id="forest", name="Forest Area", description="Dense forest and vegetation cover", image_url="/api/demo/image/forest", category="vegetation"),
    DemoScene(id="agriculture", name="Agricultural Land", description="Agricultural fields and farming area", image_url="/api/demo/image/agriculture", category="agriculture"),
    DemoScene(id="coastal", name="Coastal Area", description="Coastal zone with shoreline features", image_url="/api/demo/image/coastal", category="coastal"),
    DemoScene(id="urban_2023", name="Urban 2023", description="Urban area captured in 2023", image_url="/api/demo/image/urban_2023", category="comparison"),
    DemoScene(id="urban_2026", name="Urban 2026", description="Same urban area captured in 2026", image_url="/api/demo/image/urban_2026", category="comparison"),
]


@router.get("/demo")
async def get_demo_scenes():
    return {"scenes": [s.model_dump() for s in DEMO_SCENES]}


@router.get("/demo/image/{scene_id}")
async def get_demo_image(scene_id: str):
    """Serve a demo scene image."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "demo")

    # Try common extensions
    for ext in ("jpg", "jpeg", "png", "webp"):
        path = os.path.join(data_dir, f"{scene_id}.{ext}")
        if os.path.exists(path):
            with open(path, "rb") as f:
                content = f.read()
            media = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
            return Response(content=content, media_type=media.get(ext, "image/jpeg"))

    # Generate a placeholder if no image exists
    from app.utils.image_utils import _generate_placeholder_image
    content = _generate_placeholder_image(scene_id)
    return Response(content=content, media_type="image/png")
