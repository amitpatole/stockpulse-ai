# VO-337: Screen reader accessibility issue in data provider fallback chain

## User Story

---

## User Story: Screen Reader Accessibility — Data Provider Fallback Chain

---

### User Story

**As a** visually impaired trader using a screen reader,
**I want** to be notified when the app switches to a fallback data provider,
**so that** I understand why data may be delayed or from a different source, and can trust the information I'm hearing.

---

### Acceptance Criteria

- When the fallback chain activates (e.g., Polygon → Yahoo Finance), an ARIA live region announces the provider change (e.g., *"Data source switched to Yahoo Finance (free tier). Some data may be delayed."*)
- The Settings page (`/settings`) data provider status indicators include `aria-label` attributes describing provider name, tier, and health state — not just color coding
- Provider status changes (healthy → error → fallback) are announced without requiring page focus change (`aria-live="polite"`)
- No duplicate or redundant announcements on rapid consecutive fallbacks (debounce minimum 3s)
- All existing screen reader behavior on the Settings page is unaffected

---

### Priority Reasoning

**High.** Accessibility is a legal compliance requirement and a trust signal. Users relying on screen readers are making financial decisions — silent provider switches create information asymmetry that undermines the product entirely. QA caught this during review, so it's not yet in production, but it ships in the next release window.

---

### Estimated Complexity

**2 / 5**

The fallback logic already exists in `backend/data_providers/base.py` (registry `get_quote()`, lines 148–196). The fix is primarily frontend: add an ARIA live region to the Settings page (`frontend/src/app/settings/page.tsx`) and wire it to provider state changes. No backend changes required.
