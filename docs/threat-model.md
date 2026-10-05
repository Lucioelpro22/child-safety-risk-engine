# Threat model

## System boundary

The engine is a pure in-process library. It receives text from a caller, normalizes and evaluates it against a fixed ruleset, and returns an assessment containing aggregate signal metadata. It does not store input, send it over the network, or perform an external action.

The caller and surrounding product remain responsible for identity, authorization, transport, storage, review queues, notifications, and case handling.

## Assets

- Children's and families' privacy and safety.
- Conversation content and identifiers held by an integrating product.
- Reviewer decisions and safeguarding case records.
- Ruleset integrity and release provenance.
- Availability of the review pipeline.

## Threats and controls

| Threat | Control in this repository | Required control in the integrating product |
|---|---|---|
| Sensitive text appears in logs | Core output contains no excerpts | Redact inputs, traces, exceptions, and request bodies |
| Unauthorized access to cases | No case storage or access layer exists | Enforce authentication, RBAC, tenant isolation, and audit logs |
| Overreliance on a score | Explanations state that human review is required | Require trained review and prohibit sole reliance for consequential action |
| False positives or negatives | Stable, inspectable rules and tests | Validate on representative data and monitor error patterns |
| Ruleset tampering | Versioned source and CI checks | Pin releases, review changes, protect branches, verify provenance |
| Resource exhaustion | API/library enforce 10,000-character messages, 100 messages including the current message, and 100,000 total characters including newline separators; iterables are consumed incrementally | Apply request body, timeout, concurrency, and queue limits |
| Data retention beyond purpose | Library has no retention mechanism | Define lawful basis, minimization, retention, deletion, and access review |
| Malicious input or regex abuse | Rules are reviewed and tested | Add fuzzing/resource tests before accepting untrusted high-volume input |

## Abuse cases

This component could be misused for mass surveillance, discriminatory profiling, automated punishment, or exposing private conversation content. Product owners must limit collection to a defined safeguarding purpose, document access, provide correction and appeal routes, and conduct an impact review before deployment.

## Residual risk

Language is contextual, multilingual, evolving, and ambiguous. A match is a signal, not proof; absence of a match is not proof of safety. The package cannot determine age, intent, relationship, consent, imminent danger, or legal status. Human safeguarding expertise remains necessary.
