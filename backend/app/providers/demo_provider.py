"""DemoAIProvider — first-class, guaranteed provider. Works offline, no API keys needed."""
from __future__ import annotations
import asyncio
import random
import uuid
from app.providers.base_provider import BaseAIProvider
from app.models.schemas import (
    AnalysisResponse, CompareResponse, Finding, ObjectDetection,
    EvidenceRegion, LandCover, GovernmentUse, ChangeDetection,
)
from app.services.intent_service import classify_intent
from app.services.insight_service import generate_insight, generate_change_insight


# --- Demo response data for single-image analysis ---

DEMO_RESPONSES: dict[str, dict] = {
    "GENERAL_DESCRIPTION": {
        "answer": "This satellite image shows a mixed-use area with visible built-up structures, vegetation patches, and transportation infrastructure. The scene contains a combination of residential and commercial development with scattered green spaces. Road networks are clearly visible connecting different sections of the area.",
        "objects": [
            {"label": "Buildings", "count": 38, "confidence": 0.85, "regions": [
                {"x": 0.15, "y": 0.20, "width": 0.30, "height": 0.25},
                {"x": 0.55, "y": 0.10, "width": 0.35, "height": 0.30},
            ]},
            {"label": "Roads", "count": 8, "confidence": 0.90, "regions": [
                {"x": 0.05, "y": 0.45, "width": 0.90, "height": 0.08},
            ]},
            {"label": "Vegetation patches", "count": 5, "confidence": 0.82, "regions": [
                {"x": 0.60, "y": 0.55, "width": 0.25, "height": 0.20},
            ]},
            {"label": "Water body", "count": 1, "confidence": 0.75, "regions": [
                {"x": 0.02, "y": 0.70, "width": 0.15, "height": 0.12},
            ]},
        ],
        "land_cover": {"built_up": 55, "vegetation": 25, "water": 8, "bare_land": 12},
        "findings": [
            {
                "finding": "Mixed-use development with residential and commercial structures",
                "confidence": 0.87,
                "evidence_quality": "medium",
                "evidence_description": "Multiple building types visible with varying roof sizes and orientations",
                "limitations": ["Visual interpretation only — building use cannot be confirmed from imagery alone"],
                "region": {"x": 0.15, "y": 0.15, "width": 0.70, "height": 0.40},
            },
            {
                "finding": "Active road network connecting settlement areas",
                "confidence": 0.91,
                "evidence_quality": "high",
                "evidence_description": "Clear linear features consistent with paved roads visible across the scene",
                "limitations": ["Road condition cannot be assessed from this imagery"],
                "region": {"x": 0.05, "y": 0.42, "width": 0.90, "height": 0.12},
            },
        ],
        "observations": [
            "The area appears to be a semi-urban settlement with moderate development density.",
            "Vegetation is concentrated in the southeastern portion of the image.",
            "A small water body is visible in the southwestern corner.",
        ],
    },
    "BUILDING_ANALYSIS": {
        "answer": "Approximately 47 buildings are visually estimated in this scene. The structures vary in size from small residential units to larger commercial buildings. The highest building density is concentrated in the northern portion of the image, with sparser development toward the south.",
        "objects": [
            {"label": "Large buildings", "count": 12, "confidence": 0.88, "regions": [
                {"x": 0.20, "y": 0.10, "width": 0.25, "height": 0.20},
                {"x": 0.55, "y": 0.15, "width": 0.20, "height": 0.18},
            ]},
            {"label": "Small buildings", "count": 35, "confidence": 0.82, "regions": [
                {"x": 0.10, "y": 0.05, "width": 0.80, "height": 0.45},
            ]},
        ],
        "land_cover": {"built_up": 65, "vegetation": 22, "water": 5, "bare_land": 8},
        "findings": [
            {
                "finding": "High building density in the northern section",
                "confidence": 0.89,
                "evidence_quality": "high",
                "evidence_description": "Dense cluster of roof structures visible in the upper portion of the image",
                "limitations": ["Building count is an AI estimate — actual count may vary"],
                "region": {"x": 0.10, "y": 0.05, "width": 0.80, "height": 0.35},
            },
            {
                "finding": "Mix of residential and potentially commercial structures",
                "confidence": 0.78,
                "evidence_quality": "medium",
                "evidence_description": "Varying roof sizes suggest different building types",
                "limitations": ["Building function cannot be determined from satellite imagery alone"],
                "region": {"x": 0.20, "y": 0.10, "width": 0.60, "height": 0.30},
            },
        ],
        "observations": [
            "47 buildings are visually estimated across the scene.",
            "Building density is highest in the northern region.",
            "12 larger structures suggest commercial or institutional buildings.",
            "Development follows a grid-like pattern along visible road networks.",
        ],
    },
    "ROAD_ANALYSIS": {
        "answer": "The image shows a network of approximately 8 road segments of varying widths. A major road runs east-west through the center of the scene, with several smaller roads branching off to the north and south. Road infrastructure appears well-maintained based on visual appearance.",
        "objects": [
            {"label": "Major roads", "count": 2, "confidence": 0.92, "regions": [
                {"x": 0.0, "y": 0.42, "width": 1.0, "height": 0.10},
                {"x": 0.45, "y": 0.0, "width": 0.10, "height": 1.0},
            ]},
            {"label": "Minor roads", "count": 6, "confidence": 0.80, "regions": []},
        ],
        "land_cover": {"built_up": 58, "vegetation": 24, "water": 6, "bare_land": 12},
        "findings": [
            {
                "finding": "Primary east-west arterial road",
                "confidence": 0.93,
                "evidence_quality": "high",
                "evidence_description": "Wide linear feature traversing the full width of the image",
                "limitations": ["Road classification based on width alone — official road type requires verification"],
                "region": {"x": 0.0, "y": 0.42, "width": 1.0, "height": 0.10},
            },
        ],
        "observations": [
            "Primary road network connects northern and southern settlement areas.",
            "Road surfaces appear lighter in color suggesting paved surfaces.",
            "At least one intersection is visible near the center of the scene.",
        ],
    },
    "WATER_ANALYSIS": {
        "answer": "Two water bodies are visible in this image. A larger water body appears in the southwestern portion of the scene, and a smaller pond or reservoir is visible in the eastern section. The water appears relatively clear based on color characteristics.",
        "objects": [
            {"label": "Large water body", "count": 1, "confidence": 0.88, "regions": [
                {"x": 0.05, "y": 0.65, "width": 0.20, "height": 0.18},
            ]},
            {"label": "Small water body", "count": 1, "confidence": 0.76, "regions": [
                {"x": 0.72, "y": 0.40, "width": 0.10, "height": 0.08},
            ]},
        ],
        "land_cover": {"built_up": 45, "vegetation": 30, "water": 15, "bare_land": 10},
        "findings": [
            {
                "finding": "Two water bodies identified in the scene",
                "confidence": 0.84,
                "evidence_quality": "medium",
                "evidence_description": "Dark-toned areas consistent with water surface reflectance",
                "limitations": ["Water body boundaries are approximate", "Depth and quality cannot be assessed from satellite imagery"],
                "region": {"x": 0.05, "y": 0.65, "width": 0.20, "height": 0.18},
            },
        ],
        "observations": [
            "Larger water body in the southwest may be a natural lake or reservoir.",
            "Smaller body in the east appears to be a constructed pond.",
            "Vegetation surrounding the larger water body suggests a natural riparian zone.",
        ],
    },
    "VEGETATION_ANALYSIS": {
        "answer": "Vegetation covers approximately 25-30% of the visible area. Dense vegetation is concentrated in the southeastern portion of the scene, while scattered green patches are visible throughout the built-up area. This is a visual estimate — proper vegetation index calculation requires multispectral imagery.",
        "objects": [
            {"label": "Dense vegetation", "count": 3, "confidence": 0.85, "regions": [
                {"x": 0.60, "y": 0.55, "width": 0.30, "height": 0.30},
            ]},
            {"label": "Sparse vegetation", "count": 6, "confidence": 0.72, "regions": [
                {"x": 0.10, "y": 0.30, "width": 0.15, "height": 0.12},
            ]},
        ],
        "land_cover": {"built_up": 48, "vegetation": 32, "water": 8, "bare_land": 12},
        "findings": [
            {
                "finding": "Dense vegetation cluster in southeastern section",
                "confidence": 0.86,
                "evidence_quality": "medium",
                "evidence_description": "Dark green tones indicating healthy vegetation cover",
                "limitations": ["Visual estimate from RGB imagery — not NDVI. Species identification not possible."],
                "region": {"x": 0.60, "y": 0.55, "width": 0.30, "height": 0.30},
            },
        ],
        "observations": [
            "Overall vegetation appears healthy based on green color intensity.",
            "Green spaces within the built-up area suggest parks or gardens.",
            "Vegetation density decreases toward the northern (more urbanized) section.",
        ],
    },
    "FLOOD_ANALYSIS": {
        "answer": "Based on visual analysis, there are indications of possible water accumulation in low-lying areas of the scene. The southwestern region shows expanded water extent compared to typical conditions. This is an AI-assisted screening — field verification and official assessment are required.",
        "objects": [
            {"label": "Potential flood area", "count": 2, "confidence": 0.74, "regions": [
                {"x": 0.05, "y": 0.60, "width": 0.30, "height": 0.25},
                {"x": 0.35, "y": 0.72, "width": 0.18, "height": 0.14},
            ]},
        ],
        "land_cover": {"built_up": 40, "vegetation": 20, "water": 28, "bare_land": 12},
        "findings": [
            {
                "finding": "Possible water expansion in the southwestern area",
                "confidence": 0.76,
                "evidence_quality": "medium",
                "evidence_description": "Water-like reflectance patterns extending beyond typical water body boundaries",
                "limitations": ["This is a visual screening only", "Cannot confirm flooding without temporal comparison and ground validation"],
                "region": {"x": 0.05, "y": 0.60, "width": 0.30, "height": 0.25},
            },
        ],
        "observations": [
            "Expanded water extent visible in the southwestern portion of the image.",
            "Nearby structures may be affected if flooding is confirmed.",
            "Severity estimate: MEDIUM — requires field verification.",
        ],
    },
    "URBAN_EXPANSION": {
        "answer": "The image shows significant built-up area covering approximately 60-65% of the scene. Urban development appears concentrated in the northern and central regions with a clear urban-rural transition visible toward the south. Development patterns suggest active urbanization.",
        "objects": [
            {"label": "Dense urban area", "count": 1, "confidence": 0.88, "regions": [
                {"x": 0.10, "y": 0.05, "width": 0.75, "height": 0.45},
            ]},
            {"label": "Urban fringe", "count": 1, "confidence": 0.75, "regions": [
                {"x": 0.10, "y": 0.50, "width": 0.60, "height": 0.20},
            ]},
        ],
        "land_cover": {"built_up": 63, "vegetation": 20, "water": 7, "bare_land": 10},
        "findings": [
            {
                "finding": "Active urbanization along the southern fringe",
                "confidence": 0.82,
                "evidence_quality": "medium",
                "evidence_description": "Transition zone between dense development and open land visible",
                "limitations": ["Cannot determine rate of expansion from a single image", "Temporal comparison recommended"],
                "region": {"x": 0.10, "y": 0.50, "width": 0.60, "height": 0.20},
            },
        ],
        "observations": [
            "Dense urban core in the northern section.",
            "Development density decreases toward the south.",
            "Urban fringe zone suggests ongoing expansion.",
        ],
    },
    "LAND_COVER": {
        "answer": "The AI-estimated visual land-cover composition of this scene is approximately: Built-up 55%, Vegetation 25%, Water 8%, Bare land 12%. These are visual estimates from RGB imagery and do not represent scientifically validated land-cover classification.",
        "objects": [],
        "land_cover": {"built_up": 55, "vegetation": 25, "water": 8, "bare_land": 12},
        "findings": [
            {
                "finding": "Predominantly built-up land cover",
                "confidence": 0.83,
                "evidence_quality": "medium",
                "evidence_description": "Visual estimation based on color and texture patterns in the satellite image",
                "limitations": ["These are AI-estimated proportions from RGB imagery", "Not a validated land-cover classification"],
                "region": None,
            },
        ],
        "observations": [
            "Built-up area dominates the scene.",
            "Vegetation is concentrated in patches rather than contiguous areas.",
            "Small water bodies present in the scene.",
        ],
    },
    "CHANGE_ANALYSIS": {
        "answer": "Based on the image, this area shows characteristics of an evolving landscape. Without a direct temporal comparison image, specific changes cannot be definitively identified. However, the mix of new-looking and weathered structures suggests recent development activity. Upload a before image for detailed change analysis.",
        "objects": [
            {"label": "Potentially new structures", "count": 8, "confidence": 0.68, "regions": [
                {"x": 0.30, "y": 0.20, "width": 0.25, "height": 0.20},
            ]},
        ],
        "land_cover": {"built_up": 58, "vegetation": 24, "water": 6, "bare_land": 12},
        "findings": [
            {
                "finding": "Some structures appear newer based on visual characteristics",
                "confidence": 0.65,
                "evidence_quality": "low",
                "evidence_description": "Brighter roof surfaces and clearer edges suggest recent construction",
                "limitations": ["Single-image analysis cannot confirm temporal changes", "Before/after comparison recommended for change detection"],
                "region": {"x": 0.30, "y": 0.20, "width": 0.25, "height": 0.20},
            },
        ],
        "observations": [
            "Some structures appear recently constructed based on visual appearance.",
            "For reliable change detection, please upload before and after images.",
        ],
    },
    "AGRICULTURE": {
        "answer": "The image shows agricultural land with visible field patterns. Approximately 3-4 distinct field parcels are visible with varying crop conditions. The fields show different stages of cultivation based on color variations.",
        "objects": [
            {"label": "Agricultural fields", "count": 4, "confidence": 0.84, "regions": [
                {"x": 0.10, "y": 0.30, "width": 0.35, "height": 0.40},
                {"x": 0.55, "y": 0.25, "width": 0.30, "height": 0.35},
            ]},
        ],
        "land_cover": {"built_up": 15, "vegetation": 55, "water": 10, "bare_land": 20},
        "findings": [
            {
                "finding": "Active agricultural activity with multiple field parcels",
                "confidence": 0.83,
                "evidence_quality": "medium",
                "evidence_description": "Regular geometric patterns consistent with cultivated fields",
                "limitations": ["Crop type identification not possible from this imagery resolution"],
                "region": {"x": 0.10, "y": 0.30, "width": 0.75, "height": 0.45},
            },
        ],
        "observations": [
            "Multiple agricultural parcels visible.",
            "Color variations suggest different crops or growth stages.",
            "Irrigation infrastructure may be present based on field patterns.",
        ],
    },
    "FOREST": {
        "answer": "The image shows significant forest cover with dense canopy in the eastern and southern sections. The forest appears relatively contiguous with some fragmentation near the built-up areas. Visual estimate suggests approximately 40-50% forest cover in the visible scene.",
        "objects": [
            {"label": "Dense forest", "count": 2, "confidence": 0.87, "regions": [
                {"x": 0.55, "y": 0.40, "width": 0.40, "height": 0.50},
            ]},
        ],
        "land_cover": {"built_up": 20, "vegetation": 55, "water": 10, "bare_land": 15},
        "findings": [
            {
                "finding": "Contiguous forest cover in the southeast",
                "confidence": 0.87,
                "evidence_quality": "high",
                "evidence_description": "Dense, dark-green canopy cover visible in satellite imagery",
                "limitations": ["Forest type and health cannot be assessed from RGB imagery alone"],
                "region": {"x": 0.55, "y": 0.40, "width": 0.40, "height": 0.50},
            },
        ],
        "observations": [
            "Dense forest canopy covers the southeastern portion.",
            "Some fragmentation visible near built-up areas.",
            "Forest edge appears well-defined in the south.",
        ],
    },
    "COASTAL": {
        "answer": "The image shows a coastal area with visible shoreline, water, and adjacent development. The coastline runs roughly north-south in the western portion of the scene with built-up areas inland.",
        "objects": [
            {"label": "Shoreline", "count": 1, "confidence": 0.90, "regions": [
                {"x": 0.0, "y": 0.10, "width": 0.05, "height": 0.80},
            ]},
        ],
        "land_cover": {"built_up": 30, "vegetation": 20, "water": 35, "bare_land": 15},
        "findings": [
            {
                "finding": "Coastal development adjacent to shoreline",
                "confidence": 0.84,
                "evidence_quality": "medium",
                "evidence_description": "Built-up structures visible close to the coastline",
                "limitations": ["Coastal zone boundaries require official CRZ mapping for regulatory decisions"],
                "region": {"x": 0.05, "y": 0.15, "width": 0.30, "height": 0.60},
            },
        ],
        "observations": [
            "Coastal area with visible development.",
            "Shoreline appears relatively stable.",
            "Development extends close to the coast.",
        ],
    },
    "ENCROACHMENT_SCREENING": {
        "answer": "Visual screening suggests several structures that may be located outside expected development zones. Approximately 8-12 potential structures are identified in the peripheral areas. This is a screening indicator only — field verification and official boundary comparison are required.",
        "objects": [
            {"label": "Potential encroachment structures", "count": 10, "confidence": 0.68, "regions": [
                {"x": 0.70, "y": 0.60, "width": 0.20, "height": 0.15},
                {"x": 0.05, "y": 0.75, "width": 0.15, "height": 0.12},
            ]},
        ],
        "land_cover": {"built_up": 52, "vegetation": 28, "water": 5, "bare_land": 15},
        "findings": [
            {
                "finding": "Potential encroachment requiring field verification",
                "confidence": 0.68,
                "evidence_quality": "low",
                "evidence_description": "Structures visible in areas that may be outside expected development zones",
                "limitations": [
                    "Cannot confirm encroachment without official boundary data",
                    "Field verification is mandatory",
                    "This is a screening indicator only — not a legal determination",
                ],
                "region": {"x": 0.70, "y": 0.60, "width": 0.20, "height": 0.15},
            },
        ],
        "observations": [
            "Several structures appear to be in peripheral areas.",
            "Potential encroachment requiring field verification — not a legal determination.",
        ],
    },
    "OBJECT_DETECTION": {
        "answer": "Multiple object categories are visible in this satellite image. The scene contains buildings, roads, vegetation patches, and at least one water body. Buildings are the most numerous features with approximately 38 structures identified.",
        "objects": [
            {"label": "Buildings", "count": 38, "confidence": 0.85, "regions": [
                {"x": 0.15, "y": 0.10, "width": 0.70, "height": 0.40},
            ]},
            {"label": "Roads", "count": 8, "confidence": 0.90, "regions": [
                {"x": 0.05, "y": 0.45, "width": 0.90, "height": 0.08},
            ]},
            {"label": "Vegetation", "count": 5, "confidence": 0.82, "regions": [
                {"x": 0.60, "y": 0.55, "width": 0.25, "height": 0.20},
            ]},
            {"label": "Water body", "count": 1, "confidence": 0.78, "regions": [
                {"x": 0.02, "y": 0.70, "width": 0.15, "height": 0.12},
            ]},
        ],
        "land_cover": {"built_up": 55, "vegetation": 25, "water": 8, "bare_land": 12},
        "findings": [
            {
                "finding": "38 buildings visually identified across the scene",
                "confidence": 0.85,
                "evidence_quality": "medium",
                "evidence_description": "Roof structures visible with varying sizes and orientations",
                "limitations": ["Count is an AI estimate and may differ from ground truth"],
                "region": {"x": 0.15, "y": 0.10, "width": 0.70, "height": 0.40},
            },
        ],
        "observations": [
            "Buildings are the primary feature category.",
            "Road network is well-developed.",
            "Vegetation and water bodies present.",
        ],
    },
}


# --- Follow-up response chains ---
FOLLOWUP_CHAINS = {
    "density": {
        "answer": "The highest building density is in the northern section of the image, where approximately 25-30 structures are clustered within a small area. This region shows characteristics of a dense residential or mixed-use development pattern.",
        "findings": [
            {
                "finding": "Highest density concentration in the northern region",
                "confidence": 0.86,
                "evidence_quality": "medium",
                "evidence_description": "Closely packed roof structures visible in satellite imagery",
                "limitations": ["Density is a visual estimate"],
                "region": {"x": 0.15, "y": 0.05, "width": 0.65, "height": 0.30},
            }
        ],
    },
    "biggest_change": {
        "answer": "The most significant visible change is concentrated in the northeastern area of the scene, where new construction appears to have replaced previously open land. This region shows the strongest visual difference between the two time periods.",
        "findings": [
            {
                "finding": "Largest change area in the northeast",
                "confidence": 0.84,
                "evidence_quality": "medium",
                "evidence_description": "Strong visual difference in the northeastern quadrant",
                "limitations": ["Based on visual comparison — precise area measurement requires GIS analysis"],
                "region": {"x": 0.60, "y": 0.05, "width": 0.35, "height": 0.35},
            }
        ],
    },
    "department": {
        "answer": "Based on the analysis showing urban expansion and new construction, the most relevant government departments would be: (1) Urban Planning / Municipal Administration for development compliance review, and (2) Revenue / Land Records department for land-use verification. The priority level is HIGH given the extent of visible changes.",
        "findings": [
            {
                "finding": "Multiple departments require notification",
                "confidence": 0.88,
                "evidence_quality": "high",
                "evidence_description": "Urban expansion pattern matches criteria for planning review",
                "limitations": ["Department relevance is an AI suggestion — actual jurisdiction depends on local governance structure"],
                "region": None,
            }
        ],
    },
    "urban": {
        "answer": "Yes, the scene appears predominantly urban. Built-up structures cover approximately 55-65% of the visible area. The development pattern is consistent with a semi-urban to urban settlement with residential areas, commercial structures, and supporting infrastructure.",
        "findings": [
            {
                "finding": "Predominantly urban landscape",
                "confidence": 0.88,
                "evidence_quality": "high",
                "evidence_description": "Dense building coverage with infrastructure network",
                "limitations": ["Visual classification — official urban/rural designation requires census data"],
                "region": None,
            }
        ],
    },
    "default": {
        "answer": "Based on the previous analysis of this scene, the area shows a mixed-use landscape with significant built-up coverage, scattered vegetation, and visible infrastructure. The AI-estimated findings provide a screening-level overview suitable for decision-support and further investigation.",
        "findings": [],
    },
}


# --- Comparison demo data ---
DEMO_COMPARISON = {
    "overall_change": 0.72,
    "changes": [
        {
            "type": "urban_expansion",
            "severity": "high",
            "description": "Significant new construction visible in the northeastern quadrant. Approximately 15-20 new structures appear to have been built, replacing previously open or agricultural land.",
            "confidence": 0.88,
            "evidence_description": "Clear visual difference in building density between the two time periods",
            "region": {"x": 0.55, "y": 0.08, "width": 0.38, "height": 0.35},
        },
        {
            "type": "vegetation_loss",
            "severity": "medium",
            "description": "Noticeable reduction in green cover in the central-eastern area, likely due to land clearing for development.",
            "confidence": 0.82,
            "evidence_description": "Green areas in the before image appear as bare or built-up in the after image",
            "region": {"x": 0.45, "y": 0.35, "width": 0.30, "height": 0.25},
        },
        {
            "type": "road_expansion",
            "severity": "medium",
            "description": "New road segments or widening of existing roads visible in the southern section.",
            "confidence": 0.78,
            "evidence_description": "Linear features appear wider or more defined in the later image",
            "region": {"x": 0.10, "y": 0.60, "width": 0.70, "height": 0.10},
        },
        {
            "type": "construction",
            "severity": "high",
            "description": "Active construction activity visible in multiple locations, indicated by disturbed soil patterns and partially completed structures.",
            "confidence": 0.80,
            "evidence_description": "Bright patches consistent with exposed soil and construction materials",
            "region": {"x": 0.30, "y": 0.15, "width": 0.25, "height": 0.20},
        },
    ],
    "findings": [
        {
            "finding": "Significant urban expansion detected between the two time periods",
            "confidence": 0.88,
            "evidence_quality": "high",
            "evidence_description": "Clear increase in building count and density visible in the northeastern and central regions",
            "limitations": [
                "Visual comparison only — precise measurements require GIS analysis",
                "AI-estimated confidence",
            ],
            "region": {"x": 0.55, "y": 0.08, "width": 0.38, "height": 0.35},
        },
        {
            "finding": "Vegetation cover reduction associated with new development",
            "confidence": 0.82,
            "evidence_quality": "medium",
            "evidence_description": "Previously green areas now show built-up characteristics",
            "limitations": [
                "Vegetation assessment from RGB imagery only — not NDVI",
                "Seasonal variation could affect vegetation appearance",
            ],
            "region": {"x": 0.45, "y": 0.35, "width": 0.30, "height": 0.25},
        },
        {
            "finding": "Infrastructure development including road expansion",
            "confidence": 0.78,
            "evidence_quality": "medium",
            "evidence_description": "Road network appears denser in the later image",
            "limitations": ["Road condition assessment requires higher resolution imagery"],
            "region": {"x": 0.10, "y": 0.60, "width": 0.70, "height": 0.10},
        },
    ],
}

DEMO_FLOOD_COMPARISON = {
    "overall_change": 0.65,
    "changes": [
        {
            "type": "water_expansion",
            "severity": "high",
            "description": "Significant water expansion visible across the central and southern portions of the scene. Previously dry land now appears inundated.",
            "confidence": 0.85,
            "evidence_description": "Dark-toned water-like surfaces extended beyond normal water body boundaries",
            "region": {"x": 0.15, "y": 0.40, "width": 0.60, "height": 0.45},
        },
        {
            "type": "vegetation_loss",
            "severity": "medium",
            "description": "Vegetation in low-lying areas appears submerged or damaged.",
            "confidence": 0.76,
            "evidence_description": "Previously green areas now show water or damaged vegetation signatures",
            "region": {"x": 0.30, "y": 0.50, "width": 0.35, "height": 0.30},
        },
    ],
    "findings": [
        {
            "finding": "Possible flooding with significant water expansion",
            "confidence": 0.85,
            "evidence_quality": "medium",
            "evidence_description": "Clear increase in water extent between the two images",
            "limitations": [
                "AI-assisted visual screening only",
                "Not a substitute for official flood assessment",
                "Field verification required",
            ],
            "region": {"x": 0.15, "y": 0.40, "width": 0.60, "height": 0.45},
        },
    ],
}


def _match_followup_key(query: str) -> str:
    """Match a follow-up query to a response key."""
    q = query.lower()
    if any(w in q for w in ["density", "densest", "most buildings", "highest"]):
        return "density"
    if any(w in q for w in ["biggest change", "largest change", "most significant", "strongest"]):
        return "biggest_change"
    if any(w in q for w in ["department", "government", "investigate", "ministry", "authority"]):
        return "department"
    if any(w in q for w in ["urban", "city", "town"]):
        return "urban"
    return "default"


class DemoAIProvider(BaseAIProvider):
    """First-class demo provider — works offline, no API keys needed."""

    async def analyze_image(
        self,
        image_bytes: bytes,
        query: str,
        intent: str,
        session_id: str,
        history: list[dict],
        image_name: str = "",
    ) -> AnalysisResponse:
        # Simulate realistic processing time
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Check if this is a follow-up
        if history:
            return await self.follow_up_query(query, session_id, history)

        data = DEMO_RESPONSES.get(intent, DEMO_RESPONSES["GENERAL_DESCRIPTION"])

        objects = [
            ObjectDetection(
                label=o["label"],
                count=o["count"],
                confidence=o["confidence"],
                regions=[EvidenceRegion(**r) for r in o.get("regions", [])],
            )
            for o in data.get("objects", [])
        ]

        lc = data.get("land_cover")
        land_cover = LandCover(**lc) if lc else None

        findings = [
            Finding(
                finding=f["finding"],
                confidence=f["confidence"],
                evidence_quality=f["evidence_quality"],
                evidence_description=f["evidence_description"],
                limitations=f["limitations"],
                region=EvidenceRegion(**f["region"]) if f.get("region") else None,
            )
            for f in data.get("findings", [])
        ]

        from app.services.insight_service import generate_insight
        gov = generate_insight(intent)

        return AnalysisResponse(
            answer=data["answer"],
            intent=intent,
            confidence=findings[0].confidence if findings else 0.80,
            objects=objects,
            land_cover=land_cover,
            findings=findings,
            observations=data.get("observations", []),
            evidence=[f.evidence_description for f in findings],
            government_use=gov,
            limitations=[
                "AI-estimated visual interpretation from demo data.",
                "Demonstration mode — not connected to a live AI model.",
                "Field verification recommended for any actionable decisions.",
            ],
            session_id=session_id,
            mode="demo",
        )

    async def compare_images(
        self,
        before_bytes: bytes,
        after_bytes: bytes,
        query: str,
        session_id: str,
        history: list[dict],
    ) -> CompareResponse:
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Detect if flood-related
        q = query.lower()
        is_flood = any(w in q for w in ["flood", "water", "inundat"])
        data = DEMO_FLOOD_COMPARISON if is_flood else DEMO_COMPARISON

        changes = [
            ChangeDetection(
                type=c["type"],
                severity=c["severity"],
                description=c["description"],
                confidence=c["confidence"],
                evidence_description=c["evidence_description"],
                region=EvidenceRegion(**c["region"]) if c.get("region") else None,
            )
            for c in data["changes"]
        ]

        findings = [
            Finding(
                finding=f["finding"],
                confidence=f["confidence"],
                evidence_quality=f["evidence_quality"],
                evidence_description=f["evidence_description"],
                limitations=f["limitations"],
                region=EvidenceRegion(**f["region"]) if f.get("region") else None,
            )
            for f in data["findings"]
        ]

        from app.services.insight_service import generate_change_insight
        gov = generate_change_insight(changes)

        # Generate real heatmap from actual images
        from app.utils.image_utils import generate_difference_heatmap
        heatmap = generate_difference_heatmap(before_bytes, after_bytes)

        return CompareResponse(
            overall_change=data["overall_change"],
            changes=changes,
            findings=findings,
            government_use=gov,
            heatmap_base64=heatmap,
            limitations=[
                "AI-assisted visual change interpretation — demo mode.",
                "Visual Change Map is a pixel-difference visualization, not scientific change detection.",
                "Field verification required for actionable decisions.",
            ],
            session_id=session_id,
            mode="demo",
        )

    async def follow_up_query(
        self,
        query: str,
        session_id: str,
        history: list[dict],
    ) -> AnalysisResponse:
        await asyncio.sleep(random.uniform(0.3, 0.8))

        key = _match_followup_key(query)
        data = FOLLOWUP_CHAINS.get(key, FOLLOWUP_CHAINS["default"])

        findings = [
            Finding(
                finding=f["finding"],
                confidence=f["confidence"],
                evidence_quality=f["evidence_quality"],
                evidence_description=f["evidence_description"],
                limitations=f["limitations"],
                region=EvidenceRegion(**f["region"]) if f.get("region") else None,
            )
            for f in data.get("findings", [])
        ]

        from app.services.insight_service import generate_insight
        intent = classify_intent(query)
        gov = generate_insight(intent)

        return AnalysisResponse(
            answer=data["answer"],
            intent=intent,
            confidence=findings[0].confidence if findings else 0.80,
            objects=[],
            land_cover=None,
            findings=findings,
            observations=[],
            evidence=[f.evidence_description for f in findings],
            government_use=gov,
            limitations=["AI-estimated response in demo mode.", "Field verification recommended."],
            session_id=session_id,
            mode="demo",
        )
