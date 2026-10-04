# Contributing

Thank you for improving this defensive, open-source project.

## Before opening a change

- Read the README, SECURITY.md, and [the threat model](docs/threat-model.md).
- Use synthetic examples only. Never commit real child data or identifiable conversations.
- Explain the safety rationale, expected false positives and false negatives, and any localization impact.
- Keep behavior deterministic and explainable. New rules require stable identifiers and human-readable explanations.
- Do not add network access, telemetry, model calls, or content persistence without a separate design review.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest
ruff check .
```

Changes should include focused tests and documentation. Avoid tests that merely duplicate implementation details. Reviewers may request evidence that a rule does not expose matched content or create an automated enforcement path.

## Pull requests

Describe the user-safety problem, the changed behavior, the privacy impact, and validation performed. Maintainers may reject changes that increase surveillance, enable discrimination, or imply certainty the engine cannot support.
