"""Small deterministic rules engine; it deliberately does not call an LLM or take action."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from .limits import MAX_MESSAGE_CHARS, MAX_MESSAGES, MAX_TOTAL_CHARS
from .models import RiskAssessment, RiskLevel, RiskSignal

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    return "".join(c for c in value if not unicodedata.combining(c))


def _count_matches(text: str, patterns: Iterable[str]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


_RULES: tuple[tuple[str, str, float, str, tuple[str, ...]], ...] = (
    (
        "secrecy_request",
        "secrecy",
        0.25,
        "Requests to hide the interaction from a parent, guardian, or trusted adult.",
        (r"don['’]?t tell (?:your )?(?:parents?|mom|dad|guardian|anyone)", r"keep (?:this|it) secret", r"no one can know", r"no le cuentes a tus padres", r"mant(?:en|ene|enelo)lo en secreto"),
    ),
    (
        "trust_manipulation",
        "trust_manipulation",
        0.20,
        "Language that tries to replace trusted adults or create exclusive dependence.",
        (r"only trust me", r"you can trust me more than", r"we have a special secret", r"you are mature for your age"),
    ),
    (
        "isolation",
        "isolation",
        0.20,
        "Attempts to isolate the young person from family, friends, or safety support.",
        (r"dont talk to (?:your )?(?:parents?|friends?|family)", r"stay away from", r"just you and me", r"leave your (?:friends?|family)"),
    ),
    (
        "coercion",
        "coercion",
        0.35,
        "Threats, pressure, or consequences used to force compliance.",
        (r"if you (?:dont|do not) .* i(?:'ll| will)", r"do it or else", r"i will hurt", r"nobody will believe you"),
    ),
    (
        "sexual_escalation",
        "sexual_escalation",
        0.40,
        "Requests or pressure to move a conversation toward sexual content or imagery.",
        (r"send (?:me )?(?:a |the )?(?:nude|naked|intimate)", r"show me your body", r"turn on your camera", r"take off your clothes", r"sexual (?:photo|picture)"),
    ),
    (
        "sextortion",
        "sextortion",
        0.60,
        "Threats to publish, share, or use intimate material to obtain compliance.",
        (r"unless you pay", r"i(?:'ll| will) send (?:it|them) to", r"everyone will see", r"i(?:'ll| will) post (?:it|them) online"),
    ),
)


class RiskEngine:
    """Evaluate one message or an iterable of messages without retaining content."""

    def assess(self, text: str | Iterable[str]) -> RiskAssessment:
        if isinstance(text, str):
            if len(text) > MAX_MESSAGE_CHARS:
                raise ValueError("message is too long")
            content = text
        elif isinstance(text, Iterable):
            parts: list[str] = []
            total_chars = 0
            for part in text:
                if not isinstance(part, str):
                    raise TypeError("text iterable must contain strings")
                if len(parts) >= MAX_MESSAGES:
                    raise ValueError("text contains too many messages")
                if len(part) > MAX_MESSAGE_CHARS:
                    raise ValueError("message is too long")
                # Bound the text actually evaluated, including separators.
                total_chars += len(part) + bool(parts)
                if total_chars > MAX_TOTAL_CHARS:
                    raise ValueError("text is too large")
                parts.append(part)
            content = "\n".join(parts)
        else:
            raise TypeError("text must be a string or iterable of strings")
        if not isinstance(content, str):
            raise TypeError("text must be a string or iterable of strings")
        if len(content) > MAX_TOTAL_CHARS:
            raise ValueError("text is too large")
        if _CONTROL_CHARS.search(content):
            raise ValueError("text contains unsupported control characters")
        if _EMAIL.search(content) or _PHONE.search(content):
            raise ValueError("text must be minimized before evaluation")
        folded = _fold(content)
        signals: list[RiskSignal] = []
        raw_score = 0.0
        for signal_id, category, weight, explanation, patterns in _RULES:
            count = _count_matches(folded, patterns)
            if count:
                contribution = min(weight, weight * (0.5 + 0.5 * min(count, 2)))
                raw_score += contribution
                signals.append(RiskSignal(signal_id, category, round(contribution, 4), explanation, count))
        # Multiple independent categories increase confidence, while capping output at 1.
        score = round(min(1.0, raw_score), 4)
        if score >= 0.75:
            level = RiskLevel.CRITICAL
        elif score >= 0.50:
            level = RiskLevel.HIGH
        elif score >= 0.25:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        if signals:
            explanation = "Detected " + ", ".join(s.signal_id for s in signals) + ". Human review is recommended."
        else:
            explanation = "No configured risk signals were detected; this is not proof of safety."
        return RiskAssessment(score, level, tuple(signals), explanation)


def analyze(text: str | Iterable[str]) -> RiskAssessment:
    return RiskEngine().assess(text)
