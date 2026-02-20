# VO-031: Edge case in chat message persistence when input is empty

## User Story

Written and filed as **VO-026**. Here's the summary:

---

**VO-026: Edge case in chat message persistence when input is empty**

**Story:** As a user, I want empty/whitespace-only messages silently rejected without being saved, so my chat history stays clean.

**Key acceptance criteria:**
- Empty and whitespace-only inputs produce no API call, no DB write
- Silent no-op on submit — no error shown, input retains focus
- Backend returns `400` if empty payload reaches the endpoint directly (defensive guard)
- Unit tests cover empty, whitespace, and valid paths

**Priority:** Medium — low impact now, but data integrity risk grows with adoption. Clean it up before it scales.

**Complexity:** 1/5 — frontend trim check + one backend guard clause. No schema changes.
