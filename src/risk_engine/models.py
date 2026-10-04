from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class RiskSignal:
    """A rule match with safe, non-content-bearing evidence."""

    signal_id: str
    category: str
    score: float
    explanation: str
    evidence_count: int


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    score: float
    level: RiskLevel
    signals: tuple[RiskSignal, ...]
    explanation: str
    ruleset_version: str = "2026.1"

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level.value,
            "signals": [
                {
                    "signal_id": s.signal_id,
                    "category": s.category,
                    "score": s.score,
                    "explanation": s.explanation,
                    "evidence_count": s.evidence_count,
                }
                for s in self.signals
            ],
            "explanation": self.explanation,
            "ruleset_version": self.ruleset_version,
        }
