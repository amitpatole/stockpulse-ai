# VO-011: Add pagination to news and research list endpoints

## Technical Design

Design spec written to `docs/tasks/VO-003/design.md`. Here's the summary:

---

**Key decisions made:**

1. **Shared helper per-file, not a shared module.** A `_parse_pagination()` helper stays local to each blueprint. Extracting it to a shared util would be premature for two callers — we can refactor later if a third endpoint needs it.

2. **Paired COUNT + SELECT.** Each paginated request runs two queries: a `COUNT(*)` with the same `WHERE` clause for `total`, then the windowed `SELECT` with `LIMIT ? OFFSET ?`. Both use bound parameters only.

3. **`research.py` DB access left alone.** It uses `sqlite3.connect(Config.DB_PATH)` directly instead of `get_db_connection()`. That inconsistency is real but out of scope — touching it risks introducing a bug orthogonal to pagination.

4. **`limit` param in research retired, not deprecated.** The user story says remove it. It has no known external consumers (no frontend tests reference it), so a clean cut is safer than a compatibility shim.

5. **Response envelope is the only breaking change.** Top-level shape goes from `[...]` to `{ data: [...], page, page_size, total }`. Frontend teams need to update their fetch hooks, but that's explicitly out of VO-003's scope.

6. **No schema migrations.** `created_at` columns already exist and drive ordering; `COUNT(*)` needs nothing new.
