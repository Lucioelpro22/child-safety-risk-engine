# Demo and staging operations

This runbook is for a short-lived local or private staging demonstration. It
does not authorize public exposure. The service produces assistive signals for
human review; it does not make clinical, legal, safeguarding, emergency, or
automated moderation decisions.

## Quickstart (local only)

Use a clean checkout and synthetic examples only:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,test]'
python -m pytest -q
ruff check .
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

In another terminal, verify liveness and evaluate one invented message:

```bash
curl --fail-with-body --silent --show-error http://127.0.0.1:8000/health
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8000/v1/risk/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: 12345678-1234-5678-1234-567812345678' \
  -d '{"message":"Keep this secret. Do not tell your parents.","age_context":13}'
```

For a container smoke test:

```bash
docker build -t child-safety-risk-engine:staging .
docker run --rm --name child-safety-risk-engine-staging \
  -p 127.0.0.1:8000:8000 child-safety-risk-engine:staging
```

The container must remain bound to loopback for a local demo. A private staging
deployment requires an authenticated gateway, TLS, an allow-list, rate limits,
and the controls in [allowlist-demo-deployment.md](allowlist-demo-deployment.md).

## Preflight

Before sharing a staging URL or recording a demo, confirm all of the following:

- The reviewed commit or immutable image digest is recorded.
- The full tests, Ruff, dependency audit, and container build pass.
- Only synthetic, invented text is used; no names, handles, identifiers, copied
  conversations, images, or real minor data are present.
- The gateway requires authentication and an explicit allow-list; the service
  is not directly reachable from the public internet.
- Request bodies, response bodies, authorization headers, and raw exceptions
  are excluded from logs, traces, analytics, and crash reports.
- The response contains signal metadata only and does not echo the input.
- A trained human reviewer owns any simulated high or critical result.
- An operator, expiry time, disable procedure, and deletion deadline are recorded.

The API limits one message to 10,000 characters, history to 100 items, history
to 100,000 characters, and total evaluation text to 100,000 characters. Enforce
equal or smaller limits at the gateway and reject oversized bodies before
forwarding them.

## Synthetic test set

Use short, invented examples such as these. They are test fixtures, not evidence
or ground truth:

```text
No le cuentes a nadie; esto queda entre nosotros.
How was school today?
```

Do not add real names, contact information, locations, dates of birth, intimate
material, or copied conversations to examples, screenshots, issues, or logs.

## Rollback and shutdown

If the demo behaves unexpectedly or sensitive data may have been submitted:

1. Revoke demo credentials and disable the gateway route immediately.
2. Remove the network allow-list entry and stop the workload.
3. Preserve only minimal operational metadata needed for incident handling;
   do not copy or circulate request bodies.
4. Delete temporary logs, traces, caches, browser storage, exports, and volumes
   according to the documented deletion deadline.
5. If the image or code is suspect, redeploy the last reviewed immutable image or
   commit after tests and dependency checks pass. Do not roll forward blindly.
6. Recheck the public network and gateway from an independent client.
7. Record the shutdown time, owner, affected revision, and remediation without
   recording conversation content.

For a local container, use:

```bash
docker stop child-safety-risk-engine-staging
docker rm child-safety-risk-engine-staging
```

Do not connect this demo endpoint to account actions, notifications, family or
law-enforcement contact, emergency escalation, clinical workflows, or automated
content removal. Those require separate governance, qualified review, and a
purpose-built system design.
