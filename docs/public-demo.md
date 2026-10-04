# Controlled public demo proposal

This document defines a safe, reproducible demonstration for
`child-safety-risk-engine`. It is a documentation and validation plan; it is
not authorization to deploy the API to the public internet.

## Demo scope

The demo exposes only the two existing HTTP routes:

| Route | Purpose | Expected use |
| --- | --- | --- |
| `GET /health` | Liveness check | Local smoke test or an authenticated gateway health probe |
| `POST /v1/risk/evaluate` | Return deterministic, explainable signals | Synthetic examples only |

The demo must run with authentication, rate limiting, TLS, access logs that
exclude request bodies, and a deletion policy supplied by the consuming
gateway. The API adapter itself does not provide user accounts, case
management, evidence storage, emergency escalation, or safeguarding decisions.

## Synthetic examples

Use neutral, invented text that contains no names, handles, addresses, phone
numbers, email addresses, images, or copied conversations. For example:

```bash
curl --fail-with-body --silent --show-error \
  http://127.0.0.1:8000/health
```

```bash
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8000/v1/risk/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: 12345678-1234-5678-1234-567812345678' \
  -d '{"message":"Keep this fictional exchange private from trusted adults.","age_context":13}'
```

Expected properties of the response:

```json
{
  "risk_score": 0.25,
  "risk_level": "medium",
  "signals": ["secrecy_request"],
  "policy_version": "2026.1",
  "request_id": "12345678-1234-5678-1234-567812345678"
}
```

The response must never contain the submitted text. A demo should show this
property explicitly by inspecting the response body, without displaying the
input in a hosted UI or telemetry stream.

## Boundaries and limits

- Keep the service bound to `127.0.0.1` for a local demo. A hosted demo needs
  an authenticated gateway and TLS termination before exposure.
- Send only synthetic, de-identified examples created for the demo. Never use
  real child data, intimate imagery, copied chats, or personal identifiers.
- Treat the score as a triage signal, not a probability, diagnosis, legal
  finding, accusation, or automated moderation decision.
- Keep a qualified human reviewer in the loop for any simulated high or
  critical result. Do not trigger reports, family contact, account actions, or
  emergency intervention from this endpoint alone.
- Keep request bodies out of application, proxy, analytics, and error logs.
- Enforce the input limits in the API and at the gateway. The current adapter
  bounds each message, history count, history aggregate, and total evaluation
  text. Reject oversized requests before forwarding them when possible.
- Apply a low request rate and a small concurrency limit for a public demo.
  Return a generic `429` from the gateway when the limit is reached.
- Delete demo request and response data after the shortest practical period;
  the preferred setting is no persistence.

## Validation checklist

Run this checklist before sharing a demo URL or recording a screen capture:

- [ ] The deployed revision is identified by an immutable commit or image
      digest and matches the reviewed source.
- [ ] `GET /health` succeeds, while the service port is unreachable from the
      public network unless a reviewed gateway is in front of it.
- [ ] The demo uses only the synthetic examples in this document or newly
      created equivalents.
- [ ] A valid UUID in `X-Request-ID` is preserved; an invalid value is replaced
      with a generated UUID and returned in the response header and body.
- [ ] Invalid JSON, unknown fields, blank text, PII-like text, control
      characters, inconsistent age bands, and oversized history return generic
      `422` errors without `detail` or submitted content.
- [ ] A failing evaluator returns a generic `500` response without exception
      text, request content, or secrets.
- [ ] The response contains structured signals and no message excerpts,
      identifiers, or participant metadata.
- [ ] Proxy, server, tracing, and analytics logs are checked for body and
      header leakage; sensitive request headers are redacted.
- [ ] TLS, authentication, authorization, rate limiting, CORS, and a deletion
      policy are verified at the gateway before any external access.
- [ ] The demo page states that the engine is experimental, deterministic, and
      assistive, and provides a responsible-use contact and shutdown procedure.
- [ ] The demo can be disabled quickly and its temporary data can be deleted.

## Recommended release gate

Publish a demo only after the full test suite, linting, container smoke test,
dependency audit, and this checklist pass. Keep the first demonstration local
or behind an allow-list; a public, unauthenticated endpoint is outside the
scope of this project.

