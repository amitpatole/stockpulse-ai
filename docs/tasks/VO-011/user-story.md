# VO-011: Add pagination to news and research list endpoints

## User Story

User story written to `docs/tasks/VO-003/user-story.md`. Here's the summary:

---

**VO-003: Add pagination to news and research list endpoints**

**Story:** As a frontend developer consuming the news and research APIs, I want `GET /api/news` and `GET /api/research/briefs` to support `page` and `page_size` query parameters, so that the UI can load data incrementally and avoid stalling on large payloads as the database grows.

**Key acceptance criteria:**
- Both endpoints accept `page` (default: 1) and `page_size` (default: 25, max: 100)
- Response wraps results: `{ data, page, page_size, total }` — `total` is filter-scoped
- Invalid params → HTTP 400; oversized `page_size` → silently clamped to 100
- SQL uses bound `LIMIT ? OFFSET ?` — no string interpolation
- Existing hardcoded `LIMIT 50`/`LIMIT 100` in `news.py` eliminated; `research.py`'s `limit` param retired

**Priority: P2 — Medium.** Not blocking today, but a prerequisite for any "load more" UX and a ticking time bomb as rows accumulate.

**Complexity: 2/5.** Mechanical SQL change + input validation. No schema migrations needed.
