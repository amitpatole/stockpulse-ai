# VO-350: Race condition in settings persistence during concurrent requests

## Technical Design

## VO-350 Technical Design Spec: Race Condition in Settings Persistence

### 1. Approach

Apply a **module-level `threading.RLock`** in `settings_manager.py`, mirroring the scheduler.py pattern (VO-344). The root issue is that multi-step write operations (`deactivate-all → check-exists → insert/update`) are non-atomic — concurrent threads interleave across those steps, producing 0 or 2+ active providers.

The lock guards all write paths. Reads remain unlocked (WAL mode handles read-read concurrency). No schema changes needed — SQLite's WAL + the application-level mutex is sufficient.

---

### 2. Files to Modify/Create

| File | Action |
|---|---|
| `backend/core/settings_manager.py` | Add module-level `_lock = threading.RLock()`, wrap `set_setting()`, `add_ai_provider()`, `set_active_provider()`, `delete_ai_provider()` with `with _lock:` |
| `backend/tests/test_settings_race_condition.py` | **Create** — regression test suite (≥10 concurrent threads) |

No other files need changes. The API routes in `backend/api/settings.py` delegate directly to `settings_manager` functions, so locking at the manager layer covers all callers.

---

### 3. Data Model Changes

None. The existing schema is sound:

```sql
settings(key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP)
ai_providers(id, provider_name, api_key, model, is_active, ...)
```

The `PRIMARY KEY` on `settings.key` already prevents duplicate key insertion at the DB level. The bug is purely in multi-step application logic, not schema.

---

### 4. API Changes

None. Existing endpoints remain unchanged — the fix is transparent to HTTP callers.

---

### 5. Frontend Changes

None.

---

### 6. Testing Strategy

**File**: `backend/tests/test_settings_race_condition.py`

**Test classes:**

- **`TestSetSettingSingleThreaded`** — correctness baseline: upsert new key, overwrite existing, empty/null values
- **`TestConcurrentSetSetting`** — 10 threads writing to the same key simultaneously; assert final DB state contains exactly one consistent value (last write wins, no corruption)
- **`TestConcurrentAddAiProvider`** — 10 threads calling `add_ai_provider()` concurrently; assert exactly one row has `is_active = 1` post-run
- **`TestConcurrentSetActiveProvider`** — 10 threads each activating a different provider; assert exactly one `is_active = 1` row in final state
- **`TestDeleteUnderConcurrentRead`** — delete while concurrent reads are in-flight; assert no exceptions and no dirty reads
- **`TestSettingsRoutes`** — HTTP smoke tests on existing endpoints under load (mirrors the scheduler route tests)

**Harness pattern** (consistent with VO-343/VO-344):
```python
barrier = threading.Barrier(N)
threads = [threading.Thread(target=lambda: (barrier.wait(), write_op())) for _ in range(N)]
[t.start() for t in threads]
[t.join(timeout=5) for t in threads]
assert exactly_one_active_provider(db_path)
```
