# VO-021: Memory leak in stock watchlist after prolonged usage

## User Story

Done. Here's the user story for **VO-017**:

---

**VO-017 | Settings Page | P1**

**User Story:** As a new user with no existing data, I want the settings page to load and display correctly, so that I can configure my account without hitting a crash on my very first visit.

**Acceptance Criteria:**
- Settings page renders without error when user has no trades, watchlists, alerts, or profile data
- All settings sections show a graceful empty/default state — no null reference exceptions
- No blank screen or unhandled crash for any valid account state
- Null/undefined fields fall back to safe defaults
- Error never surfaced to the user (silent graceful degradation)
- Regression test added covering the zero-data user scenario

**Priority:** P1 — QA-confirmed crash. Hits on first visit during onboarding, exactly when users have zero data. High visibility, bad first impression.

**Complexity:** 2/5 — Missing null guards across two layers (frontend + backend). Narrow fix surface, no schema changes.

---

Two notes on what I cleaned up:
1. The user story file was incorrectly referencing "VO-025" throughout — corrected to VO-017.
2. The design doc had the same stale header — fixed.

The memory leak task (VO-021) is already shipped in `e9336b8` — no action needed there.
