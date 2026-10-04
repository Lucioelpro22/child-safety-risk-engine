# Security policy

## Scope

This repository contains a local, deterministic text-signal library. It has no authentication layer, network listener, database, telemetry, or external model. Deploying it inside a product introduces additional security responsibilities for that product.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository when available. If it is unavailable, contact the maintainer through a private channel listed on the repository profile. Do not open a public issue for a security report.

Do not send real child data, names, contact details, intimate imagery, credentials, or raw conversation transcripts. A useful report includes the affected version, a minimal synthetic reproduction, impact, and a proposed mitigation.

## Supported versions

Security fixes target the latest release on the default branch. Pin a released version in applications and review dependency and ruleset changes before upgrading.

## Safe deployment requirements

The integrating application should provide:

- strict authentication and least-privilege authorization;
- encryption in transit and at rest;
- tenant isolation and reviewer access logging;
- input size, encoding, and resource limits;
- redaction and data minimization before logs or traces;
- documented retention and deletion workflows;
- abuse monitoring and an incident response plan;
- human safeguarding review for every consequential action.

The engine's score must never be used as the sole basis for an automated accusation, account action, child contact, law-enforcement report, or clinical decision.
