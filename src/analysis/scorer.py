"""
Stage 14 — Weighted Scoring

Combines the 4 section-wise similarity scores (from similarity.py) into
one overall match percentage, using fixed weights.
"""

from __future__ import annotations
from typing import Dict

# Must sum to 1.0
SECTION_WEIGHTS: Dict[str, float] = {
    "skills": 0.50,
    "experience": 0.25,
    "projects": 0.15,
    "education": 0.10,
}


def compute_weighted_score(section_scores: Dict[str, float]) -> float:
    """
    Combines section similarity scores (each 0.0-1.0) into one overall
    weighted score (0.0-1.0).
    """
    total = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        score = section_scores.get(section, 0.0)
        total += score * weight
    return total


def format_score_breakdown(section_scores: Dict[str, float]) -> Dict[str, str]:
    """
    Human-readable percentage breakdown, e.g. for dashboard display (Stage 18).
    """
    overall = compute_weighted_score(section_scores)
    breakdown = {
        section: f"{section_scores.get(section, 0.0) * 100:.1f}%"
        for section in SECTION_WEIGHTS
    }
    breakdown["overall"] = f"{overall * 100:.1f}%"
    return breakdown


if __name__ == "__main__":
    sample_section_scores = {
        "skills": 0.15,
        "experience": 0.60,
        "projects": 0.0,
        "education": 0.88,
    }

    import json
    print(json.dumps(format_score_breakdown(sample_section_scores), indent=2))
