"""
Stage 9-11 — TF, IDF, TF-IDF Vector (implemented from scratch, no sklearn)

Uses SMOOTHED IDF to avoid zero-weighting terms that appear in every
document being compared (a real risk with only 2 documents — resume vs
ideal profile — where any genuinely matching skill would otherwise get
IDF=0 and vanish from the similarity calculation).

Smoothed IDF formula (same approach scikit-learn uses by default,
smooth_idf=True):
    IDF(term) = log( (1 + N) / (1 + df) ) + 1
    where N  = total number of documents
          df = number of documents containing the term

The "+1" in numerator/denominator prevents division issues and ensures
even a term present in every document keeps a small positive weight
instead of dropping to exactly 0.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import math


def tokenize_document(items: List[str]) -> List[str]:
    """
    Joins a section's list of strings into one blob and splits into words.
    Items are assumed already cleaned (lowercase, punctuation-stripped) by
    preprocessor.py - this just does the word-splitting.
    """
    blob = " ".join(items)
    words = [w for w in blob.split(" ") if w.strip()]
    return words


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """
    Stage 9 - Term Frequency.
    Raw count of each word within a single document.
    """
    tf = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    return tf


def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """
    Stage 10 - Inverse Document Frequency (SMOOTHED).
    IDF(term) = log( (1 + N) / (1 + df) ) + 1

    documents: a list of token-lists, one per document
               (in our 2-document setup: [resume_tokens, ideal_tokens])
    """
    total_docs = len(documents)
    doc_count_per_term: Dict[str, int] = {}

    for doc_tokens in documents:
        unique_terms_in_doc = set(doc_tokens)
        for term in unique_terms_in_doc:
            doc_count_per_term[term] = doc_count_per_term.get(term, 0) + 1

    idf = {}
    for term, doc_count in doc_count_per_term.items():
        idf[term] = math.log((1 + total_docs) / (1 + doc_count)) + 1

    return idf


def compute_tfidf_vector(tf: Dict[str, float], idf: Dict[str, float]) -> Dict[str, float]:
    """
    Stage 11 - TF-IDF Vector.
    TF-IDF(term) = TF(term) * IDF(term)
    """
    vector = {}
    for term, freq in tf.items():
        vector[term] = freq * idf.get(term, 0.0)
    return vector


def build_tfidf_vectors(
    doc_a_items: List[str],
    doc_b_items: List[str],
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Orchestrates Stage 9-11 for a pair of documents (e.g. resume section vs
    ideal profile section for the SAME section).

    Returns (vector_a, vector_b) - term -> tfidf-weight dicts,
    ready for cosine similarity in Stage 12.
    """
    tokens_a = tokenize_document(doc_a_items)
    tokens_b = tokenize_document(doc_b_items)

    tf_a = compute_tf(tokens_a)
    tf_b = compute_tf(tokens_b)

    idf = compute_idf([tokens_a, tokens_b])

    vector_a = compute_tfidf_vector(tf_a, idf)
    vector_b = compute_tfidf_vector(tf_b, idf)

    return vector_a, vector_b


if __name__ == "__main__":
    resume_skills = ["react", "python", "sql"]
    ideal_skills = ["react", "git", "javascript", "html", "css"]

    vec_resume, vec_ideal = build_tfidf_vectors(resume_skills, ideal_skills)

    import json
    print("Resume TF-IDF vector:")
    print(json.dumps(vec_resume, indent=2))
    print("\nIdeal Profile TF-IDF vector:")
    print(json.dumps(vec_ideal, indent=2))
