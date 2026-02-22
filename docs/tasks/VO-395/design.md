# VO-395: Edge case in stock detail page when input is empty

## Technical Design

---

## VO-362 Technical Design Spec: Empty Input Edge Case on Stock Detail Page

### 1. Approach

Add a client-side guard at the top of the stock detail page that redirects to home (with a toast) when the `ticker` param is empty or missing. Add inline validation to the ticker input submission path — both Enter key and button click — that blocks navigation and API calls when the field is blank or whitespace-only, focusing and highlighting the input instead.

### 2. Files to Create/Modify

- MODIFY: `frontend/src/app/stocks/[ticker]/page.tsx` (add empty param redirect guard)
- MODIFY: `frontend/src/components/dashboard/StockGrid.tsx` (inline validation on submit path)

### 3. Data Model

No database changes. No new tables or columns required.

### 4. API Spec

No new endpoints. Existing `GET /api/stocks/<ticker>/detail` already returns 404 for invalid tickers — this spec prevents the call from being made in the first place.

### 5. Frontend Component Spec

**`frontend/src/app/stocks/[ticker]/page.tsx`**

At the top of the component, after unwrapping `params`, add a guard:

```typescript
const { ticker } = use(params);
if (!ticker || !ticker.trim()) {
  // redirect to home with toast query param
  redirect('/?error=missing-ticker');
}
```

On the home page (`frontend/src/app/page.tsx`), read the `error` query param and surface a toast: _"No ticker specified. Please search for a stock."_ This keeps redirect logic server-safe and avoids client-only hooks at the page level.

**`frontend/src/components/dashboard/StockGrid.tsx`**

The `handleAddStock` / Enter-key submission path (lines ~90–105) currently calls `addStock()` immediately. Add a validation gate before that:

```typescript
if (!searchQuery.trim()) {
  setValidationError('Please enter a ticker symbol');
  inputRef.current?.focus();
  return; // no API call, no navigation
}
setValidationError(null);
```

- Render an inline `<p role="alert">` below the input when `validationError` is set, styled with a red border on the input (`ring-red-500`).
- Clear `validationError` on any non-empty `onChange`.
- This same guard covers both Enter keydown and any submit button click.

**Loading/Error States**: No change to existing loading/error states. The empty-input path never reaches the API, so no spinner or network error is possible.

### 6. Verification

1. **Direct URL access**: Navigate to `/stocks/` or `/stocks/%20` in the browser — confirm redirect to home and toast message _"No ticker specified"_ appears.
2. **Keyboard submission**: Focus the StockGrid search input, leave it blank, press Enter — confirm no API call fires (check Network tab), inline red error message appears, and input retains focus.
3. **Mouse submission**: Clear the input, click the search/add button — confirm identical behavior to keyboard path; no route change occurs.
