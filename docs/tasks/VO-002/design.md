# VO-002: Add watchlist portfolio groups with CRUD

## Technical Design

The design spec is written. Here's a summary of the key decisions:

**Architecture decisions:**

- **`stocks` table stays as a global registry** — it's already used by the scheduler, news, and AI ratings systems. Watchlist membership is a pure overlay via junction table, so no existing queries break.

- **No ORM migration runner** — consistent with the project's pattern. The migration lives in `init_all_tables()` using the same `PRAGMA table_info` approach already used for `_migrate_news`.

- **Client-side filtering, not a new ratings endpoint** — `StockGrid` already fetches all ratings; filtering by the active watchlist's ticker array client-side avoids a new backend query and keeps the polling logic simple.

- **`localStorage` for active watchlist** — no session infrastructure exists; this is the right fit for the stack.

- **Drag-and-drop deferred** — the user story explicitly calls this out as a v2 addition. Shipping without it keeps complexity at a manageable level.

**Scope is clean:** 3 backend files touched, 2 new frontend components, 3 frontend files modified. The `stocks` blueprint is untouched, so nothing regresses on the existing flat-list behavior during the migration window.
