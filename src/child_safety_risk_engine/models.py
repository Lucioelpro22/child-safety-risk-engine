"""Input and output contracts for the risk engine.

Models deliberately accept opaque pseudonymous identifiers only.  They never
model names, email addresses, phone numbers, locations, or other direct
identifiers, and serialized output excludes the original message by default.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")


class RiskLevel(StrEnum):
    """Stable, human-readable risk bands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalCategory(StrEnum):
    """Explainable behavioral categories; these are not demographic labels."""

    SECRECY_REQUEST = "secrecy_request"
    TRUST_MANIPULATION = "trust_manipulation"
    AGE_BOUNDARY_TESTING = "age_boundary_testing"
    SEXUALIZATION = "sexualization"
    COERCION = "coercion"
    SEXTORTION = "sextortion"
    MIGRATION_OFF_PLATFORM = "migration_off_platform"
    MEETING_REQUEST = "meeting_request"
    THREAT = "threat"
    UNKNOWN = "unknown"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class AgeContext(_StrictModel):
    """Minimal age context; use an age band where exact age is unnecessary."""

    age_years: int | None = Field(default=None, ge=0, le=17)
    age_band: str | None = Field(default=None, pattern=r"^(unknown|under_13|13_15|16_17)$")
    consent_basis: str = Field(
        default="user_provided", pattern=r"^(user_provided|guardian|unknown)$"
    )

    @classmethod
    def _validate_consistency(cls, values: dict) -> dict:
        age = values.get("age_years")
        band = values.get("age_band")
        if age is None and band is None:
            values["age_band"] = "unknown"
        if age is not None and band is not None and band != "unknown":
            expected = "under_13" if age < 13 else "13_15" if age < 16 else "16_17"
            if band != expected:
                raise ValueError("age_years and age_band are inconsistent")
        return values

    from pydantic import model_validator

    _validate_consistency = model_validator(mode="after")(
        lambda self: self if self.age_years is None or self.age_band in (None, "unknown") or (
            self.age_band
            == (
                "under_13"
                if self.age_years < 13
                else "13_15"
                if self.age_years < 16
                else "16_17"
            )
        ) else (_ for _ in ()).throw(ValueError("age_years and age_band are inconsistent"))
    )


class MessageInput(_StrictModel):
    """A message to analyze, carrying only pseudonymous participant IDs."""

    message_id: UUID
    sender_ref: Annotated[str, Field(min_length=8, max_length=128)]
    recipient_ref: Annotated[str, Field(min_length=8, max_length=128)]
    text: Annotated[str, Field(min_length=1, max_length=20_000)]
    age_context: AgeContext = Field(default_factory=AgeContext)
    observed_at: datetime | None = None

    @field_validator("sender_ref", "recipient_ref")
    @classmethod
    def opaque_reference_only(cls, value: str) -> str:
        if not _OPAQUE_ID.fullmatch(value) or _EMAIL.search(value) or _PHONE.search(value):
            raise ValueError("participant references must be opaque pseudonymous IDs")
        return value

    @field_validator("text")
    @classmethod
    def safe_text(cls, value: str) -> str:
        if _CONTROL_CHARS.search(value):
            raise ValueError("message contains unsupported control characters")
        return value


class Signal(_StrictModel):
    """A transparent signal emitted by a detector, without message contents."""

    category: SignalCategory
    confidence: float = Field(ge=0, le=1)
    evidence_span: tuple[int, int] | None = None
    rationale: Annotated[str, Field(min_length=1, max_length=500)]

    @field_validator("evidence_span")
    @classmethod
    def valid_span(cls, value: tuple[int, int] | None) -> tuple[int, int] | None:
        if value is not None and (value[0] < 0 or value[1] <= value[0]):
            raise ValueError("evidence_span must be a non-empty, non-negative range")
        return value


class RiskScore(_StrictModel):
    """Normalized score and band; score is bounded to prevent ambiguous output."""

    value: float = Field(ge=0, le=1)
    level: RiskLevel
    model_version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]


class RiskAssessment(_StrictModel):
    """Privacy-minimized assessment returned to callers."""

    assessment_id: UUID
    message_id: UUID
    score: RiskScore
    signals: list[Signal] = Field(default_factory=list, max_length=50)
    analyzed_at: datetime
    retention_expires_at: datetime | None = None
    contains_sensitive_content: bool = True

    @field_validator("retention_expires_at")
    @classmethod
    def retention_is_future(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("retention_expires_at must include timezone information")
        return value
