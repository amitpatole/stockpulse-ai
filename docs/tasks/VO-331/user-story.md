# VO-331: Incorrect error handling in stock search autocomplete returns 500 instead of 400

## User Story

---

## User Story: VO-333 — Correct Error Handling in Stock Search Autocomplete

---

### User Story

**As a** trader using the stock search autocomplete,
**I want** to receive a clear `400 Bad Request` response when my search input is invalid,
**so that** I understand the problem is with my input — not a server failure — and can correct it without confusion.

---

### Context

The `/api/stocks/search` endpoint currently swallows validation/input errors and either silently returns `[]` or bubbles up an unhandled `500`. The `news.py` API (via `_parse_pagination`) already demonstrates the correct pattern: validate early, return explicit `400` with a message. The search endpoint needs to follow suit.

Relevant code: `backend/api/stocks.py:231-247`, `backend/core/stock_manager.py:147-188`

---

### Acceptance Criteria

- [ ] Requests with a missing or empty `q` parameter return `400` with a descriptive error message (not a silent `[]`)
- [ ] Requests with `q` exceeding a maximum length (e.g. 100 chars) return `400`
- [ ] Requests with obviously invalid characters (e.g. null bytes, control characters) return `400`
- [ ] Upstream/external failures (Yahoo Finance timeout, unexpected response) return `502` or `503`, **not** `500`
- [ ] All valid queries continue to behave as before — no regression
- [ ] Error responses follow the existing JSON shape: `{"error": "<message>"}`
- [ ] Unit tests cover each invalid input case

---

### Priority Reasoning

**High.** A `500` signals a server crash to clients and monitoring tools — it fires false alerts, erodes trust, and masks real outages. This is a correctness bug, not polish. The fix is low-risk and confined to one endpoint.

---

### Estimated Complexity

**2 / 5** — Input validation + status code correction in a single endpoint. The correct pattern already exists in `news.py`. No schema changes, no new dependencies.
