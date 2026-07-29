"""
Stage 12-13 — Cosine Similarity + Section-Based Comparison (from scratch)

Cosine similarity formula:
    similarity = (A . B) / (||A|| * ||B||)
    where A . B    = dot product of the two vectors
          ||A||    = magnitude (Euclidean norm) of vector A
          ||B||    = magnitude (Euclidean norm) of vector B

Operates on the TF-IDF vectors produced by tfidf.py for ONE section at a
time (e.g. resume["skills"] vs ideal["skills"]). Section-wise comparison
(Stage 13) is just calling this once per section.
"""

from __future__ import annotations
from typing import Dict
import math


def dot_product(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Sum of (weight_a * weight_b) for every term that appears in EITHER vector.
    Terms missing from one side contribute 0 for that side automatically
    (via .get(term, 0.0)).
    """
    all_terms = set(vec_a.keys()) | set(vec_b.keys())
    return sum(vec_a.get(term, 0.0) * vec_b.get(term, 0.0) for term in all_terms)


def magnitude(vec: Dict[str, float]) -> float:
    """Euclidean norm: sqrt(sum of squares of all weights in the vector)."""
    return math.sqrt(sum(weight ** 2 for weight in vec.values()))


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Stage 12 - Cosine Similarity.
    Returns a value between 0.0 and 1.0 (1.0 = identical direction, i.e.
    perfect match; 0.0 = no overlap at all).

    Handles the edge case where one vector is empty (e.g. resume has no
    "projects" at all) - returns 0.0 instead of crashing on a divide-by-zero,
    since an empty section genuinely has 0% similarity to a non-empty one.
    """
    mag_a = magnitude(vec_a)
    mag_b = magnitude(vec_b)

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot_product(vec_a, vec_b) / (mag_a * mag_b)


def section_similarity(
    resume_tfidf_vectors: Dict[str, Dict[str, float]],
    ideal_tfidf_vectors: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """
    Stage 13 - Section-Based Comparison.
    Given TF-IDF vectors for each section (already built via
    tfidf.build_tfidf_vectors for each of skills/education/experience/projects),
    returns a similarity score (0.0-1.0) per section.

    Expects both dicts to have the same section keys, e.g.:
        {"skills": {...vector...}, "education": {...}, "experience": {...}, "projects": {...}}
    """
    scores = {}
    for section in resume_tfidf_vectors:
        resume_vec = resume_tfidf_vectors[section]
        ideal_vec = ideal_tfidf_vectors.get(section, {})
        scores[section] = cosine_similarity(resume_vec, ideal_vec)
    return scores


if __name__ == "__main__":
    from src.analysis.tfidf import build_tfidf_vectors

    # simulate one section (skills) end to end
    resume_skills = ["react", "python", "sql"]
    ideal_skills = ["react", "git", "javascript", "html", "css"]

    vec_resume, vec_ideal = build_tfidf_vectors(resume_skills, ideal_skills)
    score = cosine_similarity(vec_resume, vec_ideal)

    print(f"Skills similarity: {score:.4f} ({score * 100:.1f}%)")

    # simulate an empty section (e.g. no projects on resume)
    empty_score = cosine_similarity({}, {"portfolio": 1.4, "ecommerce": 1.4})
    print(f"Empty-section similarity (expected 0.0): {empty_score:.4f}")


