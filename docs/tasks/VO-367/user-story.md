# VO-367: Missing input validation in SSE event streaming allows injection

## User Story

## User Story: VO-350 — SSE Event Streaming Input Validation

---

**User Story**

As a **platform user receiving real-time market data via SSE**, I want **all SSE event payloads to be validated and sanitized before streaming**, so that **malicious data from external sources cannot inject rogue events or corrupt the SSE stream for other users**.

---

**Acceptance Criteria**

- [ ] All fields written into SSE `data:` payloads are validated against an allowlist of expected types/formats before emission
- [ ] Newline characters (`\n`, `\r`) in string fields are stripped or rejected — these break SSE framing and can inject fake events
- [ ] SSE `event:` and `id:` fields are restricted to alphanumeric + hyphens only
- [ ] Malformed or oversized payloads are dropped with a server-side error log — never forwarded to clients
- [ ] JSON serialization is the only accepted encoding path; raw string interpolation into SSE fields is prohibited
- [ ] Existing SSE functionality (price alerts, scheduler events) remains fully operational
- [ ] Unit tests cover: clean payload passthrough, newline injection attempt, oversized field, invalid event name

---

**Priority Reasoning**

**High.** SSE injection can let an attacker spoof price alerts or system events to other connected users — a direct trust and integrity risk on a financial platform. This is a low-effort attack vector with meaningful blast radius. Ship before the next public release.

---

**Estimated Complexity**

**2 / 5** — Defensive input layer at a single emission point (`send_sse_event`). No schema changes, no new infrastructure. Mostly string validation + tests.
