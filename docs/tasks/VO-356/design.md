# VO-356: Race condition in SSE event streaming during concurrent requests

## Technical Design

The design doc is already scaffolded and my analysis confirms it. Here's the technical design spec:

---

## VO-350 Technical Design Spec

### 1. Approach

Apply a **module-level `threading.RLock`** in `settings_manager.py`, identical to the VO-344 scheduler pattern. The root bugs are two multi-step non-atomic write sequences:

- **`add_ai_provider()`**: `UPDATE SET is_active=0` (all) → `SELECT` (exists check) → `INSERT/UPDATE`. Two concurrent threads can both run the deactivate step before either inserts, leaving either 0 or 2 active rows.
- **`set_active_provider()`**: same deactivate-all → activate-one pattern, same race.

`set_setting()` uses `INSERT OR REPLACE` which SQLite serializes internally, but wrapping it is cheap and consistent. SQLite WAL mode already handles read-read concurrency — reads stay unlocked.

### 2. Files to Modify/Create

| File | Action |
|---|---|
| `backend/core/settings_manager.py` | Add `_lock = threading.RLock()` at module level; wrap `set_setting()`, `add_ai_provider()`, `set_active_provider()`, `delete_ai_provider()` with `with _lock:` blocks |
| `backend/tests/test_settings_race_condition.py` | **Create** — full regression suite |

No route changes needed. `backend/api/settings.py` delegates directly to manager functions, so locking at the manager layer covers all HTTP callers.

### 3. Data Model Changes

None. Existing schema is correct:
- `settings(key TEXT PRIMARY KEY, ...)` — PK prevents duplicate keys at DB level; bug is application-layer only
- `ai_providers(id, is_active, ...)` — no constraint on `is_active` uniqueness (intentional for flexibility), so the race must be closed at the application layer

### 4. API Changes

None. Fix is fully transparent to HTTP callers.

### 5. Frontend Changes

None.

### 6. Testing Strategy

**File**: `backend/tests/test_settings_race_condition.py`

Six test classes mirroring the VO-343/VO-344 harness pattern:

| Class | What It Proves |
|---|---|
| `TestSetSettingSingleThreaded` | Baseline correctness: new key, overwrite, empty value |
| `TestConcurrentSetSetting` | 10 threads → same key; final DB has exactly one row, consistent value |
| `TestConcurrentAddAiProvider` | 10 threads `add_ai_provider()` concurrently; assert exactly `1` row with `is_active=1` |
| `TestConcurrentSetActiveProvider` | 10 threads each activating a different provider; final state: exactly one `is_active=1` |
| `TestDeleteUnderConcurrentRead` | Delete during concurrent reads; no exceptions, no dirty reads |
| `TestSettingsRoutes` | HTTP smoke tests via Flask test client (mirrors VO-344 route tests) |

Concurrency harness (consistent with prior art):
```python
barrier = threading.Barrier(N)
results = []
lock = threading.Lock()
threads = [threading.Thread(target=lambda: (barrier.wait(), worker())) for _ in range(N)]
[t.start() for t in threads]
[t.join(timeout=5) for t in threads]
assert db_query("SELECT COUNT(*) FROM ai_providers WHERE is_active=1") == 1
```

**Key invariants to assert**: exactly one `is_active=1` row after concurrent writes; `settings` table has no duplicate keys; no thread raises an unhandled exception.
