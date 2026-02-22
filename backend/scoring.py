"""Deterministic TrustScore computation — no LLM involved."""

# Attribute weights — must sum to 100
ATTRIBUTE_WEIGHTS: dict[str, tuple[int, str]] = {
    # id: (weight, human-readable label)
    "data_selling":        (15, "Sells User Data"),
    "data_sharing":        (10, "Shares Data with Partners"),
    "account_deletion":    (10, "Account & Data Deletion"),
    "encryption":          (10, "Data Encryption"),
    "data_retention":      (8,  "Data Retention Period"),
    "third_party_tracking":(10, "Third-Party Tracking"),
    "government_requests": (7,  "Government Data Requests"),
    "arbitration_clause":  (8,  "Mandatory Arbitration"),
    "class_action_waiver": (7,  "Class-Action Waiver"),
    "unilateral_changes":  (5,  "Unilateral Terms Changes"),
    "liability_limitation":(5,  "Liability Limitation"),
    "content_license":     (5,  "License to Your Content"),
}

GRADE_THRESHOLDS = [
    (80, "A"),
    (60, "B"),
    (40, "C"),
    (20, "D"),
    (0,  "F"),
]


def get_label(attribute_id: str) -> str:
    """Return human-readable label for an attribute id."""
    entry = ATTRIBUTE_WEIGHTS.get(attribute_id)
    return entry[1] if entry else attribute_id.replace("_", " ").title()


def get_weight(attribute_id: str) -> int:
    """Return the point weight for an attribute id."""
    entry = ATTRIBUTE_WEIGHTS.get(attribute_id)
    return entry[0] if entry else 0


def severity_to_multiplier(severity: str) -> float:
    """Convert severity string to a score multiplier."""
    mapping = {"good": 1.0, "neutral": 0.5, "bad": 0.0}
    return mapping.get(severity.lower(), 0.0)


def compute_score(
    attributes: list[dict],
) -> tuple[int, str, list[dict]]:
    """
    Compute TrustScore from a list of attribute dicts.
    
    Each attribute dict must have at least: id, value, severity, evidence.
    
    Returns: (score 0-100, grade letter, enriched attributes with weight/points)
    """
    total = 0.0
    enriched = []

    for attr in attributes:
        attr_id = attr["id"]
        weight = get_weight(attr_id)
        multiplier = severity_to_multiplier(attr.get("severity", "bad"))
        points = weight * multiplier

        enriched.append({
            "id": attr_id,
            "label": get_label(attr_id),
            "value": attr.get("value", "Unknown"),
            "severity": attr.get("severity", "bad"),
            "evidence": attr.get("evidence", "No evidence found."),
            "weight": weight,
            "points_earned": round(points, 1),
        })
        total += points

    score = min(100, max(0, round(total)))

    grade = "F"
    for threshold, letter in GRADE_THRESHOLDS:
        if score >= threshold:
            grade = letter
            break

    return score, grade, enriched
