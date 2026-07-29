"""
src/analysis/minhash_similarity.py

Estimates Jaccard similarity between two resumes using a hand-implemented
MinHash (Minwise Hashing) algorithm.

Deliberately kept separate from `similarity.py` in this same folder, since
that module likely already handles TF-IDF-based resume/job matching
(consistent with tfidf.py, scorer.py, recommender.py in this project).
This module is for a different use case: near-duplicate / overlap
detection between two resumes via MinHash-estimated Jaccard similarity.

No external ML/math libraries — only `hashlib`, `random`, and `re` from
the standard library.
"""

import hashlib
import random
import re

# --------------------------------------------------------------------------
# Tokenization / shingling
# --------------------------------------------------------------------------

_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text


def tokenize(text: str) -> list:
    """Split cleaned text into a list of word tokens."""
    cleaned = clean_text(text)
    return cleaned.split(" ") if cleaned else []


def get_shingles(text: str, k: int = 3) -> set:
    """
    Build the set of word-level k-shingles (k-grams) for a document.

    e.g. tokens=["senior","python","developer"], k=2
      -> {"senior python", "python developer"}
    """
    tokens = tokenize(text)
    if not tokens:
        return set()
    if len(tokens) < k:
        return {" ".join(tokens)}
    return {" ".join(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}


# --------------------------------------------------------------------------
# MinHash
# --------------------------------------------------------------------------

# A large prime > 2^32, used as the modulus for universal hashing
# (Mersenne prime 2^61 - 1).
_MERSENNE_PRIME = (1 << 61) - 1
_MAX_HASH_32 = (1 << 32) - 1


def _string_to_int(s: str) -> int:
    """Deterministically map a string to an int in [0, 2^32 - 1] via SHA-256."""
    digest = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(digest, 16) % (_MAX_HASH_32 + 1)


class MinHash:
    """
    A MinHash sketch built from a family of `num_perm` simulated random
    permutations, implemented via universal hashing:

        h_i(x) = (a_i * x + b_i) mod p

    For each shingle x in the document, compute h_i(x) for every i and
    keep the running minimum. The resulting vector of minima is the
    MinHash signature.
    """

    def __init__(self, num_perm: int = 128, seed: int = 42):
        if num_perm < 1:
            raise ValueError("num_perm must be >= 1")

        self.num_perm = num_perm
        self.seed = seed

        rng = random.Random(seed)
        self.a = [rng.randint(1, _MERSENNE_PRIME - 1) for _ in range(num_perm)]
        self.b = [rng.randint(0, _MERSENNE_PRIME - 1) for _ in range(num_perm)]

        self.signature = [_MERSENNE_PRIME] * num_perm

    def update(self, shingles) -> None:
        for shingle in shingles:
            x = _string_to_int(shingle)
            a, b, sig = self.a, self.b, self.signature
            for i in range(self.num_perm):
                hashed = (a[i] * x + b[i]) % _MERSENNE_PRIME
                if hashed < sig[i]:
                    sig[i] = hashed

    def get_signature(self) -> list:
        return list(self.signature)

    @staticmethod
    def jaccard(sig1: list, sig2: list) -> float:
        if len(sig1) != len(sig2):
            raise ValueError("Signatures must be the same length")
        if not sig1:
            return 0.0
        matches = sum(1 for x, y in zip(sig1, sig2) if x == y)
        return matches / len(sig1)


def exact_jaccard(set1: set, set2: set) -> float:
    """Ground-truth Jaccard similarity computed directly on shingle sets."""
    if not set1 and not set2:
        return 0.0
    union = len(set1 | set2)
    if union == 0:
        return 0.0
    return len(set1 & set2) / union


# --------------------------------------------------------------------------
# High-level entry point
# --------------------------------------------------------------------------

def compare_resumes(
    text1: str,
    text2: str,
    num_perm: int = 128,
    k: int = 3,
    seed: int = 42,
) -> dict:
    """
    Compare two resumes (raw text) using MinHash-estimated Jaccard
    similarity, plus exact Jaccard for reference.
    """
    shingles1 = get_shingles(text1, k=k)
    shingles2 = get_shingles(text2, k=k)

    mh1 = MinHash(num_perm=num_perm, seed=seed)
    mh1.update(shingles1)

    mh2 = MinHash(num_perm=num_perm, seed=seed)
    mh2.update(shingles2)

    sig1 = mh1.get_signature()
    sig2 = mh2.get_signature()

    matches = sum(1 for x, y in zip(sig1, sig2) if x == y)

    return {
        "estimated_jaccard": MinHash.jaccard(sig1, sig2),
        "exact_jaccard": exact_jaccard(shingles1, shingles2),
        "matches": matches,
        "num_perm": num_perm,
        "k": k,
        "sig1": sig1,
        "sig2": sig2,
        "shingles1_count": len(shingles1),
        "shingles2_count": len(shingles2),
        "shared_shingles": len(shingles1 & shingles2),
    }