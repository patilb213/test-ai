"""
Test AI — Semantic Element Matching Engine

Uses sentence-transformer embeddings to rank candidate UI elements.
Does not automatically click or approve a replacement.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_semantic_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "AI semantic matching requires sentence-transformers. "
            "Install it with: python -m pip install sentence-transformers"
        ) from exc

    return SentenceTransformer(MODEL_NAME)


def element_description(element: dict[str, Any]) -> str:
    """Build a semantic description without input values."""

    fields = (
        "role",
        "name",
        "label",
        "placeholder",
        "text",
        "tag",
        "type",
        "containerText",
    )

    parts = []

    for field in fields:
        value = element.get(field)

        if value:
            parts.append(f"{field}: {str(value)[:200]}")

    return " | ".join(parts)


def rank_semantic_candidates(
    original: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    limit: int = 5,
    model=None,
) -> list[dict[str, Any]]:
    """
    Rank potential replacements by semantic similarity.

    The caller must separately verify that each candidate
    exists uniquely and is safe to interact with.
    """

    if not isinstance(original, dict):
        raise ValueError("Original target must be a dictionary.")

    if not candidates:
        return []

    original_description = element_description(original)

    if not original_description:
        return []

    prepared = [
        (candidate, element_description(candidate))
        for candidate in candidates
        if isinstance(candidate, dict)
    ]

    prepared = [
        (candidate, description)
        for candidate, description in prepared
        if description
    ]

    if not prepared:
        return []

    encoder = model if model is not None else get_semantic_model()

    descriptions = [
        original_description,
        *[description for _, description in prepared],
    ]

    vectors = encoder.encode(
        descriptions,
        normalize_embeddings=True,
    )

    results = []

    original_vector = vectors[0]

    for index, (candidate, description) in enumerate(prepared):
        candidate_vector = vectors[index + 1]

        similarity = float(
            sum(
                float(a) * float(b)
                for a, b in zip(original_vector, candidate_vector)
            )
        )

        similarity = max(-1.0, min(1.0, similarity))

        results.append({
            "candidate": candidate,
            "description": description,
            "semantic_similarity": round(similarity, 4),
            "model": MODEL_NAME,
            "requires_validation": True,
        })

    results.sort(
        key=lambda item: item["semantic_similarity"],
        reverse=True,
    )

    return results[:max(0, limit)]


def evaluate_semantic_recovery(
    ranked_candidates: list[dict[str, Any]],
    *,
    minimum_similarity: float = 0.80,
    minimum_margin: float = 0.08,
) -> dict[str, Any]:
    """
    Return a recommendation, never an automatic approval.

    Similarity is not a calibrated probability of correctness.
    """

    if not ranked_candidates:
        return {
            "status": "NO_MATCH",
            "recommended_candidate": None,
        }

    best = ranked_candidates[0]
    runner_up = (
        ranked_candidates[1]["semantic_similarity"]
        if len(ranked_candidates) > 1
        else 0.0
    )

    score = best["semantic_similarity"]
    margin = score - runner_up

    if score >= minimum_similarity and margin >= minimum_margin:
        status = "VALIDATION_REQUIRED"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "status": status,
        "recommended_candidate": best["candidate"],
        "semantic_similarity": score,
        "margin": round(margin, 4),
        "model": MODEL_NAME,
    }
