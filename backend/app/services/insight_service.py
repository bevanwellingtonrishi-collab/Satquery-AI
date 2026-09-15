"""Government insight engine — maps analysis findings to relevant departments."""
from __future__ import annotations
from app.models.schemas import GovernmentUse


INSIGHT_MAP: dict[str, dict] = {
    "BUILDING_ANALYSIS": {
        "department": "Urban Planning / Municipal Administration",
        "issue": "Building density and development patterns",
        "priority": "MEDIUM",
        "recommended_action": "Review recent development against approved land-use and building permits.",
        "reasoning": "Building pattern analysis helps urban planning authorities monitor development compliance.",
    },
    "ROAD_ANALYSIS": {
        "department": "Public Works Department / Municipal Authorities",
        "issue": "Road infrastructure assessment",
        "priority": "MEDIUM",
        "recommended_action": "Cross-reference observed road network with planned infrastructure projects.",
        "reasoning": "Road network monitoring supports infrastructure planning and maintenance prioritization.",
    },
    "WATER_ANALYSIS": {
        "department": "Water Resources / Irrigation Department",
        "issue": "Water body status and extent",
        "priority": "MEDIUM",
        "recommended_action": "Verify water body boundaries and assess resource availability.",
        "reasoning": "Water body monitoring supports resource management and environmental protection.",
    },
    "FLOOD_ANALYSIS": {
        "department": "Disaster Management Authority",
        "issue": "Potential flood impact assessment",
        "priority": "HIGH",
        "recommended_action": "Initiate field verification of affected areas and coordinate emergency response if validated.",
        "reasoning": "Flood screening supports early warning and disaster preparedness.",
    },
    "VEGETATION_ANALYSIS": {
        "department": "Forest Department / Environment Ministry",
        "issue": "Vegetation cover assessment",
        "priority": "MEDIUM",
        "recommended_action": "Assess vegetation change against baseline data and environmental regulations.",
        "reasoning": "Vegetation monitoring supports forest conservation and environmental compliance.",
    },
    "URBAN_EXPANSION": {
        "department": "Urban Planning / Municipal Administration",
        "issue": "Urban expansion and development pressure",
        "priority": "HIGH",
        "recommended_action": "Review urban growth patterns against master plan and zoning regulations.",
        "reasoning": "Urban expansion monitoring is critical for sustainable development planning.",
    },
    "LAND_COVER": {
        "department": "Land Records / Revenue Department",
        "issue": "Land-use pattern assessment",
        "priority": "MEDIUM",
        "recommended_action": "Compare observed land-use with official land records and classifications.",
        "reasoning": "Land-cover monitoring helps maintain accurate land records and detect unauthorized changes.",
    },
    "CHANGE_ANALYSIS": {
        "department": "Urban Planning / Municipal Administration",
        "issue": "Temporal change detection in land use",
        "priority": "HIGH",
        "recommended_action": "Investigate significant changes and verify against approved development plans.",
        "reasoning": "Change detection reveals development trends requiring administrative attention.",
    },
    "AGRICULTURE": {
        "department": "Agriculture Department",
        "issue": "Agricultural land-use and crop patterns",
        "priority": "MEDIUM",
        "recommended_action": "Assess crop coverage and agricultural activity against seasonal expectations.",
        "reasoning": "Agricultural monitoring supports food security planning and farmer support programs.",
    },
    "FOREST": {
        "department": "Forest Department / Environment Ministry",
        "issue": "Forest cover assessment",
        "priority": "HIGH",
        "recommended_action": "Verify forest cover changes against protected area boundaries and logging permits.",
        "reasoning": "Forest monitoring is critical for conservation and compliance with environmental laws.",
    },
    "COASTAL": {
        "department": "Coastal Zone Management / Environment Department",
        "issue": "Coastal area assessment",
        "priority": "HIGH",
        "recommended_action": "Review coastal changes against CRZ regulations and environmental protection guidelines.",
        "reasoning": "Coastal monitoring supports erosion management and environmental protection.",
    },
    "ENCROACHMENT_SCREENING": {
        "department": "Revenue / Local Administration",
        "issue": "Potential encroachment screening",
        "priority": "HIGH",
        "recommended_action": "Conduct field verification of structures identified near boundaries. This is a screening indicator only.",
        "reasoning": "Encroachment screening identifies areas requiring on-ground inspection, not legal determination.",
    },
    "OBJECT_DETECTION": {
        "department": "Urban Planning / Survey Department",
        "issue": "Object and feature inventory",
        "priority": "LOW",
        "recommended_action": "Use detected features to update geospatial databases and planning documents.",
        "reasoning": "Object detection provides an overview of visible features for inventory and planning.",
    },
    "GENERAL_DESCRIPTION": {
        "department": "Multi-departmental",
        "issue": "General area assessment",
        "priority": "LOW",
        "recommended_action": "Route findings to the relevant department based on the primary features observed.",
        "reasoning": "General description provides an overview for preliminary assessment.",
    },
}


def generate_insight(intent: str, findings: list = None, severity: str = None) -> GovernmentUse:
    """Generate government insight based on analysis intent and findings."""
    base = INSIGHT_MAP.get(intent, INSIGHT_MAP["GENERAL_DESCRIPTION"])

    priority = base["priority"]
    # Escalate priority based on severity
    if severity == "high" or (findings and len(findings) > 3):
        priority = "HIGH"

    return GovernmentUse(
        department=base["department"],
        issue=base["issue"],
        priority=priority,
        recommended_action=base["recommended_action"],
        reasoning=base["reasoning"],
    )


def generate_change_insight(changes: list) -> GovernmentUse:
    """Generate insight specifically for change detection results."""
    if not changes:
        return generate_insight("GENERAL_DESCRIPTION")

    # Find the most severe change
    severity_order = {"high": 3, "medium": 2, "low": 1}
    most_severe = max(changes, key=lambda c: severity_order.get(getattr(c, 'severity', 'low'), 0))

    change_type = getattr(most_severe, 'type', '')

    # Map change types to intents
    type_intent_map = {
        "urban_expansion": "URBAN_EXPANSION",
        "building_increase": "BUILDING_ANALYSIS",
        "vegetation_loss": "VEGETATION_ANALYSIS",
        "vegetation_gain": "VEGETATION_ANALYSIS",
        "water_expansion": "FLOOD_ANALYSIS",
        "water_change": "WATER_ANALYSIS",
        "road_expansion": "ROAD_ANALYSIS",
        "coastal_change": "COASTAL",
        "agricultural_change": "AGRICULTURE",
        "forest_change": "FOREST",
        "construction": "BUILDING_ANALYSIS",
    }

    intent = type_intent_map.get(change_type, "CHANGE_ANALYSIS")
    severity = getattr(most_severe, 'severity', 'medium')
    return generate_insight(intent, severity=severity)
