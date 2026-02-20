# VO-024: Stale cache in auth flow shows outdated data

## User Story

## User Story: Stale Cache in Auth Flow

---

**Story**

As a returning user, I want the auth flow to display current, accurate data upon login, so that I can trust the information I see reflects my actual account state and avoid making decisions based on outdated data.

---

**Acceptance Criteria**

- Cache is invalidated or refreshed at the start of each auth flow (login, token refresh, session restore)
- User profile, permissions, and session data shown post-login match the latest server state
- No stale data from a previous session bleeds into a new session
- QA can reproduce the original bug scenario and confirm it no longer occurs
- No regression in auth flow performance (cache invalidation does not cause noticeable latency spike)

---

**Priority Reasoning**

**High.** Auth flow is a trust boundary. Showing stale data here — especially permissions or account state — can cause incorrect access decisions, user confusion, and potential security implications. QA caught it, but it's the kind of bug users notice and lose confidence over fast.

---

**Complexity: 3 / 5**

Cache invalidation is always nuanced — need to identify exactly what's cached, where (client vs. server), and when the TTL is set. Likely straightforward once the cache layer is located, but warrants careful testing across session edge cases (logout/login, token expiry, multi-tab).

---

**Next step:** Assign to an engineer to locate the cache layer in the auth flow and confirm scope before estimating sprint placement.
