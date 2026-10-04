# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [0.1.2] - 2026-10-04

### Fixed

- Include the FastAPI application package in source checkouts used by CI.
- Align package, API, and module version metadata at `0.1.2`.
- Add a reproducible synthetic-only privacy smoke test and allow-list deployment checklist.

## [0.1.1] - 2026-10-04

### Fixed

- Corrected the controlled demo example and aligned the bundled policy version.
- Redacted evaluator exception details from application logs.
- Added no-store and defensive response headers for the HTTP adapter.
- Documented privacy controls for allow-listed demonstrations.

## [0.1.0] - 2026-10-04

Initial public release.

### Added

- Deterministic, explainable rules for secrecy requests, trust manipulation,
  isolation, coercion, sexual escalation, and sextortion signals.
- Stable risk levels (`low`, `medium`, `high`, `critical`) and capped scores.
- Safe structured assessments containing signal identifiers, categories,
  explanations, and evidence counts without matched text excerpts.
- Python API via `risk_engine.analyze` and `RiskEngine.assess`.
- Optional FastAPI adapter with `/health` and `/v1/risk/evaluate` endpoints.
- Strict request validation, bounded inputs, generic error responses, and
  validated `X-Request-ID` propagation.
- Privacy, threat-model, safe-use, security, and contribution guidance.
- Non-root Docker image, Dependabot configuration, CI across Python 3.11–3.13,
  Ruff checks, tests, and dependency auditing.

### Safety boundaries

- The engine is a triage signal component, not a finding of abuse or a
  probability estimate.
- It does not retain content, contact people, moderate accounts, or make
  safeguarding, law-enforcement, clinical, or disciplinary decisions.
- Consequential use requires a trained human reviewer and an integrating
  product with appropriate legal, privacy, security, and safeguarding controls.

[0.1.0]: https://github.com/Lucioelpro22/child-safety-risk-engine/releases/tag/v0.1.0
[0.1.1]: https://github.com/Lucioelpro22/child-safety-risk-engine/releases/tag/v0.1.1
[0.1.2]: https://github.com/Lucioelpro22/child-safety-risk-engine/releases/tag/v0.1.2
