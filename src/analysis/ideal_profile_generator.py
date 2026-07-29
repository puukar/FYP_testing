"""
Stage 6 — Generate Ideal Candidate Profile (LLM #2)

Given a target role (chosen by the user in Stage 5, e.g. from a dropdown),
asks Gemini to generate what an ideal candidate's resume would look like —
in the SAME schema as resume_structurer.py's output, so both sides can be
compared section-by-section later (Stage 9-14: TF-IDF, cosine similarity,
weighted scoring).

No scoring here — just generates the reference profile to compare against.
"""

from __future__ import annotations
from typing import Dict, List

from src.analysis.llm_client import generate_structured_json

# Same schema shape as resume_structurer.py — MUST stay identical so
# section-wise comparison in later stages lines up correctly.
IDEAL_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills/technologies an ideal candidate for this role should have.",
        },
        "education": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Typical education expected for this role.",
        },
        "experience": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Typical experience expected for this role.",
        },
        "projects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Typical project types that demonstrate this role's skills.",
        },
    },
    "required": ["skills", "education", "experience", "projects"],
}

_PROMPT_TEMPLATE = """You are defining the ideal candidate profile for a specific job role, \
to be used as a reference point for evaluating real resumes against.

Target role: {role}

Generate what an ideal candidate for this role would typically have, across four sections:
1. skills - key technologies/skills expected for this role (8-12 items, most important first)
2. education - typical education background expected (1-2 items)
3. experience - typical experience expected, phrased generally, not as a specific person's history \
(2-4 items)
4. projects - typical project types that would demonstrate readiness for this role (2-4 items)

"- Each skill must be a SINGLE atomic concept, not a bundled phrase. "
"Split compound skills into separate entries (e.g. 'GDPR', 'HIPAA', 'PCI-DSS' "
"as three separate skills, not one combined string). Avoid parenthetical "
"expansions - use the common short form only (e.g. 'SIEM', not "
"'Security Information and Event Management (SIEM)')."

Rules:
- Be realistic and specific to this role - not generic across all tech jobs.
- Keep skill names standardized (e.g. "React" not "reactjs", "JavaScript" not "js").
- This is a REFERENCE profile, not a real person - phrase entries generally.
- Do not include any scoring, ranking, or evaluation - only the profile itself.

Return JSON only, matching the schema exactly.
"""


def generate_ideal_profile(role: str) -> Dict[str, List[str]]:
    """
    Generates the ideal candidate profile for a given role via Gemini.
    Falls back to an all-empty structure if the LLM call fails
    (e.g. free-tier rate limit hit).
    """
    empty_result = {"skills": [], "education": [], "experience": [], "projects": []}

    if not role or not role.strip():
        return empty_result

    prompt = _PROMPT_TEMPLATE.format(role=role.strip())

    try:
        result = generate_structured_json(prompt, IDEAL_PROFILE_SCHEMA)
        return {
            "skills": result.get("skills", []),
            "education": result.get("education", []),
            "experience": result.get("experience", []),
            "projects": result.get("projects", []),
        }
    except RuntimeError as e:
        print(f"[ideal_profile_generator] LLM generation failed: {e}")
        return empty_result


if __name__ == "__main__":
    import json
    profile = generate_ideal_profile("Junior Web Developer")
    print(json.dumps(profile, indent=2))
