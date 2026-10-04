# Staging gateway template

`nginx.conf.example` is a provider-neutral starting point for a short-lived,
synthetic-only staging demo. It is intentionally not a drop-in production
configuration. Replace the example domain, approved network ranges, upstream,
certificate paths, and exact browser origin after a security review.

Before enabling it:

1. Mount certificates and the `htpasswd` file as secret-manager volumes. Do not
   put them in Git, images, environment dumps, or support tickets.
2. Replace `192.0.2.0/24` with the smallest approved VPN/NAT range. Keep `deny all`.
3. Replace `https://demo.example.invalid` with the exact HTTPS UI origin, or leave
   the map empty when the demo is CLI-only. Never use `*` with credentials.
4. Point `risk_engine:8000` at a private service network and verify the backend
   port is not reachable from the public network.
5. Validate the configuration with `nginx -t`, then run the preflight checks in
   [`docs/allowlist-demo-deployment.md`](../../docs/allowlist-demo-deployment.md).

The gateway rate limit and concurrency limit are deliberately conservative demo
defaults. Tune them only with synthetic traffic and document the chosen values.
The gateway must not capture request bodies, response bodies, authorization
headers, cookies, or tracing payloads. At shutdown, revoke the staging credential,
remove the route and allow-list, stop the workload, and delete temporary logs and
volumes.
