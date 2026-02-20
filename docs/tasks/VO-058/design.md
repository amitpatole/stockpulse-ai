# VO-058: Fix broken Google sign-in in login flow

## Technical Design

## Technical Design Spec: Google Sign-In (VO-035)

---

### 1. Approach

Add Google OAuth 2.0 using `authlib` (OAuth client) and `flask-login` (session management). A new `auth` blueprint handles the OAuth dance. All existing API routes get a `@login_required` decorator. The Next.js frontend gets a `/login` page and a middleware redirect for unauthenticated users. Session state lives server-side in Flask, consistent with the existing `SECRET_KEY` config.

---

### 2. Files to Modify / Create

**Create:**
- `backend/api/auth.py` — OAuth routes (`/auth/google`, `/auth/google/callback`, `/auth/logout`, `/auth/me`)
- `backend/auth_utils.py` — `LoginManager` init, `User` model class (not ORM — raw SQL, consistent with existing pattern), `login_required` decorator
- `frontend/src/app/login/page.tsx` — Login page component
- `frontend/src/middleware.ts` — Next.js middleware for auth redirect

**Modify:**
- `backend/app.py` — Register `auth` blueprint, init `LoginManager`
- `backend/database.py` — Add `users` table creation to `init_all_tables()`
- `backend/config.py` — Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `OAUTHLIB_INSECURE_TRANSPORT`
- `backend/requirements.txt` — Add `authlib`, `flask-login`
- `backend/api/*.py` (all 10 blueprints) — Add `@login_required` to route handlers

---

### 3. Data Model Changes

```sql
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT    UNIQUE NOT NULL,
    name       TEXT,
    google_id  TEXT    UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

No migration tool in use — `init_all_tables()` in `database.py` runs on startup and uses `CREATE TABLE IF NOT EXISTS`, so this is a safe additive change.

---

### 4. API Changes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/google` | Redirect to Google OAuth consent screen |
| `GET` | `/auth/google/callback` | Exchange code, upsert user, create session, redirect to `/` |
| `GET` | `/auth/logout` | Clear session, redirect to `/login` |
| `GET` | `/auth/me` | Return `{id, email, name}` for authenticated user; `401` otherwise |

On callback failure: redirect to `/login?error=auth_failed` — no stack trace, no Google error detail exposed.

---

### 5. Frontend Changes

**`frontend/src/app/login/page.tsx`** — Minimal page: app name, single "Sign in with Google" button that navigates to `http://localhost:5000/auth/google`. No client-side OAuth; the backend owns the full flow.

**`frontend/src/middleware.ts`** — Next.js middleware checks `/auth/me` on every request. If `401`, redirects to `/login`. Excludes `/login` itself from the check to avoid redirect loops.

No new state management needed — auth state fetched via `useEffect` on page load using the existing fetch pattern in the codebase.

---

### 6. Testing Strategy

**Unit tests** (`backend/tests/`):
- `test_users_table_created` — assert `users` table exists after `init_all_tables()`
- `test_login_required_returns_401` — hit any `/api/*` route without session, expect `401`

**Integration tests** (mock Google's token endpoint with `responses` or `unittest.mock`):
- `test_oauth_callback_creates_user` — simulate valid callback, assert user row inserted, session set
- `test_oauth_callback_upserts_existing_user` — same Google ID twice, assert no duplicate row
- `test_logout_clears_session` — after login, call `/auth/logout`, assert `/auth/me` returns `401`
- `test_callback_failure_no_stack_trace` — simulate Google error, assert response body contains no traceback

**Manual smoke test checklist** (in task acceptance):
- Sign in → lands on dashboard
- Hard-refresh → stays authenticated
- `/auth/logout` → back to `/login`
- Direct `/api/stocks` without session → `401`
