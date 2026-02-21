# VO-375: Screen reader accessibility issue in agent run history

## Technical Design

Now I have everything I need. Let me also restore the VO-374 design.md to its correct content (I accidentally overwrote it with duplicate content that was already there — checking it was actually the same content, so no harm done). Let me now write the design spec for the accessibility task.

---

## VO-372: Screen Reader Accessibility — Agent Run History

### Approach

VO-371 landed the structural baseline (table semantics, `RunStatusBadge` labels, `<tr aria-label>`, `aria-live` on the table container, ActivityFeed live regions). Three gaps remain that the user story explicitly calls out: (1) the `aria-live` region covers the entire table and fires on every 15-second poll, creating announcement noise; (2) `run.error` is never rendered, so failed runs have no accessible (or visible) error detail; (3) `ActivityFeed`'s assertive region uses `role="status"` (which implies polite) instead of `role="alert"`. All fixes are frontend-only.

---

### Files to Modify

| File | Change |
|---|---|
| `frontend/src/app/agents/page.tsx` | Scope `aria-live` to a dedicated announcement div; add expandable error row for failed runs; add `role="region"` landmark |
| `frontend/src/components/agents/ActivityFeed.tsx` | Change `role="status"` → `role="alert"` on the assertive live region |
| `frontend/src/__tests__/agents/AgentRunHistory.test.tsx` | New — `jest-axe` audit + RTL assertions for expand/collapse and live region content |

---

### Data Model Changes

None. `run.error` is already present on the `AgentRun` type (`types.ts:61`) and returned by the API; it is just not rendered.

---

### API Changes

None.

---

### Frontend Changes

**`agents/page.tsx`**

1. **Scoped live announcement** — remove `aria-live` from the overflow `<div>`. Add a visually-hidden `<div aria-live="polite" aria-atomic="true" className="sr-only">` above the table that receives a string like `"Run history updated: 20 runs"` via `useEffect` whenever `runs` reference changes. Prevents full-table re-announcement on every poll cycle.

2. **Expandable error rows** — for runs where `run.error` is truthy:
   - Add a `<button aria-expanded={isOpen} aria-controls={`error-${run.id}`} aria-label={`Show error details for ${run.agent_name}`}>` inside the status cell.
   - Render a hidden sibling `<tr id={`error-${run.id}`} hidden={!isOpen}><td colSpan={5}><p role="alert">{run.error}</p></td></tr>`.
   - Error text is associated via `aria-describedby={`error-${run.id}`}` on the parent `<tr>`.

3. **Landmark region** — wrap the run history container in `<section aria-label="Agent run history">` so screen reader users can jump to it directly via landmark navigation.

**`ActivityFeed.tsx`**

- Line 70: `role="status"` → `role="alert"`. `role="status"` is polite by definition; the assertive `aria-live` is correct behavior but the roles conflict semantically and some AT implementations honour the role over the attribute.

---

### Testing Strategy

**File**: `frontend/src/__tests__/agents/AgentRunHistory.test.tsx`

| Test | Assertion |
|---|---|
| `axe audit — no violations` | `jest-axe` scan of full `<AgentsPage>` render with mock runs |
| `error row expand/collapse` | Click expand button → `aria-expanded="true"`, error `<tr>` visible; click again → hidden |
| `aria-controls target exists` | `aria-controls` ID matches rendered error row `id` |
| `live region fires on data change` | Mock `useApi` returning updated `runs[]` → announcement div text updates |
| `no announcement on first load` | Live region is empty until data has changed at least once (no "20 runs" on mount) |
| `failed run has describedby` | `<tr aria-describedby>` points to error row for failed status; absent for completed |

No new dependencies. `jest-axe` is assumed available; if not, add as a dev dependency alongside existing RTL setup.
