from uuid import UUID

from fastapi.testclient import TestClient

from app.api import app, create_app


def evaluator(payload: dict) -> dict:
    return {"risk_score": 0.87, "risk_level": "high", "signals": ["secrecy_request"]}


client = TestClient(create_app(evaluator))


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_evaluate_returns_safe_structured_response() -> None:
    request_id = "12345678-1234-5678-1234-567812345678"
    response = client.post(
        "/v1/risk/evaluate",
        headers={"X-Request-ID": request_id},
        json={"message": "don't tell your parents", "age_context": 13},
    )
    assert response.status_code == 200
    assert response.json() == {
        "risk_score": 0.87,
        "risk_level": "high",
        "signals": ["secrecy_request"],
            "policy_version": "2026.1",
        "request_id": request_id,
    }
    assert "message" not in response.text


def test_invalid_request_has_generic_error() -> None:
    response = client.post("/v1/risk/evaluate", json={"message": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert "detail" not in response.json()


def test_evaluator_errors_are_not_leaked(caplog) -> None:
    secret = "internal secret payload"
    failing = TestClient(
        create_app(lambda payload: (_ for _ in ()).throw(RuntimeError(secret))),
        raise_server_exceptions=False,
    )
    response = failing.post("/v1/risk/evaluate", json={"message": "hello"})
    assert response.status_code == 500
    assert response.json()["error"]["message"] == "Unable to evaluate request"
    assert secret not in response.text
    assert secret not in caplog.text


def test_api_rejects_pii_and_aggregate_history_over_limit() -> None:
    response = client.post("/v1/risk/evaluate", json={"message": "email me at child@example.com"})
    assert response.status_code == 422
    assert "child@example.com" not in response.text

    response = client.post(
        "/v1/risk/evaluate",
        json={"message": "hello", "conversation_history": ["x" * 10_000] * 11},
    )
    assert response.status_code == 422
    assert "conversation_history" not in response.text


def test_api_requires_consistent_age_band() -> None:
    response = client.post(
        "/v1/risk/evaluate",
        json={"message": "hello", "age_context": 12, "age_band": "13_15"},
    )
    assert response.status_code == 422


def test_unknown_fields_are_rejected_without_detail_leak() -> None:
    response = client.post(
        "/v1/risk/evaluate",
        json={"message": "hello", "unexpected": "sensitive-value"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert "sensitive-value" not in response.text
    assert "detail" not in response.json()


def test_total_text_limit_bounds_message_plus_history() -> None:
    # The individual history limit is 100,000 characters.  The aggregate
    # limit must still account for the current message to bound engine work.
    response = client.post(
        "/v1/risk/evaluate",
        json={"message": "x", "conversation_history": ["a" * 1_000] * 100},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_malformed_request_id_is_replaced_and_returned() -> None:
    response = client.post(
        "/v1/risk/evaluate",
        headers={"X-Request-ID": "attacker-controlled-id"},
        json={"message": "hello"},
    )
    assert response.status_code == 200
    generated = response.json()["request_id"]
    assert UUID(generated)
    assert response.headers["x-request-id"] == generated
    assert generated != "attacker-controlled-id"


def test_default_app_uses_bundled_rules_engine() -> None:
    response = TestClient(app).post(
        "/v1/risk/evaluate",
        json={"message": "don't tell your parents"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "medium"
    assert body["signals"] == ["secrecy_request"]
    assert body["policy_version"] == "2026.1"
