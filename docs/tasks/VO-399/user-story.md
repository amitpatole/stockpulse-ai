# VO-399: Screen reader accessibility issue in data provider fallback chain

## User Story

## User Story: VO-362 — Screen Reader Accessibility in Data Provider Fallback Chain

---

### User Story

**As a** trader using a screen reader to monitor live market data,
**I want** to be notified when the data provider switches to a fallback source,
**so that** I understand why data may look different and can trust the information I'm acting on.

---

### Acceptance Criteria

- When the primary data provider fails and a fallback is activated, an ARIA live region announces the switch (e.g., *"Primary data source unavailable. Using fallback provider."*)
- When the primary provider recovers, a follow-up announcement confirms the switch back
- ARIA announcements use `aria-live="polite"` for fallback events and `aria-live="assertive"` only if data becomes fully unavailable
- Fallback state is visually indicated (e.g., a status badge) with an accessible label — not color alone
- The fallback status badge is reachable via keyboard tab order and readable by screen readers
- No duplicate or redundant announcements fire if the provider flaps rapidly (debounce ≥ 2s)
- All changes pass WCAG 2.1 AA automated checks (axe-core or equivalent)

---

### Priority Reasoning

**High.** Financial decisions depend on data provenance. A sighted user sees a visual indicator; a screen reader user gets nothing — that's a material information gap, not just a cosmetic gap. Regulatory risk (ADA/accessibility compliance) compounds the user impact.

---

### Estimated Complexity

**3 / 5**

Straightforward DOM/ARIA work, but requires coordination between the data provider service layer (backend event emission) and the frontend SSE consumer to propagate fallback state reliably without over-announcing.
