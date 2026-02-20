# VO-022: Missing input validation in alert system allows XSS

## Technical Design

Design spec is written. Here's a summary of what I documented:

---

**VO-022 Design: Two compounding gaps, defense in depth across three layers.**

**Root cause:**
1. `backend/core/stock_monitor.py` builds alert messages directly from raw external news titles — no sanitization before INSERT.
2. `frontend/src/app/research/page.tsx` passes AI-generated content through a naive markdown regex and straight into `dangerouslySetInnerHTML` — a live XSS sink.

The `ActivityFeed` text path is actually safe (React escapes JSX interpolation), but the research page is not.

**Files to touch (no schema or API shape changes):**

| File | Change |
|---|---|
| `backend/core/stock_monitor.py` | `sanitize_alert_text()` helper — strip HTML tags, reject event-handler and `javascript:` patterns before every `create_alert()` call |
| `backend/api/news.py` | `html.escape()` on all string fields in the alerts serializer — backstop for anything already stored |
| `frontend/src/app/research/page.tsx` | Escape raw content before the markdown transform, then DOMPurify before `dangerouslySetInnerHTML` |
| `backend/tests/test_alerts_xss.py` | New — parametrized payload suite plus legitimate-chars round-trip assertions |

**Key decisions:** stdlib `html` module on the backend (no new dependency); `dompurify` on the frontend (one new package, necessary because `dangerouslySetInnerHTML` can't be removed without reworking the markdown renderer). Output escaping at the API layer is a cheap but meaningful backstop for pre-existing stored data.
