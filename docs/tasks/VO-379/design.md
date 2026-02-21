# VO-379: Race condition in settings persistence during concurrent requests

## Technical Design

---

## VO-350 Technical Design Spec — Race Condition in Settings Persistence

### 1. Approach

Add a module-level `threading.RLock` to `settings_manager.py` that serializes all multi-step write operations. The critical race paths are `add_ai_provider()` (deactivate-all → check-exists → upsert) and `set_active_provider()` (deactivate-all → activate-one) — both are non-atomic multi-statement sequences that can interleave under concurrent requests, leaving zero or multiple active providers. Reads remain unlocked since SQLite WAL mode already provides safe concurrent reads.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/core/settings_manager.py` — add module-level `_lock = threading.RLock()`, wrap `add_ai_provider()`, `set_active_provider()`, and `delete_ai_provider()` write paths with `with _lock:`
- **CREATE**: `backend/tests/test_settings_race_condition.py` — concurrency regression test suite (10+ threads hammering same key/provider simultaneously, barrier-synchronized)

---

### 3. Data Model

No schema changes. Existing tables are correct:

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    api_key TEXT NOT NULL,
    model TEXT,
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`INSERT OR REPLACE INTO settings` is already atomic at the SQLite level — no lock needed there. The `ai_providers` multi-step sequences are the sole target.

---

### 4. API Spec

No new endpoints. No changes to existing response contracts. All existing routes in `backend/api/settings.py` remain identical — the fix is purely in the persistence layer below them.

---

### 5. Frontend Component Spec

Not applicable. This is a backend-only bugfix with no user-visible UI changes.

---

### 6. Verification

1. **Concurrent activation test**: Spin 10 threads simultaneously calling `set_active_provider()` with different provider IDs; assert exactly one row has `is_active = 1` after all threads complete — no zero-active or multi-active states.
2. **Interleaved add test**: 10 threads concurrently call `add_ai_provider()` with `set_active=True` on distinct providers; assert the DB has no duplicate `is_active = 1` rows and all providers are inserted exactly once.
3. **Manual smoke test**: Open two browser tabs, change the active AI provider in both simultaneously, reload — confirm the UI reflects exactly one active provider with no 500 errors in the Flask log.
