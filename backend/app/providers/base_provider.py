"""Abstract base class for AI providers."""
from abc import ABC, abstractmethod
from typing import Optional
from app.models.schemas import AnalysisResponse, CompareResponse


class BaseAIProvider(ABC):
    """Provider interface — all AI providers must implement these methods."""

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        query: str,
        intent: str,
        session_id: str,
        history: list[dict],
        image_name: str = "",
    ) -> AnalysisResponse:
        ...

    @abstractmethod
    async def compare_images(
        self,
        before_bytes: bytes,
        after_bytes: bytes,
        query: str,
        session_id: str,
        history: list[dict],
    ) -> CompareResponse:
        ...

    @abstractmethod
    async def follow_up_query(
        self,
        query: str,
        session_id: str,
        history: list[dict],
    ) -> AnalysisResponse:
        ...
