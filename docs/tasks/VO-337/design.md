# VO-337: Screen reader accessibility issue in data provider fallback chain

## Technical Design

I now have a complete picture of the stack. Here's the technical design spec:

---

## Technical Design Spec: Screen Reader Accessibility — Data Provider Fallback Chain

---

### 1. Approach

Two-part, purely additive change. No schema migration, no new endpoints.

**Backend**: Wire a `provider_fallback` SSE event into `DataProviderRegistry.get_quote()` and `get_historical()` via an optional callback injected at app startup. The registry already has `logger.warning` on each failed provider (`base.py:164, 184`); we emit an SSE event from those same sites when the fallback actually succeeds.

**Frontend**: (a) Add an `aria-live="polite"` announcement region to `settings/page.tsx` that renders the latest fallback message, debounced ≥3 s; (b) add `aria-label` attributes to the existing color-dot status indicators in that page; (c) extend `useSSE` to track `provider_fallback` events; (d) add the new event type to `types.ts`.

---

### 2. Files to Modify

| File | Change |
|---|---|
| `backend/data_providers/base.py` | Add optional `on_fallback: Callable[[str, str, str], None] \| None` to `DataProviderRegistry.__init__`; call it inside `get_quote` and `get_historical` when a non-primary provider returns data |
| `backend/app.py` | After building the registry, set `registry.on_fallback = lambda from_, to_, reason: send_sse_event('provider_fallback', {...})` |
| `frontend/src/lib/types.ts` | Add `'provider_fallback'` to `SSEEventType`; add `ProviderFallbackEvent` interface |
| `frontend/src/hooks/useSSE.ts` | Handle `provider_fallback` case in `handleEvent`; expose `lastProviderFallback: ProviderFallbackEvent \| null` from hook state |
| `frontend/src/app/settings/page.tsx` | (1) Consume `lastProviderFallback` from `useSSE`; (2) render a `<div role="status" aria-live="polite" aria-atomic="true">` that shows the message string; (3) add `aria-label` to each color-dot status indicator |

No new files needed.

---

### 3. Data Model Changes

None.

---

### 4. API Changes

No new endpoints. The existing `/api/stream` SSE endpoint gains one new named event:

```
event: provider_fallback
data: {"from_provider": "Polygon", "to_provider": "Yahoo Finance",
       "tier": "free", "reason": "exception", "timestamp": "..."}
```

---

### 5. Frontend Changes

**`types.ts`** — extend union and add interface:
```ts
export type SSEEventType = ... | 'provider_fallback';

export interface ProviderFallbackEvent {
  from_provider: string;
  to_provider: string;
  tier: string;           // 'free' | 'freemium' | 'premium'
  reason: string;         // 'exception' | 'no_data'
  timestamp: string;
}
```

**`useSSE.ts`** — add `lastProviderFallback` to `SSEState`; populate it in the `provider_fallback` case.

**`settings/page.tsx`** — two concrete changes:

1. **ARIA live region** — placed at the top of the page body, always mounted but visually hidden when empty:
```tsx
const DEBOUNCE_MS = 3000;
const lastAnnouncedRef = useRef<number>(0);
const { lastProviderFallback } = useSSE();
const [announcement, setAnnouncement] = useState('');

useEffect(() => {
  if (!lastProviderFallback) return;
  const now = Date.now();
  if (now - lastAnnouncedRef.current < DEBOUNCE_MS) return;
  lastAnnouncedRef.current = now;
  setAnnouncement(
    `Data source switched to ${lastProviderFallback.to_provider} (${lastProviderFallback.tier} tier). Some data may be delayed.`
  );
}, [lastProviderFallback]);

// In JSX:
<div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
  {announcement}
</div>
```

2. **`aria-label` on color dots** — the three existing status rows in the System Status section (`base.py:303-334`) each have an unlabeled `<span className="h-2 w-2 rounded-full ...">`. Add:
```tsx
<span
  aria-label={`${label}: ${statusText}`}
  className={clsx('h-2 w-2 rounded-full', colorClass)}
/>
```
where `label` is `"Backend API"` / `"Database"` / `"yfinance (Free)"` and `statusText` is the string already rendered in the adjacent `<span>`.

---

### 6. Testing Strategy

**Backend unit test** (extend `backend/tests/test_data_provider_fallback.py`):
- Add `test_on_fallback_callback_called_on_exception`: configure a mock callback on the registry; primary raises, fallback succeeds; assert callback called once with correct `(from, to, reason)` args.
- Add `test_on_fallback_not_called_when_primary_succeeds`: primary returns valid data; assert callback never called.
- Add `test_on_fallback_none_safe`: registry with no callback set; primary raises, fallback succeeds without error (no `AttributeError`).

**Backend integration**: confirm `send_sse_event` is called with `'provider_fallback'` via a mock patch on `app.send_sse_event` when `registry.get_quote` falls back.

**Frontend — `useSSE` hook**: unit test with a mock `EventSource` that emits a `provider_fallback` event; assert `lastProviderFallback` is populated correctly.

**Frontend — Settings page**: React Testing Library snapshot or assertion:
- Render `<SettingsPage />` with a mocked `useSSE` returning a non-null `lastProviderFallback`; query by `role="status"` and assert expected announcement text.
- Assert all three status dot `<span>` elements have a non-empty `aria-label`.
- Trigger two rapid fallback events < 3 s apart; assert announcement DOM node is updated only once (debounce).

**Regression**: existing `pytest backend/tests/test_data_provider_fallback.py` suite must pass unmodified — the callback is optional (`None` by default), so existing tests are unaffected.
