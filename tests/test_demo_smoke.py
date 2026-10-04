"""Release smoke test for the local, synthetic-only demo contract."""

import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import app, create_app
from risk_engine import __version__


def test_package_version_matches_distribution_metadata() -> None:
    assert __version__ == "0.1.2"
    metadata = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert metadata["project"]["version"] == __version__


def test_local_demo_contract_is_private_and_generic() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "child-safety-risk-engine"}
    assert health.headers["cache-control"] == "no-store"
    assert health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["referrer-policy"] == "no-referrer"
    assert health.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"

    synthetic_message = "Keep this secret from trusted adults."
    evaluation = client.post(
        "/v1/risk/evaluate",
        headers={"X-Request-ID": "12345678-1234-5678-1234-567812345678"},
        json={"message": synthetic_message, "age_context": 13},
    )
    assert evaluation.status_code == 200
    assert evaluation.json()["signals"] == ["secrecy_request"]
    assert evaluation.json()["request_id"] == "12345678-1234-5678-1234-567812345678"
    assert synthetic_message not in evaluation.text

    invalid = client.post(
        "/v1/risk/evaluate",
        json={"message": "", "unexpected": "synthetic-private-value"},
    )
    assert invalid.status_code == 422
    assert invalid.json() == {
        "error": {"code": "invalid_request", "message": "Request validation failed"},
        "request_id": invalid.headers["x-request-id"],
    }
    assert "synthetic-private-value" not in invalid.text

    failing = TestClient(
        create_app(lambda payload: (_ for _ in ()).throw(RuntimeError("synthetic evaluator failure"))),
        raise_server_exceptions=False,
    )
    internal = failing.post("/v1/risk/evaluate", json={"message": "synthetic failure input"})
    assert internal.status_code == 500
    assert internal.json()["error"] == {
        "code": "internal_error",
        "message": "Unable to evaluate request",
    }
    assert "synthetic evaluator failure" not in internal.text
    assert "synthetic failure input" not in internal.text
