# VO-368: Timezone display bug in scheduler configuration for non-US locales

## User Story

## VO-XXX: Timezone Display Bug in Scheduler Configuration

---

### User Story

**As a** trader or analyst using Virtual Office outside the United States,
**I want** the scheduler configuration to display and interpret job times in my local timezone,
**so that** I can schedule data fetches, alerts, and reports at the correct local time without mentally converting from US timezones.

---

### Acceptance Criteria

- [ ] Scheduler UI displays all job times in the user's local timezone (detected from browser or user profile setting)
- [ ] Cron/interval triggers stored in the database use UTC internally; display layer handles conversion
- [ ] When creating or editing a scheduled job, the time picker reflects local timezone with a visible timezone label (e.g., `09:00 CET`)
- [ ] Existing persisted jobs are not affected — stored UTC values remain unchanged
- [ ] Scheduler route responses include a `timezone` field alongside trigger args
- [ ] Non-US locales tested: at minimum UTC+1 (CET), UTC+5:30 (IST), UTC+9 (JST), UTC-3 (BRT)
- [ ] No regression in existing scheduler tests (`test_scheduler_race_condition.py`, 45 tests still pass)

---

### Priority Reasoning

**High.** The scheduler is core infrastructure — it drives alerts, data pulls, and reports. A non-US user scheduling a job at "09:00" getting UTC instead of local time causes silent, hard-to-debug failures. Trust in the platform erodes quickly when jobs fire at the wrong time. This is a correctness bug, not cosmetic.

---

### Estimated Complexity

**3 / 5**

- Backend: Low risk — UTC storage is already correct per `scheduler.py`; only the API response layer needs a `timezone` field surfaced
- Frontend: Moderate — timezone-aware time picker + display formatting
- Testing: Add locale-parameterized tests; existing 45 scheduler tests must stay green

---

**Definition of Done:** Bug cannot be reproduced for any non-US locale. QA sign-off on CET and IST manual test cases.
