# Technical Spec: Data Table Pagination

## Approach
Implement server-side pagination with limit/offset parameters to reduce data transfer and improve UX. Pagination state (page number/offset) lives in URL query parameters for shareable, bookmarkable views. Frontend shows **prev/next buttons** with disabled states at boundaries.

---

## Files to Modify/Create

### Backend
- **`backend/api/stocks.py`** - Add limit/offset to `/api/stocks` GET
- **`backend/api/research.py`** - Replace `limit` with limit/offset in `/api/research/briefs` GET
- **`backend/core/stock_manager.py`** - Modify `get_all_stocks()` to support offset

### Frontend
- **`frontend/src/components/dashboard/StockGrid.tsx`** - Add pagination controls
- **`frontend/src/app/research/page.tsx`** - Add pagination controls
- **`frontend/src/lib/api.ts`** - Update API client functions to accept limit/offset
- **`frontend/src/hooks/useApi.ts`** - No changes (pagination state in components, not hook)

---

## Data Model Changes
**None.** No new tables/columns. Pagination is query-level only.

---

## API Changes

### GET `/api/stocks`
**Query Params (NEW):**
- `limit` (int, optional, default=20, max=100): Records per page
- `offset` (int, optional, default=0): Skip N records
- `market` (str, optional): Existing filter

**Response:**
```json
{
  "data": [ /* stock objects */ ],
  "meta": {
    "limit": 20,
    "offset": 0,
    "total": 150,
    "has_next": true,
    "has_previous": false
  }
}
```

### GET `/api/research/briefs`
**Query Params (CHANGE):**
- `limit` (int, optional, default=25, max=100): Records per page (existing param, now enforced)
- `offset` (int, optional, default=0): Skip N records (NEW)
- `ticker` (str, optional): Existing filter

**Response:** Same metadata wrapper as `/api/stocks`

---

## Frontend Changes

### StockGrid.tsx
- Add local state: `page` (number), `limit` (20)
- Calculate `offset = (page - 1) * limit`
- Pass to `getRatings(limit, offset)` API call
- Render pagination buttons below grid:
  - **Previous** button (disabled if page === 1)
  - Page indicator: `Page {page} of {Math.ceil(total / limit)}`
  - **Next** button (disabled if `!has_next`)
- Derive total from API response metadata

### ResearchPage.tsx
- Same pattern as StockGrid
- Add state: `page` (number), `limit` (25)
- Update `getResearchBriefs(filterTicker, limit, offset)` call
- Pagination UI below briefs list

### lib/api.ts
```typescript
export async function getRatings(limit?: number, offset?: number): Promise<APIResponse>
export async function getResearchBriefs(ticker?: string, limit?: number, offset?: number): Promise<APIResponse>
```

---

## Testing Strategy

### Backend Unit Tests
- **test_pagination_limit_offset.py** (new file)
  - Test default limit/offset (20/0 for stocks, 25/0 for briefs)
  - Test custom limit/offset values
  - Test `limit > max` clamps to max (100)
  - Test `offset` beyond total (returns empty array)
  - Test `has_next` / `has_previous` flags
  - Test filter + pagination together (market + offset)

### Frontend Integration Tests
- **StockGrid.test.tsx** (extend existing)
  - User clicks next → page increments, data refetches
  - Previous button disabled on page 1
  - Next button disabled when `has_next=false`
  - URL query params update with offset
  - Boundary cases: single page, empty results

- **research.test.tsx** (extend existing)
  - Same pagination interaction tests
  - Filter + pagination (ticker + offset together)

### E2E Tests
- **pagination.spec.ts** (new Playwright test)
  - Navigate stocks table → click next → verify new rows load
  - Navigate research briefs → click prev → verify correct rows
  - Verify URL state persists on refresh

---

## Acceptance Criteria
- ✅ All rows fit on page (no scrolling within table)
- ✅ Prev/next buttons manage navigation
- ✅ Performance: Payloads < 100KB
- ✅ URL query params track pagination state
- ✅ Metadata shows total count and has_next/has_previous
- ✅ All tests pass
