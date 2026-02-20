# VO-058: Fix broken Google sign-in in login flow

## User Story

Good. Let me be direct about what the codebase shows.

---

## User Story: VO-XXX — Google Sign-In for Login Flow

> **Context note:** The codebase has **no user authentication system** today — no login page, no OAuth routes, no user table. This is a greenfield build, not a bug fix. Framing it as "broken" is inaccurate; it was never implemented.

---

### User Story

**As a** Virtual Office user,
**I want** to sign in with my Google account,
**so that** I can access the app securely without managing a separate password.

---

### Acceptance Criteria

- [ ] A login page exists at `/login` with a "Sign in with Google" button
- [ ] Clicking the button initiates Google OAuth 2.0 flow via a `/auth/google` route
- [ ] On success, a session is created and the user is redirected to the dashboard
- [ ] On failure, a clear error message is shown — no stack traces, no sensitive data in logs
- [ ] Unauthenticated requests to any route redirect to `/login`
- [ ] Sign-out clears the session and redirects to `/login`
- [ ] A `users` table is created in the DB (id, email, name, google_id, created_at)
- [ ] All API keys remain inaccessible without an active session

---

### Priority Reasoning

**P1.** The app currently has zero access control — any user on the network can read API keys and configure AI providers. Google sign-in is the fastest path to gating access without building a credential system from scratch.

---

### Complexity: 3/5

Standard OAuth 2.0 integration. Flask has mature libraries (`authlib`, `flask-login`). The work is real — new DB schema, session middleware, route guards on all existing endpoints — but nothing exotic.

---

**Recommended owner:** Backend engineer familiar with Flask. Frontend changes are minimal (login page only).
