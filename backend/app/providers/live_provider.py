"""OptionalLiveAIProvider — optional cloud AI integration. App works without this."""
from __future__ import annotations
import json
import logging
from app.providers.base_provider import BaseAIProvider
from app.models.schemas import (
    AnalysisResponse, CompareResponse, Finding, ObjectDetection,
    EvidenceRegion, LandCover, GovernmentUse, ChangeDetection,
)
from app.services.insight_service import generate_insight, generate_change_insight

logger = logging.getLogger(__name__)


class OptionalLiveAIProvider(BaseAIProvider):
    """Optional cloud AI provider. Falls back to DemoAIProvider on any failure."""

    def __init__(self, provider: str, api_key: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy-load the AI client."""
        if self._client is None:
            if self.provider == "gemini":
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key)
                    self._client = genai.GenerativeModel(self.model)
                except ImportError:
                    raise RuntimeError("google-generativeai package not installed. Install with: pip install google-generativeai")
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize Gemini client: {e}")
            else:
                raise RuntimeError(f"Unsupported provider: {self.provider}")
        return self._client

    def _build_system_prompt(self, intent_context: str = "") -> str:
        return f"""You are SATQuery AI, a satellite imagery analysis assistant.

Analyze ONLY the supplied imagery.
Do not invent objects or features not visible in the image.
Do not claim exact measurements unless supported by clear evidence.
When visual evidence is uncertain, explicitly say so.
Provide useful observations for government and remote-sensing workflows.

{intent_context}

Return ONLY valid JSON matching this exact structure:
{{
  "answer": "your detailed answer",
  "objects": [{{"label": "string", "count": number, "confidence": 0.0-1.0, "regions": [{{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}}]}}],
  "land_cover": {{"built_up": number, "vegetation": number, "water": number, "bare_land": number}},
  "findings": [{{"finding": "string", "confidence": 0.0-1.0, "evidence_quality": "high|medium|low", "evidence_description": "string", "limitations": ["string"], "region": {{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}} or null}}],
  "observations": ["string"],
  "evidence": ["string"]
}}

Coordinates are normalized: 0=left/top, 1=right/bottom.
Label all regions as "AI-estimated".
"""

    def _parse_response(self, text: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # Remove opening ```json
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)

    async def analyze_image(
        self,
        image_bytes: bytes,
        query: str,
        intent: str,
        session_id: str,
        history: list[dict],
        image_name: str = "",
    ) -> AnalysisResponse:
        import PIL.Image
        import io

        client = self._get_client()
        from app.services.intent_service import get_intent_prompt_context
        intent_ctx = get_intent_prompt_context(intent)
        system_prompt = self._build_system_prompt(intent_ctx)

        img = PIL.Image.open(io.BytesIO(image_bytes))

        # Build conversation context
        messages = [system_prompt]
        for h in history[-5:]:  # Last 5 exchanges
            messages.append(f"Previous Q: {h.get('query', '')}\nPrevious A: {h.get('answer', '')}")
        messages.append(img)
        messages.append(f"User question: {query}")

        try:
            response = client.generate_content(messages)
            data = self._parse_response(response.text)
        except Exception as e:
            logger.warning(f"First attempt failed: {e}. Retrying with repair prompt...")
            try:
                repair_prompt = f"The previous response was not valid JSON. Please return ONLY valid JSON for this satellite image analysis query: {query}"
                messages.append(repair_prompt)
                response = client.generate_content(messages)
                data = self._parse_response(response.text)
            except Exception as e2:
                logger.error(f"Retry failed: {e2}")
                raise RuntimeError(f"AI response parsing failed after retry: {e2}")

        # Build structured response
        objects = [
            ObjectDetection(
                label=o.get("label", ""),
                count=o.get("count", 0),
                confidence=o.get("confidence", 0.5),
                regions=[EvidenceRegion(**r) for r in o.get("regions", [])],
            )
            for o in data.get("objects", [])
        ]

        lc = data.get("land_cover")
        land_cover = LandCover(**lc) if lc else None

        findings = [
            Finding(
                finding=f.get("finding", ""),
                confidence=f.get("confidence", 0.5),
                evidence_quality=f.get("evidence_quality", "medium"),
                evidence_description=f.get("evidence_description", ""),
                limitations=f.get("limitations", []),
                region=EvidenceRegion(**f["region"]) if f.get("region") else None,
            )
            for f in data.get("findings", [])
        ]

        gov = generate_insight(intent, findings)

        return AnalysisResponse(
            answer=data.get("answer", "Analysis complete."),
            intent=intent,
            confidence=findings[0].confidence if findings else 0.75,
            objects=objects,
            land_cover=land_cover,
            findings=findings,
            observations=data.get("observations", []),
            evidence=data.get("evidence", []),
            government_use=gov,
            limitations=["AI-generated interpretation.", "Field verification recommended."],
            session_id=session_id,
            mode="live",
        )

    async def compare_images(
        self,
        before_bytes: bytes,
        after_bytes: bytes,
        query: str,
        session_id: str,
        history: list[dict],
    ) -> CompareResponse:
        import PIL.Image
        import io

        client = self._get_client()
        system_prompt = self._build_system_prompt(
            "Compare these two satellite images and identify visible changes in buildings, roads, vegetation, water, and land-use patterns."
        )

        before_img = PIL.Image.open(io.BytesIO(before_bytes))
        after_img = PIL.Image.open(io.BytesIO(after_bytes))

        comparison_prompt = f"""Compare the BEFORE image (first) and AFTER image (second).
User question: {query}

Return ONLY valid JSON:
{{
  "overall_change": 0.0-1.0,
  "changes": [{{"type": "string", "severity": "low|medium|high", "description": "string", "confidence": 0.0-1.0, "evidence_description": "string", "region": {{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}} or null}}],
  "findings": [{{"finding": "string", "confidence": 0.0-1.0, "evidence_quality": "high|medium|low", "evidence_description": "string", "limitations": ["string"], "region": {{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}} or null}}]
}}"""

        try:
            response = client.generate_content([system_prompt, before_img, after_img, comparison_prompt])
            data = self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Compare failed: {e}")
            raise RuntimeError(f"Comparison analysis failed: {e}")

        changes = [
            ChangeDetection(
                type=c.get("type", "unknown"),
                severity=c.get("severity", "medium"),
                description=c.get("description", ""),
                confidence=c.get("confidence", 0.5),
                evidence_description=c.get("evidence_description", ""),
                region=EvidenceRegion(**c["region"]) if c.get("region") else None,
            )
            for c in data.get("changes", [])
        ]

        findings = [
            Finding(
                finding=f.get("finding", ""),
                confidence=f.get("confidence", 0.5),
                evidence_quality=f.get("evidence_quality", "medium"),
                evidence_description=f.get("evidence_description", ""),
                limitations=f.get("limitations", []),
                region=EvidenceRegion(**f["region"]) if f.get("region") else None,
            )
            for f in data.get("findings", [])
        ]

        from app.utils.image_utils import generate_difference_heatmap
        heatmap = generate_difference_heatmap(before_bytes, after_bytes)

        gov = generate_change_insight(changes)

        return CompareResponse(
            overall_change=data.get("overall_change", 0.5),
            changes=changes,
            findings=findings,
            government_use=gov,
            heatmap_base64=heatmap,
            limitations=["AI-generated comparison.", "Visual Change Map is pixel-based, not scientifically validated."],
            session_id=session_id,
            mode="live",
        )

    async def follow_up_query(
        self,
        query: str,
        session_id: str,
        history: list[dict],
    ) -> AnalysisResponse:
        # For follow-ups without image, use text-only generation
        client = self._get_client()
        context = "\n".join([f"Q: {h.get('query','')}\nA: {h.get('answer','')}" for h in history[-5:]])
        prompt = f"""{self._build_system_prompt()}

Previous conversation:
{context}

Follow-up question: {query}"""

        try:
            response = client.generate_content([prompt])
            data = self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Follow-up failed: {e}")
            raise RuntimeError(f"Follow-up query failed: {e}")

        findings = [
            Finding(
                finding=f.get("finding", ""),
                confidence=f.get("confidence", 0.5),
                evidence_quality=f.get("evidence_quality", "medium"),
                evidence_description=f.get("evidence_description", ""),
                limitations=f.get("limitations", []),
                region=EvidenceRegion(**f["region"]) if f.get("region") else None,
            )
            for f in data.get("findings", [])
        ]

        from app.services.intent_service import classify_intent
        intent = classify_intent(query)
        gov = generate_insight(intent)

        return AnalysisResponse(
            answer=data.get("answer", ""),
            intent=intent,
            confidence=findings[0].confidence if findings else 0.75,
            objects=[],
            land_cover=None,
            findings=findings,
            observations=data.get("observations", []),
            evidence=data.get("evidence", []),
            government_use=gov,
            limitations=["AI-generated response.", "Field verification recommended."],
            session_id=session_id,
            mode="live",
        )
