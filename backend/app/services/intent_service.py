"""Intent classification service — simple keyword-based, no ML required."""
from __future__ import annotations

INTENT_KEYWORDS: dict[str, list[str]] = {
    "BUILDING_ANALYSIS": ["building", "house", "structure", "structures", "built", "construction", "dwelling", "rooftop"],
    "ROAD_ANALYSIS": ["road", "highway", "street", "path", "lane", "intersection", "bridge", "pavement"],
    "WATER_ANALYSIS": ["water", "river", "lake", "pond", "reservoir", "stream", "canal", "ocean", "sea"],
    "FLOOD_ANALYSIS": ["flood", "flooding", "inundation", "submerged", "waterlogged", "deluge"],
    "VEGETATION_ANALYSIS": ["vegetation", "green", "crop", "plant", "tree", "forest", "canopy", "grassland", "ndvi", "biomass"],
    "URBAN_EXPANSION": ["urban", "city", "town", "expansion", "sprawl", "urbanization", "metropolitan"],
    "LAND_COVER": ["land cover", "land use", "landcover", "land-cover", "classification", "terrain"],
    "CHANGE_ANALYSIS": ["change", "changed", "before", "after", "growth", "increase", "decrease", "different", "comparison", "compare", "transform"],
    "AGRICULTURE": ["agriculture", "farm", "field", "crop", "harvest", "irrigation", "cultivat"],
    "FOREST": ["forest", "deforestation", "woodland", "timber", "logging"],
    "COASTAL": ["coast", "coastal", "shore", "beach", "mangrove", "erosion", "shoreline"],
    "ENCROACHMENT_SCREENING": ["encroach", "encroachment", "boundary", "violation", "illegal", "unauthorized", "trespass"],
    "OBJECT_DETECTION": ["object", "detect", "find", "identify", "locate", "count", "how many", "what objects", "visible"],
}


def classify_intent(query: str) -> str:
    """Classify a natural-language query into a supported intent."""
    q = query.lower().strip()

    # Score each intent by keyword match count
    scores: dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[intent] = score

    if not scores:
        return "GENERAL_DESCRIPTION"

    # Return highest-scoring intent
    return max(scores, key=scores.get)


def get_intent_prompt_context(intent: str) -> str:
    """Return additional prompt context for a given intent."""
    contexts = {
        "BUILDING_ANALYSIS": "Focus on identifying buildings, structures, and built-up areas. Estimate counts and density.",
        "ROAD_ANALYSIS": "Focus on roads, highways, paths, and transportation infrastructure.",
        "WATER_ANALYSIS": "Focus on water bodies — rivers, lakes, ponds, reservoirs, canals.",
        "FLOOD_ANALYSIS": "Focus on signs of flooding — water extent, inundation, affected areas, severity.",
        "VEGETATION_ANALYSIS": "Focus on vegetation cover — dense, sparse, type, health indicators visible in imagery.",
        "URBAN_EXPANSION": "Focus on urban/built-up area extent, density, and expansion patterns.",
        "LAND_COVER": "Estimate the visual composition of land cover types — built-up, vegetation, water, bare land.",
        "CHANGE_ANALYSIS": "Compare visible changes between images — new construction, vegetation changes, water changes.",
        "AGRICULTURE": "Focus on agricultural fields, crops, irrigation, farming patterns.",
        "FOREST": "Focus on forest cover, deforestation, woodland extent.",
        "COASTAL": "Focus on coastal features — shoreline, erosion, mangroves, coastal development.",
        "ENCROACHMENT_SCREENING": "Identify structures or development that may extend beyond expected boundaries. Use cautious language.",
        "OBJECT_DETECTION": "Identify and count visible objects — buildings, roads, vehicles, water bodies, vegetation patches.",
        "GENERAL_DESCRIPTION": "Provide a comprehensive description of the satellite imagery — features, terrain, land use patterns.",
    }
    return contexts.get(intent, contexts["GENERAL_DESCRIPTION"])
