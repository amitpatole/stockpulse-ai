# VO-039: Race condition in agent run history during concurrent requests

## User Story

Done. Here's the summary of what was added and why:

---

**Bug Story added to `docs/tasks/VO-004/user-story.md`**

**User story:** Platform operators need run history written correctly under concurrent load so analytics data is trustworthy.

**Key acceptance criteria:**
- 10 concurrent runs → 10 complete, non-corrupted rows in `agent_runs`
- No dropped or partially-written records
- No field cross-contamination (`duration_ms`, `status`, costs)
- Write path uses proper transactions (no bare read-modify-write)
- New concurrency regression test validates all of the above
- Analytics endpoint totals verified against concurrent-write fixture

**Priority: High** — corrupt run records silently break every metric on the dashboard we're about to ship. Garbage in, garbage out.

**Complexity: 2/5** — likely a missing transaction boundary. The fix is surgical; the regression test is most of the work.

This needs to ship *before* or *with* VO-004. No point launching an analytics dashboard built on unreliable data.
