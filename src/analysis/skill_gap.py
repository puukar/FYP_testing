"""
Stage 15 — Missing Skill Detection

Simple set difference: given the ideal profile's skills and the resume's
(normalized) skills, find what's missing and what's already matched.

Operates on the CLEANED/NORMALIZED skill lists from preprocessor.py
(e.g. resume_clean["skills"], ideal_clean["skills"]) — so comparisons
are apples-to-apples (both sides already lowercased, synonym-normalized).
"""

from __future__ import annotations
from typing import Dict, List


def compute_skill_gap(
    resume_skills: List[str],
    ideal_skills: List[str],
) -> Dict[str, List[str]]:
    """
    Compares resume skills against the ideal profile's skills.

    Returns:
        {
            "matched_skills": [...],   # skills the resume already has, that
                                       # are also in the ideal profile
            "missing_skills": [...],  # skills the ideal profile wants,
                                       # that the resume does NOT have
            "extra_skills": [...],    # skills the resume has that aren't
                                      # in the ideal profile (not "missing",
                                      # just not relevant to this specific role)
        }
    """
    resume_set = set(resume_skills)
    ideal_set = set(ideal_skills)

    matched = sorted(resume_set & ideal_set)
    missing = sorted(ideal_set - resume_set)
    extra = sorted(resume_set - ideal_set)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
    }


if __name__ == "__main__":
    # using the same real data from earlier tests
    resume_skills = ["python", "react", "sql", "docker"]
    ideal_skills = [
        "javascript", "html5", "css3", "react", "git",
        "responsive design", "restful apis", "node js",
        "typescript", "web performance optimization",
    ]

    import json
    result = compute_skill_gap(resume_skills, ideal_skills)
    print(json.dumps(result, indent=2))
