# Privacy guidance

The engine is designed to process the minimum information needed to produce a signal assessment. It does not retain input or emit matched excerpts.

The reference API enforces these limits before evaluation: one message up to 10,000
characters, at most 100 history items, and at most 100,000 history characters in
total. The library applies the same bounds to strings and iterables and consumes
iterables incrementally, so an unbounded generator cannot be materialized in memory.
Requests containing an email address, phone number, or unsupported control character
are rejected for minimization. Integrators should pseudonymize participant references
and remove other direct identifiers before calling the engine.

Integrators should establish and document:

- purpose and lawful basis for processing;
- age-appropriate notice and, where required, consent;
- the minimum fields and retention period;
- encryption, access controls, tenant boundaries, and reviewer audit logs;
- deletion, correction, export, and incident response procedures;
- cross-border transfer and vendor rules;
- a human review and safeguarding escalation process.

Do not place raw text, names, usernames, phone numbers, locations, images, or credentials in logs, metrics, crash reports, fixtures, pull requests, or support tickets. Use generated synthetic text in development and de-identified data for evaluation. A score must not become a permanent label attached to a child or be used as the sole basis for an adverse decision.

Age information should use the coarsest useful band (`under_13`, `13_15`, or
`16_17`). Exact ages are accepted only for compatibility and are checked against any
provided band; age is contextual metadata and is never a risk signal by itself.
