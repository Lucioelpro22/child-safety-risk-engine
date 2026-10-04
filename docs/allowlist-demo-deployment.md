# Controlled demo deployment checklist

This checklist applies to a short-lived demonstration behind an authenticated
gateway and an explicit network allow-list. It is not a production deployment
design and does not authorize exposing the application directly to the internet.

## Gateway and network

- [ ] Bind the application to a private interface or internal container network.
- [ ] Allow only named source IPs, VPN identities, or an approved private network.
- [ ] Deny all other ingress and verify the service port is unreachable externally.
- [ ] Terminate TLS at the gateway with a valid certificate and modern protocols.
- [ ] Configure a short, documented expiry for the demo and an owner responsible
      for disabling it.
- [ ] Keep a tested disable action: revoke the gateway route, remove the allow-list,
      and stop the workload. Confirm it takes effect within minutes.

## Authentication and authorization

- [ ] Require authentication at the gateway even when the source is allow-listed.
- [ ] Prefer short-lived, individually assigned credentials or mTLS identities.
- [ ] Give demo identities access only to `GET /health` and
      `POST /v1/risk/evaluate`.
- [ ] Do not accept credentials in query parameters; redact authorization headers
      from all logs and traces.
- [ ] Revoke credentials at the end of the demo and after any suspected leak.
- [ ] Keep the engine's score behind a human-reviewed demo flow; do not connect it
      to account actions, notifications, reports, or emergency escalation.

## CORS and browser access

- [ ] Disable CORS when the demo is driven by a command-line client or server-side
      tool.
- [ ] If a browser UI is required, allow only its exact HTTPS origin(s), with no
      wildcard origin and no wildcard headers.
- [ ] Enable credentials only when the gateway uses an explicit origin allow-list
      and a deliberate session design. Never combine credentials with `*`.
- [ ] Allow only `POST` and the minimum headers required, such as `Content-Type`
      and `X-Request-ID`; do not expose authorization headers unnecessarily.

## Rate, size, and availability controls

- [ ] Apply a low rate limit per source identity and per source IP at the gateway.
- [ ] Apply a small concurrency limit and an upstream timeout.
- [ ] Reject oversized bodies at the gateway before forwarding them.
- [ ] Return a generic `429` or `413` without echoing request content or backend
      diagnostics.
- [ ] Keep application limits enabled: 10,000 characters per message, 100 history
      items, 100,000 history characters, and 100,000 total evaluation characters.
- [ ] Do not retry evaluation requests automatically unless the client has a safe,
      bounded retry policy.

## Headers, logs, and telemetry

- [ ] Verify responses include `Cache-Control: no-store`, `Pragma: no-cache`,
      `X-Content-Type-Options: nosniff`, and `Referrer-Policy: no-referrer`.
- [ ] Keep request bodies, response bodies, query strings, and raw conversation text
      out of gateway, application, tracing, analytics, and crash logs.
- [ ] Redact authorization, cookies, tokens, and any user-supplied request ID.
- [ ] Log only operational metadata: timestamp, route, status, latency, byte count,
      and a generated correlation ID. Restrict access and set a short expiry.
- [ ] Confirm exception handling emits generic client errors and does not log
      exception text that could contain submitted content.
- [ ] Disable request sampling and payload capture in APM tools for these routes.

## Data and retention

- [ ] Use only synthetic, invented examples. Never use real child data, copied chats,
      intimate imagery, names, handles, addresses, phone numbers, or email addresses.
- [ ] Keep persistence disabled for the demo where possible.
- [ ] If temporary operational logs are unavoidable, document their owner, purpose,
      access list, deletion deadline, and deletion evidence before launch.
- [ ] Delete temporary logs, caches, traces, exported results, and container volumes
      when the demo ends.
- [ ] Verify no request or response data is stored by the gateway, CDN, browser UI,
      object storage, or error tracker.

## Preflight and shutdown

- [ ] Run the full tests, lint, dependency audit, and container smoke test.
- [ ] Test a valid synthetic request and confirm the response contains no message
      excerpt or participant metadata.
- [ ] Test invalid JSON, PII-like input, oversized input, invalid credentials,
      disallowed origin, rate-limit exhaustion, and gateway timeout.
- [ ] Record the immutable image or commit used for the demo.
- [ ] Assign a shutdown time and an operator. At shutdown, revoke credentials,
      remove the route and allow-list, stop the workload, and delete temporary data.
- [ ] Recheck the public network after shutdown and retain only the minimal audit
      record needed to show that the demo was disabled.
