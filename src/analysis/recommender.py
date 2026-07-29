"""
Stage 16 — Recommendation Engine (LLM #3)

Takes ONLY the missing_skills list (from skill_gap.py) and generates
practical learning recommendations. Does NOT affect the score in any way —
this runs strictly after scoring is complete, purely for user guidance.

This is the THIRD Gemini call in the pipeline (after Stage 4 resume
structuring and Stage 6 ideal profile generation) — worth keeping in mind
for your 250-requests/day free tier budget: 3 calls per full analysis.
"""

from __future__ import annotations
from typing import Dict, List

from src.analysis.llm_client import generate_structured_json

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Practical, actionable learning recommendations.",
        },
    },
    "required": ["recommendations"],
}

_PROMPT_TEMPLATE = """A candidate is missing the following skills for their target role: {missing_skills}

Generate 3-6 practical, actionable recommendations to help them close this gap.

Rules:
- Be specific and practical - not generic advice like "learn more" or "practice more".
- Where sensible, suggest a natural learning order (e.g. learn X before Y if X is a prerequisite).
- Include at least one project-based suggestion (e.g. "build a small app using X and Y together").
- Do NOT re-score, re-rank, or re-evaluate the candidate - only generate suggestions
  for the skills already identified as missing.
- Keep each recommendation to one clear sentence.

Return JSON only, matching the schema exactly.
"""


def generate_recommendations(missing_skills: List[str]) -> List[str]:
    """
    Generates learning recommendations for a list of missing skills via Gemini.
    Falls back to an empty list if the LLM call fails, or if there are no
    missing skills at all (nothing to recommend).
    """
    if not missing_skills:
        return []

    prompt = _PROMPT_TEMPLATE.format(missing_skills=missing_skills)

    try:
        result = generate_structured_json(prompt, RECOMMENDATION_SCHEMA)
        return result.get("recommendations", [])
    except RuntimeError as e:
        print(f"[recommender] LLM recommendation generation failed: {e}")
        return []


if __name__ == "__main__":
    import json
    sample_missing = [
        "javascript", "html5", "css3", "git",
        "responsive design", "restful apis",
        "node js", "typescript", "web performance optimization",
    ]
    recs = generate_recommendations(sample_missing)
    print(json.dumps(recs, indent=2))
