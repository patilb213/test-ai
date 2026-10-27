from dataclasses import dataclass
from typing import Optional


MINIMUM_CONFIDENCE = 0.85
AUTO_APPROVAL_CONFIDENCE = 0.95


@dataclass(frozen=True)
class HealingDecision:
    confidence: float
    status: str
    reason: str


def evaluate_healing_candidate(
    base_confidence: float,
    context_similarity: Optional[float] = None,
    unique: bool = True,
) -> HealingDecision:
    """
    Evaluate a fallback locator candidate.

    This function scores the evidence supplied by the
    locator engine. It does not execute browser actions.
    """

    confidence = max(
        0.0,
        min(1.0, float(base_confidence)),
    )

    if not unique:
        return HealingDecision(
            confidence=0.0,
            status="REJECTED",
            reason="Locator matches multiple elements.",
        )

    if context_similarity is not None:
        similarity = max(
            0.0,
            min(1.0, float(context_similarity)),
        )

        if similarity < 0.60:
            return HealingDecision(
                confidence=0.0,
                status="REJECTED",
                reason="Recorded container context does not match.",
            )

        confidence = round(
            confidence * (0.70 + 0.30 * similarity),
            4,
        )

    if confidence < MINIMUM_CONFIDENCE:
        status = "REJECTED"
        reason = "Confidence is below the safety threshold."

    elif confidence < AUTO_APPROVAL_CONFIDENCE:
        status = "REVIEW_REQUIRED"
        reason = "Candidate requires user approval."

    else:
        status = "HIGH_CONFIDENCE"
        reason = "Candidate passed confidence checks."

    return HealingDecision(
        confidence=confidence,
        status=status,
        reason=reason,
    )