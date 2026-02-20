# VO-025: Memory leak in export feature after prolonged usage

## User Story

---

## User Story: Memory Leak in Export Feature

**Story ID:** BUG-040

---

### User Story

> As a **power user running the platform for extended sessions**, I want the **export/download tracking feature to release memory properly after each operation**, so that **the application remains stable and performant without requiring restarts**.

---

### Acceptance Criteria

- [ ] `requests.Session()` objects in all data providers are closed after use (via context managers or explicit `.close()`)
- [ ] CrewAI `Crew` objects are explicitly destroyed after `kickoff()` completes — no lingering agent memory accumulation
- [ ] Memory usage does not grow unboundedly during repeated export/download tracking operations over a 4+ hour session
- [ ] QA can confirm stable RSS memory after 50+ consecutive export cycles
- [ ] No open socket/file descriptor leaks detectable via `lsof` or equivalent tooling
- [ ] Exception paths close resources the same as happy paths (no leak on failure)

---

### Priority Reasoning

**High.** This is a QA-confirmed bug with a clear reproduction path. Memory leaks degrade reliability over time and will hit production users running long sessions — exactly the power users we can't afford to lose. The root causes are well-identified (unmanaged HTTP sessions, CrewAI object accumulation) and scoped. Fix it before it becomes a customer complaint.

---

### Estimated Complexity

**2 / 5**

Root causes are already identified. The fix is largely mechanical — wrap sessions in context managers, add explicit cleanup after crew execution. No architectural changes needed. Risk of regression is low if changes are localized to resource management code.
