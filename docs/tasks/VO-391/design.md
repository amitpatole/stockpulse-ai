# VO-391: Screen reader accessibility issue in SSE event streaming

## Technical Design

## VO-387: Technical Design Spec — Screen Reader Accessibility for SSE Streaming

---

### 1. Approach

Add a single `SSEAccessibilityAnnouncer` component mounted in the root layout that subscribes to `useSSE()` and writes formatted strings into two always-present `aria-live` regions — `assertive` for price alerts and `polite` for news, rating updates, and connection status transitions. A 500ms debounce guard on the hook prevents duplicate announcements when events fire in rapid succession.

---

### 2. Files to Create/Modify

- **CREATE**: `frontend/src/components/accessibility/SSEAccessibilityAnnouncer.tsx`
- **MODIFY**: `frontend/src/hooks/useSSE.ts` (expose `announcement` state: `{ assertive, polite }`; track connection transitions; add 500ms debounce)
- **MODIFY**: `frontend/src/app/layout.tsx` (mount `<SSEAccessibilityAnnouncer />` inside root layout, before `{children}`)

---

### 3. Data Model

No backend changes. No new SQLite tables or columns.

---

### 4. API Spec

No new endpoints. SSE payloads on `/api/stream` are unchanged. Existing `AlertEvent`, `NewsEvent`, and connection state from `useSSE` are sufficient.

---

### 5. Frontend Component Spec

**Component**: `SSEAccessibilityAnnouncer`
**File**: `frontend/src/components/accessibility/SSEAccessibilityAnnouncer.tsx`

**Renders in**: `frontend/src/app/layout.tsx` — before `{children}` so it is in the DOM on every page load, never injected dynamically.

**Layout** (visually hidden, always present):
```tsx
<div className="sr-only" aria-live="assertive" aria-atomic="true">
  {assertiveMessage}
</div>
<div className="sr-only" aria-live="polite" aria-atomic="true">
  {politeMessage}
</div>
```

**Announcement logic in `useSSE.ts`**:

| SSE Event | Live Region | Format |
|---|---|---|
| `alert` | `assertive` | `"Price alert: {ticker} {message}"` |
| `news` | `polite` | `"News update: {headline}"` |
| `rating_update` | `polite` | `"Rating update: {ticker} rated {rating}"` |
| `job_complete` | `polite` | `"Job complete: {job_name}"` |
| connection → reconnecting | `polite` | `"Market data stream reconnecting"` |
| connection → disconnected | `polite` | `"Market data stream disconnected"` |
| connection → connected | `polite` | `"Market data stream connected"` |

**Debounce guard** (inside `useSSE.ts`):
```ts
const lastAnnouncementRef = useRef<{ text: string; ts: number }>({ text: '', ts: 0 });

function announce(text: string, channel: 'assertive' | 'polite') {
  const now = Date.now();
  if (text === lastAnnouncementRef.current.text && now - lastAnnouncementRef.current.ts < 500) return;
  lastAnnouncementRef.current = { text, ts: now };
  setAnnouncement(prev => ({ ...prev, [channel]: text }));
}
```

Connection transition tracking: compare previous `connected` value with current via `useRef<boolean | null>` to fire only on state change.

**Loading/error states**: None — this component has no visible UI or loading state.

---

### 6. Verification

1. **Price alert announcement**: Trigger a price alert via the backend; NVDA on Firefox or VoiceOver on Safari should announce the formatted string (e.g., "Price alert: AAPL crossed above $195.00") exactly once, even if the SSE event fires twice within 500ms.

2. **Connection status transition**: Kill the backend SSE server mid-session and confirm the screen reader announces "Market data stream reconnecting" once, not repeatedly on each reconnect attempt; restore the server and confirm "Market data stream connected" fires once.

3. **Priority ordering**: Simultaneously trigger an `alert` event and a `news` event; confirm the alert (assertive) is announced before the news (polite) and that the news announcement does not interrupt a mid-sentence alert read-out.
