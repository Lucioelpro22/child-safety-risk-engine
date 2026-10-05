# Child Safety Risk Engine

[![CI](https://github.com/Lucioelpro22/child-safety-risk-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/Lucioelpro22/child-safety-risk-engine/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Version 0.1.4 · deterministic, explainable signals for child digital safety.

Deterministic, explainable Python rules for identifying safety signals in text that may involve grooming, coercion, isolation, secrecy requests, sexual escalation, or sextortion.

The package is intentionally a **signal and triage component**. It does not establish that abuse occurred, identify a perpetrator, make a clinical assessment, automatically moderate or remove content, contact authorities, or make decisions about a child. A trained human reviewer and the product's safeguarding process must make those decisions.

## Design goals

- Explainable output: every signal has a stable identifier, category, weight, explanation, and count.
- Deterministic behavior: no network calls, model calls, hidden state, or content retention.
- Privacy by default: assessments return counts and explanations, never matched message excerpts.
- Conservative integration: a score is a prioritization aid, not a probability of harm or a verdict.
- Small API: suitable for embedding in a service that owns authentication, authorization, retention, and case management.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,test]'
python -m pytest
```

```python
from risk_engine import analyze

assessment = analyze("Keep this secret. Don't tell your parents.")
print(assessment.as_dict())
```

The result contains `score`, `level`, `signals`, `explanation`, and `ruleset_version`. Do not log or persist the input text unless a separate, documented safeguarding process has a lawful basis, access controls, retention policy, and appropriate notice.

## HTTP API

The optional FastAPI adapter can be run locally after installing the project:

```bash
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Evaluate a synthetic message with a stable request ID:

```bash
curl -sS http://127.0.0.1:8000/v1/risk/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: 12345678-1234-5678-1234-567812345678' \
  -d '{"message":"Keep this secret. Do not tell your parents.","age_context":13}'
```

The response contains only structured signals and counts; it does not echo the submitted message:

```json
{
  "risk_score": 0.25,
  "risk_level": "medium",
  "signals": ["secrecy_request"],
  "policy_version": "2026.1",
  "request_id": "12345678-1234-5678-1234-567812345678"
}
```

Use `GET /health` for a liveness check. The API validates message length, age context, history size, and request IDs; callers still need to provide authentication, authorization, rate limiting, and retention controls.

The API accepts at most 99 history messages plus the current message (100
messages total). Each message is limited to 10,000 characters. The complete
text evaluated by the engine is limited to 100,000 characters, including one
newline separator between messages. Requests exceeding these limits receive
the generic HTTP 422 validation response before evaluation.

`constraints.txt` pins an audited dependency set. Pydantic requires an exact
`pydantic-core` version; update that pair together when regenerating constraints.
Dependabot ignores independent core updates to avoid incompatible installs.

## Integration guidance

The engine accepts a single string or an iterable of strings. The caller is responsible for:

1. Obtaining the necessary authority and consent for processing.
2. Minimizing, encrypting, and access-controlling any data before it reaches the engine.
3. Keeping identity, case management, reviewer notes, and evidence storage outside this package.
4. Presenting signal explanations and uncertainty to a trained reviewer.
5. Providing appeal, correction, escalation, and safeguarding procedures.

Scores and thresholds are a ruleset configuration, not validated prevalence estimates. Test them against representative, consented, de-identified data before using them operationally. Review false positives, false negatives, dialects, translations, and accessibility impacts with qualified safeguarding and legal experts.

## Repository layout

```text
src/risk_engine/       Core models and deterministic rules
app/                   Optional FastAPI adapter
tests/                 Unit and behavior tests
docs/threat-model.md   Security and privacy boundaries
docs/privacy.md        Data minimization and retention guidance
docs/operations.md     Demo/staging quickstart, preflight, rollback, and shutdown
```

## Docker

The image runs as an unprivileged user and executes a local smoke check:

```bash
docker build -t child-safety-risk-engine:0.1.4 .
docker run --rm child-safety-risk-engine:0.1.4
```

For an HTTP deployment, place the FastAPI adapter behind an authenticated gateway and apply the controls described in [docs/safe-use.md](docs/safe-use.md). A reviewed synthetic-only demonstration plan is documented in [docs/public-demo.md](docs/public-demo.md). For an allow-listed demo, use the operational [deployment checklist](docs/allowlist-demo-deployment.md).

An Nginx staging template is available under [`deploy/staging/`](deploy/staging/);
it contains placeholders only and requires a security review before use.

The operator runbook for local and private staging is [docs/operations.md](docs/operations.md).

## Security

Please read [SECURITY.md](SECURITY.md) before reporting a vulnerability. Never include real child data, intimate imagery, or identifiable conversation content in an issue or support request.

## License

MIT. See [LICENSE](LICENSE).
