# VO-382: Missing input validation in data provider fallback chain allows injection

## User Story

# User Story: VO-XXX — Input Validation in Data Provider Fallback Chain

---

## User Story

**As a** system administrator configuring data provider fallback chains,
**I want** all provider configuration inputs to be strictly validated before they are processed,
**so that** malicious or malformed input cannot inject unintended behavior into the fallback chain execution.

---

## Acceptance Criteria

- [ ] All data provider identifiers (names, URLs, API keys) are validated against an allowlist/schema before being stored or evaluated
- [ ] Fallback chain ordering inputs are type-checked and range-bounded; non-integer or out-of-range values are rejected with a clear error
- [ ] Any input that fails validation returns a 400-level HTTP error with a descriptive (but non-leaking) message — no silent failure or partial processing
- [ ] Injected payloads (shell metacharacters, SQL fragments, path traversal sequences) are rejected at the validation layer, never reaching business logic
- [ ] Existing valid configurations continue to function without regression
- [ ] Unit tests cover: valid input passes, each invalid input class is rejected, boundary values behave correctly
- [ ] No secrets or stack traces are exposed in validation error responses

---

## Priority Reasoning

**Priority: High**

This is a security defect, not a feature gap. Injection vulnerabilities in a data pipeline component can corrupt market data, exfiltrate credentials, or destabilize the fallback chain during live trading. The blast radius extends to any downstream consumer relying on provider output. Ship the fix before the next release cut.

---

## Estimated Complexity

**3 / 5**

Validation logic itself is straightforward. The complexity comes from auditing every ingestion point in the fallback chain, ensuring consistent enforcement across HTTP handlers and internal callers, and writing thorough negative-path tests without breaking existing provider configs.
