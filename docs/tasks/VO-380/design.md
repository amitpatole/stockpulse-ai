# VO-380: Timezone display bug in chart rendering for non-US locales

## Technical Design

Now I have enough context. Let me write the spec.

---

## VO-379: Technical Design Spec — Timezone Display Bug in Chart Rendering

### 1. Approach

The root bug is twofold: `PriceChart.tsx` sets a `localization.timeFormatter` (crosshair tooltip only) but never sets a `tickMarkFormatter` on the `timeScale`, so x-axis tick labels render in UTC by the library default. Additionally, `timeFormatter` omits `hour`/`minute` options, making intraday crosshair labels show date-only. The fix adds a timezone-aware `tickMarkFormatter` to the `timeScale` config and repairs `timeFormatter` to include time for intraday timeframes — all client-side, requiring no backend or API changes.

---

### 2. Files to Create/Modify

- MODIFY: `frontend/src/components/charts/PriceChart.tsx` — add `timeframe` prop; add `tickMarkFormatter` to `timeScale`; fix `timeFormatter` to include `hour`/`minute` for intraday timeframes
- MODIFY: `frontend/src/components/stocks/StockPriceChart.tsx` — pass `timeframe` prop down to `PriceChart`

No backend changes. No new files.

---

### 3. Data Model

No schema changes. Backend already emits correct UTC Unix timestamps (seconds). Timezone conversion is purely a rendering concern.

---

### 4. API Spec

No new endpoints. The existing `GET /api/stocks/<ticker>/detail?timeframe=<tf>` response is unchanged.

---

### 5. Frontend Component Spec

**Component**: `PriceChart` — `frontend/src/components/charts/PriceChart.tsx`

**New prop**:
```ts
timeframe?: '1D' | '1W' | '1M' | '3M' | '1Y' | 'All'
```

**Logic changes inside `useEffect`**:

```ts
const isIntraday = timeframe === '1D' || timeframe === '1W';

// Fix 1: tickMarkFormatter on timeScale (controls x-axis labels)
timeScale: {
  borderColor: '#334155',
  timeVisible: true,
  tickMarkFormatter: (time: UTCTimestamp, tickMarkType, locale) => {
    const d = new Date(time * 1000);
    if (tickMarkType === TickMarkType.Time) {
      return new Intl.DateTimeFormat(locale, {
        timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false,
      }).format(d);
    }
    return new Intl.DateTimeFormat(locale, {
      timeZone: tz, month: 'short', day: 'numeric',
    }).format(d);
  },
},

// Fix 2: timeFormatter — include time for intraday
localization: {
  timeFormatter: (time: Time) => {
    if (typeof time !== 'number') return String(time);
    return new Intl.DateTimeFormat(undefined, {
      timeZone: tz,
      month: 'short', day: 'numeric',
      ...(isIntraday ? { hour: '2-digit', minute: '2-digit', hour12: false } : { year: 'numeric' }),
    }).format(new Date(time * 1000));
  },
},
```

**Caller** — `StockPriceChart.tsx`: pass `timeframe={activeTimeframe}` to `<PriceChart />`.

**Timezone label** (line 129, already present): no change needed — still renders `"All times in Europe/London"` etc.

**Error/loading states**: unchanged (handled by `useApi` in `StockPriceChart`).

---

### 6. Verification

1. **Non-US timezone regression**: Set browser locale to `Europe/London` or `Asia/Tokyo`, load a `1D` chart — x-axis tick times and crosshair tooltip must show local time (e.g., `14:30` ET appears as `19:30` in London), and the footer label must read the correct IANA timezone name.

2. **Timeframe switching**: Cycle through `1D → 1W → 1M → 1Y` — intraday frames (`1D`, `1W`) must show `HH:MM` in tick labels; daily frames must show `MMM D`; no UTC bleed-through on any frame.

3. **US locale no-regression**: Set browser to `America/New_York`, confirm `1D` chart still shows market hours correctly (9:30–16:00) and no double-offset occurs.
