"""
Stage 18 (orchestrator) — Full Analysis Pipeline

Runs Stages 3-16 in sequence and returns one consolidated result dict,
ready to display in Streamlit and save via resume_repository.save_full_analysis().

This is the ONLY new file needed to tie together everything built so far:
raw_text_extractor -> resume_structurer -> ideal_profile_generator ->
preprocessor -> tfidf -> similarity -> scorer -> skill_gap -> recommender.
"""

from __future__ import annotations
from typing import Dict, Any

from src.analysis.raw_text_extractor import extract_raw_text
from src.analysis.resume_structurer import structure_resume
from src.analysis.ideal_profile_generator import generate_ideal_profile
from src.analysis.preprocessor import prepare_profile
from src.analysis.tfidf import build_tfidf_vectors
from src.analysis.similarity import section_similarity
from src.analysis.scorer import compute_weighted_score
from src.analysis.skill_gap import compute_skill_gap
from src.analysis.recommender import generate_recommendations

SECTIONS = ["skills", "education", "experience", "projects"]


def run_full_analysis(file_path: str, target_role: str) -> Dict[str, Any]:
    """
    Runs the complete pipeline for one resume against one target role.

    Returns:
        {
            "raw_text": str,
            "resume_structured": {...},   # Stage 4 output (pre-normalization)
            "ideal_profile": {...},        # Stage 6 output (pre-normalization)
            "section_scores": {...},       # Stage 13, 0.0-1.0 fractions
            "overall_score": float,        # Stage 14, 0.0-1.0 fraction
            "matched_skills": [...],       # Stage 15
            "missing_skills": [...],       # Stage 15
            "extra_skills": [...],         # Stage 15
            "recommendations": [...],      # Stage 16
        }
    """
    # Stage 3
    raw_text = extract_raw_text(file_path)

    # Stage 4 - LLM #1
    resume_structured = structure_resume(raw_text)

    # Stage 6 - LLM #2
    ideal_profile = generate_ideal_profile(target_role)

    # Stage 7+8 - normalize both sides
    resume_clean = prepare_profile(resume_structured)
    ideal_clean = prepare_profile(ideal_profile)

    # Stage 9-13 - TF-IDF + cosine similarity, per section
    resume_vectors = {}
    ideal_vectors = {}
    for section in SECTIONS:
        vec_r, vec_i = build_tfidf_vectors(resume_clean[section], ideal_clean[section])
        resume_vectors[section] = vec_r
        ideal_vectors[section] = vec_i

    section_scores = section_similarity(resume_vectors, ideal_vectors)

    # Stage 14 - weighted overall score
    overall_score = compute_weighted_score(section_scores)

    # Stage 15 - skill gap (uses NORMALIZED skills so comparisons match)
    gap = compute_skill_gap(resume_clean["skills"], ideal_clean["skills"])

    # Stage 16 - LLM #3, recommendations based on missing skills
    recommendations = generate_recommendations(gap["missing_skills"])

    return {
        "raw_text": raw_text,
        "resume_structured": resume_structured,
        "ideal_profile": ideal_profile,
        "section_scores": section_scores,
        "overall_score": overall_score,
        "matched_skills": gap["matched_skills"],
        "missing_skills": gap["missing_skills"],
        "extra_skills": gap["extra_skills"],
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python -m src.analysis.pipeline <resume_path> <target_role>")
        sys.exit(1)

    result = run_full_analysis(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))



