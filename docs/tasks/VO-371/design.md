# VO-371: Screen reader accessibility issue in agent run history

## Technical Design

## VO-370 Technical Design Spec: Screen Reader Accessibility — Agent Run History

---

### Approach

Pure frontend ARIA audit and remediation. No backend or DB changes required. Work is concentrated in the agents page and its sub-components: add semantic structure to the run history table, attach text equivalents to color/icon-only status indicators, wire up an `aria-live` region for dynamic updates, and verify keyboard focus order.

---

### Files to Modify

| File | Change |
|---|---|
| `frontend/src/app/agents/page.tsx` | Table semantics, `aria-live` region, `RunStatusBadge` labels |
| `frontend/src/components/agents/AgentCard.tsx` | Status dot text equivalents, run button label |
| `frontend/src/components/agents/ActivityFeed.tsx` | `aria-live` region for SSE events, connection indicator label |
| `frontend/src/components/layout/Sidebar.tsx` | Audit nav `title` → `aria-label` (minor) |

No new files needed; `sr-only` utility is already available via Tailwind.

---

### Data Model Changes

None.

---

### API Changes

None.

---

### Frontend Changes

**1. `agents/page.tsx` — Run History Table**
- Add `<caption className="sr-only">Agent run history</caption>` to the table
- Add `scope="col"` to all `<th>` elements
- Wrap the entire table in an `aria-live="polite" aria-atomic="false"` region so new rows are announced on refresh
- Add `aria-busy="true"` during loading state
- `RunStatusBadge`: add `aria-label={`Status: ${status}`}` to the wrapper span; add `<span className="sr-only">{status}</span>` alongside the icon so color + icon is never the sole conveyor of state
- Table rows: make each `<tr>` focusable (`tabIndex={0}`) with `aria-label` summarizing agent name, status, duration, and timestamp — enabling keyboard row navigation

**2. `AgentCard.tsx` — Status Indicator**
- Status dot (`animate-pulse` div): wrap with `<span role="img" aria-label={`Agent status: ${status}`}>` and add `<span className="sr-only">{status}</span>`
- Run button: change generic label to `aria-label={`Run ${agent.name}`}`

**3. `ActivityFeed.tsx` — Live Region**
- Wrap the event list in `<div aria-live="polite" aria-label="Agent activity feed">` for routine events
- For `agent_status` events carrying `failed`/`error`, emit into a separate `aria-live="assertive"` region (a visually hidden `<div>` that receives injected text on failure)
- Connection indicator button: add `aria-label={connected ? 'Activity feed connected' : 'Activity feed disconnected'}`

**No keyboard focus traps** to resolve — the panel uses standard scroll overflow with no modal-style capture.

---

### Testing Strategy

**Unit / Component**
- Jest + React Testing Library: assert `aria-label`, `aria-live`, `role`, `scope` attributes render correctly for each status variant (`completed`, `running`, `failed`, `error`)
- Test file: `frontend/src/__tests__/agents/RunStatusBadge.test.tsx` (new), assertions in existing agent page test if present

**Manual / Screen Reader**
- NVDA + Chrome: tab through table rows, verify announcements include agent name + status + timestamp; trigger a new run and confirm live region fires
- VoiceOver + Safari (secondary): same flow

**Automated**
- Add `axe-core` scan (via `jest-axe`) to the agents page render test — catches missing labels, contrast issues, structural violations
