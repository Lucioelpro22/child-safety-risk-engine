"""HTTP API for the child-safety risk engine.

The API deliberately returns structured, explainable risk signals without
echoing the submitted conversation.  Evaluation itself lives in the engine
module so it can also be used from batch jobs and other integrations.
"""

from __future__ import annotations

import importlib
import logging
import re
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from risk_engine.limits import (
    MAX_MESSAGE_CHARS,
    MAX_MESSAGES,
    MAX_TOTAL_CHARS,
    conversation_text_length,
)

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = MAX_MESSAGES - 1  # Reserve one slot for the current message.
MAX_HISTORY_TOTAL_CHARS = MAX_TOTAL_CHARS
MAX_TOTAL_TEXT_CHARS = MAX_TOTAL_CHARS
POLICY_VERSION = "2026.1"
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")


class RiskEvaluationRequest(BaseModel):
    """Input accepted by the public risk evaluation endpoint."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    age_context: int | None = Field(default=None, ge=0, le=17)
    age_band: str | None = Field(default=None, pattern=r"^(unknown|under_13|13_15|16_17)$")
    conversation_history: list[str] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must contain non-whitespace text")
        if _CONTROL_CHARS.search(value):
            raise ValueError("message contains unsupported control characters")
        if _EMAIL.search(value) or _PHONE.search(value):
            raise ValueError("message must be minimized before evaluation")
        return value

    @field_validator("conversation_history")
    @classmethod
    def history_items_must_be_bounded(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("conversation_history items must contain text")
        if any(len(item) > MAX_MESSAGE_CHARS for item in value):
            raise ValueError("conversation_history items are too long")
        if conversation_text_length(value) > MAX_HISTORY_TOTAL_CHARS:
            raise ValueError("conversation_history is too large")
        if any(_CONTROL_CHARS.search(item) for item in value):
            raise ValueError("conversation_history contains unsupported characters")
        if any(_EMAIL.search(item) or _PHONE.search(item) for item in value):
            raise ValueError("conversation_history must be minimized before evaluation")
        return value

    @model_validator(mode="after")
    def total_text_must_be_bounded(self) -> "RiskEvaluationRequest":
        """Apply the engine's bound to the exact text it will evaluate."""
        messages = [*self.conversation_history, self.message]
        if conversation_text_length(messages) > MAX_TOTAL_TEXT_CHARS:
            raise ValueError("message and conversation_history exceed the total text limit")
        return self

    @model_validator(mode="after")
    def age_band_matches_age(self) -> "RiskEvaluationRequest":
        if self.age_context is None:
            return self
        expected = "under_13" if self.age_context < 13 else "13_15" if self.age_context < 16 else "16_17"
        if self.age_band not in (None, "unknown", expected):
            raise ValueError("age_context and age_band are inconsistent")
        return self


class RiskEvaluationResponse(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str = Field(pattern="^(low|medium|high|critical)$")
    signals: list[str] = Field(default_factory=list, max_length=50)
    policy_version: str = POLICY_VERSION
    request_id: str


def _request_id(request: Request) -> str:
    candidate = request.headers.get("X-Request-ID", "")
    try:
        parsed = uuid.UUID(candidate)
        return str(parsed)
    except (ValueError, AttributeError):
        return str(uuid.uuid4())


def _load_evaluator() -> Callable[[dict[str, Any]], Any]:
    """Load the engine adapter without coupling the API to its implementation."""

    for module_name in ("app.risk_engine", "app.engine", "app.evaluator"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        for name in ("evaluate_risk", "evaluate", "score_message"):
            candidate = getattr(module, name, None)
            if callable(candidate):
                return candidate
    try:
        from risk_engine.engine import analyze
    except ImportError as exc:
        raise RuntimeError("risk evaluator is not configured") from exc

    def evaluate_with_rules(payload: dict[str, Any]) -> dict[str, Any]:
        history = payload.get("conversation_history") or []
        assessment = analyze([*history, payload["message"]])
        return {
            "risk_score": assessment.score,
            "risk_level": assessment.level.value,
            "signals": [signal.signal_id for signal in assessment.signals],
            "policy_version": assessment.ruleset_version,
        }

    return evaluate_with_rules


def _normalise_result(result: Any, request_id: str) -> RiskEvaluationResponse:
    if isinstance(result, RiskEvaluationResponse):
        return result.model_copy(update={"request_id": request_id})
    if not isinstance(result, dict):
        raise ValueError("evaluator returned an invalid result")
    return RiskEvaluationResponse(
        risk_score=float(result.get("risk_score", 0.0)),
        risk_level=str(result.get("risk_level", "low")),
        signals=[str(signal) for signal in result.get("signals", [])][:50],
        policy_version=str(result.get("policy_version", POLICY_VERSION)),
        request_id=request_id,
    )


def create_app(evaluator: Callable[[dict[str, Any]], Any] | None = None) -> FastAPI:
    app = FastAPI(title="Child Safety Risk Engine", version="0.1.4")
    selected_evaluator = evaluator

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any) -> JSONResponse:
        request.state.request_id = _request_id(request)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        # Triage metadata must not be cached or exposed to browser capabilities.
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {"code": "invalid_request", "message": "Request validation failed"},
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Do not include exception text or traceback in application logs: an
        # evaluator may receive sensitive material from an upstream service.
        # Detailed diagnostics belong in a separately access-controlled error
        # channel with explicit redaction.
        logger.error("risk evaluation request failed", extra={"request_id": request.state.request_id})
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "internal_error", "message": "Unable to evaluate request"},
                "request_id": request.state.request_id,
            },
        )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "child-safety-risk-engine"}

    @app.post("/v1/risk/evaluate", response_model=RiskEvaluationResponse, tags=["risk"])
    async def evaluate(payload: RiskEvaluationRequest, request: Request) -> RiskEvaluationResponse:
        fn = selected_evaluator or _load_evaluator()
        result = fn(payload.model_dump())
        if hasattr(result, "__await__"):
            result = await result
        return _normalise_result(result, request.state.request_id)

    return app


app = create_app()
