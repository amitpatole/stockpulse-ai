# VO-031: Edge case in chat message persistence when input is empty

## Technical Design

Here's the design spec for VO-026.

---

## VO-026 Technical Design Summary

**Root cause:** `chat.py:50` guards with `if not ticker or not question` — falsy checks pass `None` and `""` but let whitespace-only strings like `"   "` slip through to the AI provider. No chat message table exists yet, but the gap still burns tokens and will corrupt history if persistence is added.

**Approach:** Two-layer guard — frontend aborts silently before `fetch`, backend strips and rejects as a defensive fallback.

### Files

| File | Change |
|---|---|
| `backend/api/chat.py` | Apply `.strip()` to `question` and `ticker` at line 50 before the falsy check |
| `frontend/src/lib/api.ts` | Add `askChat()` with pre-flight `.trim()` guard; returns `null` (no `fetch`) on empty/whitespace |
| `backend/tests/test_chat_api.py` | New pytest file — 5 focused tests (empty, whitespace, valid paths) |

### Key decisions

- **No new API endpoint or schema change.** The fix is purely in the validation layer.
- **Silent no-op on frontend.** `askChat()` returns `null` rather than throwing — callers retain input focus, no error shown.
- **Backend still returns `400`** if whitespace reaches the endpoint directly (curl, other clients), satisfying the defensive guard acceptance criterion.
- **Frontend layer:** `askChat()` added to `api.ts` (no dedicated chat component exists yet), consistent with how every other resource is exposed through the API client.

Complexity lives up to the 1/5 estimate — two one-liners and a test file.
