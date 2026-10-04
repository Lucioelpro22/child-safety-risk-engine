from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from child_safety_risk_engine import (
    AgeContext,
    MessageInput,
    RiskAssessment,
    RiskLevel,
    RiskScore,
    Signal,
    SignalCategory,
)


def test_message_accepts_pseudonymous_refs_and_age_band() -> None:
    message = MessageInput(
        message_id=uuid4(),
        sender_ref="sha256:abc12345",
        recipient_ref="sha256:def67890",
        text="Please do not tell anyone.",
        age_context=AgeContext(age_years=14, age_band="13_15"),
    )
    assert message.age_context.age_band == "13_15"
    assert "text" in message.model_dump()


@pytest.mark.parametrize("ref", ["person@example.com", "+54 11 5555-5555", "name"])
def test_direct_identifiers_are_rejected(ref: str) -> None:
    with pytest.raises(ValidationError):
        MessageInput(
            message_id=uuid4(),
            sender_ref=ref,
            recipient_ref="sha256:def67890",
            text="hello",
        )


def test_age_context_rejects_inconsistent_band() -> None:
    with pytest.raises(ValidationError):
        AgeContext(age_years=12, age_band="13_15")


def test_signal_validates_range_and_score() -> None:
    with pytest.raises(ValidationError):
        Signal(category=SignalCategory.THREAT, confidence=1.2, rationale="threat")
    with pytest.raises(ValidationError):
        Signal(
            category=SignalCategory.THREAT,
            confidence=0.8,
            evidence_span=(8, 4),
            rationale="threat",
        )
    score = RiskScore(value=0.9, level=RiskLevel.HIGH, model_version="0.1.0")
    assert score.value == 0.9


def test_assessment_does_not_require_raw_message() -> None:
    assessment = RiskAssessment(
        assessment_id=uuid4(),
        message_id=uuid4(),
        score=RiskScore(value=0.7, level=RiskLevel.HIGH, model_version="0.1.0"),
        signals=[
            Signal(
                category=SignalCategory.COERCION,
                confidence=0.8,
                rationale="coercive wording",
            )
        ],
        analyzed_at=datetime.now(UTC),
    )
    assert "text" not in assessment.model_dump()
