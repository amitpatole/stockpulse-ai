# VO-017: Null reference in settings page when user has no data

## User Story

**VO-017 | Settings Page | P1**

**User Story:** As a new user with no existing data, I want the settings page to load and display correctly, so that I can configure my account without hitting a crash on my very first visit.

**Acceptance Criteria:**
- Settings page renders without error when user has no trades, watchlists, alerts, or profile data
- All settings sections show a graceful empty/default state — no null reference exceptions
- No blank screen or unhandled crash for any valid account state
- Null/undefined fields fall back to safe defaults
- Error is never surfaced to the user (silent graceful degradation)
- Regression test added covering the zero-data user scenario

**Priority:** P1 — High. Crash-level bug, QA-confirmed. Settings page is hit early in onboarding — exactly when users have no data. First impressions matter.

**Complexity:** 2/5 — Almost certainly a missing null guard on a data access path. Low surface area, well-understood fix. Regression test is non-negotiable.

**Bottom line:** Assign it, point the dev at the settings component, close it this sprint.
