"""Pydantic models for SatQuery AI structured responses."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AIMode(str, Enum):
    DEMO = "demo"
    LIVE = "live"


class EvidenceRegion(BaseModel):
    """Normalized bounding region (0-1 coordinate space)."""
    x: float = Field(..., ge=0, le=1, description="Left edge, normalized 0-1")
    y: float = Field(..., ge=0, le=1, description="Top edge, normalized 0-1")
    width: float = Field(..., ge=0, le=1)
    height: float = Field(..., ge=0, le=1)


class Finding(BaseModel):
    """Evidence-based finding with confidence and region."""
    finding: str
    confidence: float = Field(..., ge=0, le=1)
    evidence_quality: str = "medium"  # high | medium | low
    evidence_description: str = ""
    limitations: list[str] = []
    region: Optional[EvidenceRegion] = None


class ObjectDetection(BaseModel):
    label: str
    count: int = 0
    confidence: float = Field(0.0, ge=0, le=1)
    regions: list[EvidenceRegion] = []


class LandCover(BaseModel):
    """AI-estimated visual land-cover proportions (NOT scientifically validated)."""
    built_up: float = 0
    vegetation: float = 0
    water: float = 0
    bare_land: float = 0


class GovernmentUse(BaseModel):
    department: str = ""
    issue: str = ""
    priority: str = "MEDIUM"  # LOW | MEDIUM | HIGH
    recommended_action: str = ""
    reasoning: str = ""


class AnalysisResponse(BaseModel):
    answer: str
    intent: str = "GENERAL_DESCRIPTION"
    confidence: float = Field(0.0, ge=0, le=1)
    objects: list[ObjectDetection] = []
    land_cover: Optional[LandCover] = None
    findings: list[Finding] = []
    observations: list[str] = []
    evidence: list[str] = []
    government_use: Optional[GovernmentUse] = None
    limitations: list[str] = []
    session_id: str = ""
    mode: str = "demo"


class ChangeDetection(BaseModel):
    type: str
    severity: str = "medium"
    description: str = ""
    confidence: float = Field(0.0, ge=0, le=1)
    evidence_description: str = ""
    region: Optional[EvidenceRegion] = None


class CompareResponse(BaseModel):
    overall_change: float = 0
    changes: list[ChangeDetection] = []
    findings: list[Finding] = []
    government_use: Optional[GovernmentUse] = None
    heatmap_base64: str = ""
    limitations: list[str] = []
    session_id: str = ""
    mode: str = "demo"


class GeoMetadata(BaseModel):
    crs: Optional[str] = None
    bounds: Optional[list[float]] = None
    resolution: Optional[list[float]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    band_count: Optional[int] = None
    transform: Optional[list[float]] = None


class HistoryEntry(BaseModel):
    id: int = 0
    timestamp: str = ""
    image_name: str = ""
    query: str = ""
    answer: str = ""
    intent: str = ""
    confidence: float = 0
    mode: str = "demo"


class StatusResponse(BaseModel):
    mode: str = "demo"
    live_ai_available: bool = False
    provider: Optional[str] = None
    demo_available: bool = True


class DemoScene(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    category: str
