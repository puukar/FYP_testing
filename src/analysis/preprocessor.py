"""
Stage 7 + 8 (merged) â€” Synonym Normalization + Text Preparation
"""

from __future__ import annotations
from typing import Dict, List
import re

from src.analysis.skill_synonyms import SKILL_SYNONYMS


def clean_term(term: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for a single term."""
    if not term:
        return ""
    term = term.lower()
    term = re.sub(r"[^\w\s]", " ", term)
    term = re.sub(r"\s+", " ", term).strip()
    return term


def _build_lookup(synonyms_map: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Flips {base_skill: [variants]} into {cleaned_variant: base_skill}.
    Runs every key/variant through the SAME clean_term() used on incoming
    data, so "react.js" (dict) and "React.js" (incoming) both clean down
    to "react js" and actually match.
    """
    lookup = {}
    for base_skill, variants in synonyms_map.items():
        base_clean = clean_term(base_skill)
        lookup[base_clean] = base_clean
        for variant in variants:
            variant_clean = clean_term(variant)
            if variant_clean:
                lookup[variant_clean] = base_clean
    return lookup


_SYNONYM_LOOKUP = _build_lookup(SKILL_SYNONYMS)


def tokenize_section(items: List[str], apply_synonyms: bool = False) -> List[str]:
    seen = set()
    tokens = []
    for item in items:
        cleaned = clean_term(item)
        if not cleaned:
            continue
        if apply_synonyms:
            cleaned = _SYNONYM_LOOKUP.get(cleaned, cleaned)
        if cleaned not in seen:
            seen.add(cleaned)
            tokens.append(cleaned)
    return tokens


def prepare_profile(profile: Dict[str, List[str]]) -> Dict[str, List[str]]:
    return {
        "skills": tokenize_section(profile.get("skills", []), apply_synonyms=True),
        "education": tokenize_section(profile.get("education", []), apply_synonyms=False),
        "experience": tokenize_section(profile.get("experience", []), apply_synonyms=False),
        "projects": tokenize_section(profile.get("projects", []), apply_synonyms=False),
    }


if __name__ == "__main__":
    sample = {
        "skills": ["ReactJS", "React.js", "Python3", "MySQL", "React"],
        "education": ["B.Sc Computer Science, XYZ University, 2022"],
        "experience": ["Software Engineer at ABC Corp (2022-2024)"],
        "projects": [],
    }
    import json
    print(json.dumps(prepare_profile(sample), indent=2))


