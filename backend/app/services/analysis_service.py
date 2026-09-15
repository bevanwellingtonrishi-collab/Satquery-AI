"""Analysis service — orchestrates provider selection, intent classification, and response generation."""
from __future__ import annotations
import uuid
import os
import logging
from app.providers.base_provider import BaseAIProvider
from app.providers.demo_provider import DemoAIProvider
from app.models.schemas import AnalysisResponse, CompareResponse
from app.services.intent_service import classify_intent
from app.utils.image_utils import resize_image

logger = logging.getLogger(__name__)

# In-memory session store for conversation context
_sessions: dict[str, list[dict]] = {}


def get_ai_provider() -> tuple[BaseAIProvider, str]:
    """Get the appropriate AI provider based on config. Returns (provider, mode)."""
    ai_mode = os.getenv("AI_MODE", "demo").lower()
    api_key = os.getenv("LIVE_AI_API_KEY", "").strip()
    provider_name = os.getenv("LIVE_AI_PROVIDER", "").strip()
    model = os.getenv("LIVE_AI_MODEL", "gemini-2.0-flash").strip()

    if ai_mode == "live" and api_key and provider_name:
        try:
            from app.providers.live_provider import OptionalLiveAIProvider
            provider = OptionalLiveAIProvider(provider_name, api_key, model)
            return provider, "live"
        except Exception as e:
            logger.warning(f"Failed to initialize live provider: {e}. Falling back to demo.")

    return DemoAIProvider(), "demo"


def get_session_history(session_id: str) -> list[dict]:
    """Get conversation history for a session."""
    return _sessions.get(session_id, [])


def add_to_session(session_id: str, query: str, answer: str):
    """Add a Q&A pair to session history."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"query": query, "answer": answer})
    # Keep last 10 exchanges
    if len(_sessions[session_id]) > 10:
        _sessions[session_id] = _sessions[session_id][-10:]


async def analyze_image(
    image_bytes: bytes,
    query: str,
    session_id: str = "",
    image_name: str = "",
) -> AnalysisResponse:
    """Analyze a satellite image with a natural-language query."""
    if not session_id:
        session_id = str(uuid.uuid4())

    # Resize for efficiency
    processed_image = resize_image(image_bytes)

    # Classify intent
    intent = classify_intent(query)
    history = get_session_history(session_id)

    # Get provider
    provider, mode = get_ai_provider()

    try:
        result = await provider.analyze_image(
            processed_image, query, intent, session_id, history, image_name
        )
    except Exception as e:
        logger.warning(f"Live AI failed: {e}. Falling back to demo.")
        demo = DemoAIProvider()
        result = await demo.analyze_image(
            processed_image, query, intent, session_id, history, image_name
        )
        result.mode = "demo"
        result.limitations.insert(0, "Live AI unavailable — showing demo analysis.")

    # Store in session
    add_to_session(session_id, query, result.answer)

    return result


async def compare_images(
    before_bytes: bytes,
    after_bytes: bytes,
    query: str,
    session_id: str = "",
) -> CompareResponse:
    """Compare two satellite images."""
    if not session_id:
        session_id = str(uuid.uuid4())

    before_processed = resize_image(before_bytes)
    after_processed = resize_image(after_bytes)

    history = get_session_history(session_id)
    provider, mode = get_ai_provider()

    try:
        result = await provider.compare_images(
            before_processed, after_processed, query, session_id, history
        )
    except Exception as e:
        logger.warning(f"Live AI comparison failed: {e}. Falling back to demo.")
        demo = DemoAIProvider()
        result = await demo.compare_images(
            before_processed, after_processed, query, session_id, history
        )
        result.mode = "demo"
        result.limitations.insert(0, "Live AI unavailable — showing demo analysis.")

    add_to_session(session_id, query, f"Comparison analysis: {len(result.changes)} changes detected.")

    return result


async def follow_up(
    query: str,
    session_id: str,
) -> AnalysisResponse:
    """Handle follow-up query using conversation context."""
    history = get_session_history(session_id)
    provider, mode = get_ai_provider()

    try:
        result = await provider.follow_up_query(query, session_id, history)
    except Exception as e:
        logger.warning(f"Live AI follow-up failed: {e}. Falling back to demo.")
        demo = DemoAIProvider()
        result = await demo.follow_up_query(query, session_id, history)
        result.mode = "demo"

    add_to_session(session_id, query, result.answer)
    return result
