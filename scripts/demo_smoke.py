#!/usr/bin/env python3
"""Run the local v0.1.3 demo contract with synthetic input only.

This script uses FastAPI's in-process client, so it does not bind a port or
send data over the network. It is suitable for a release smoke check before a
demo is placed behind an authenticated gateway.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from app.api import app, create_app  # noqa: E402


def check(condition: bool, name: str) -> None:
    if not condition:
        raise RuntimeError(f"smoke check failed: {name}")
    print(f"PASS: {name}")


def main() -> int:
    client = TestClient(app, raise_server_exceptions=False)

    health = client.get("/health")
    check(health.status_code == 200, "health endpoint")
    check(health.headers.get("cache-control") == "no-store", "no-store response policy")
    check(health.headers.get("x-content-type-options") == "nosniff", "content type protection")
    check(health.headers.get("referrer-policy") == "no-referrer", "referrer protection")

    synthetic_message = "Keep this secret from trusted adults."
    evaluation = client.post(
        "/v1/risk/evaluate",
        headers={"X-Request-ID": "12345678-1234-5678-1234-567812345678"},
        json={"message": synthetic_message, "age_context": 13},
    )
    check(evaluation.status_code == 200, "synthetic evaluation")
    check(evaluation.json().get("signals") == ["secrecy_request"], "expected signal")
    check(synthetic_message not in evaluation.text, "response does not echo input")

    invalid = client.post(
        "/v1/risk/evaluate",
        json={"message": "", "unexpected": "synthetic-private-value"},
    )
    check(invalid.status_code == 422, "generic validation error")
    check("synthetic-private-value" not in invalid.text, "validation error does not echo input")

    failing = TestClient(
        create_app(lambda payload: (_ for _ in ()).throw(RuntimeError("synthetic evaluator failure"))),
        raise_server_exceptions=False,
    )
    internal = failing.post("/v1/risk/evaluate", json={"message": "synthetic failure input"})
    check(internal.status_code == 500, "generic internal error")
    check("synthetic evaluator failure" not in internal.text, "internal error hides exception")
    check("synthetic failure input" not in internal.text, "internal error hides input")

    print("Demo smoke test passed (synthetic data only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
