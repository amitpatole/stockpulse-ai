# VO-353: Support CSV import in watchlist management

## Technical Design

Now I have enough context to write an accurate, grounded spec.

---

## Technical Design Spec: VO-353 — CSV Import for Watchlist Management

### 1. Approach

Add a `POST /api/watchlist/<id>/import` endpoint to the existing `watchlist.py` blueprint that accepts a multipart CSV upload, parses the `symbol` column, normalizes and validates each ticker against the `stocks` table, and calls the existing `add_stock_to_watchlist()` manager function row-by-row. A `WatchlistImportModal` component handles file selection, upload, and displays the import summary; an "Import CSV" button is added to `StockGrid`'s toolbar. No schema changes are required.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/api/watchlist.py` — add `POST /<int:watchlist_id>/import` route
- **MODIFY**: `backend/app.py` — register missing `watchlist_bp` in `blueprint_map` (line ~325)
- **CREATE**: `frontend/src/components/dashboard/WatchlistImportModal.tsx`
- **MODIFY**: `frontend/src/components/dashboard/StockGrid.tsx` — add "Import CSV" button and import modal state
- **MODIFY**: `frontend/src/lib/api.ts` — add `importWatchlistCsv()` function
- **MODIFY**: `frontend/src/lib/types.ts` — add `WatchlistImportResult` type

---

### 3. Data Model

No new tables. Relies on existing:
- `watchlists(id, name, created_at)`
- `watchlist_stocks(watchlist_id, ticker)` — PRIMARY KEY `(watchlist_id, ticker)` enforces dedup at DB level
- `stocks(ticker)` — used for symbol validation

---

### 4. API Spec

**`POST /api/watchlist/<int:watchlist_id>/import`**

- **File size guard (pre-read):** The size limit relies on Flask's `MAX_CONTENT_LENGTH` app-level config (set to 1 MB). Flask rejects oversized uploads and returns `413` before the body is read into application memory, based on the `Content-Length` request header. Do not implement a post-read byte-count check — a malicious multi-hundred-MB upload would exhaust memory before such a check could fire.
- **Ownership validation:** Before processing the upload, verify that the authenticated user owns (or has write access to) the target watchlist. Query `watchlists` filtered by both `id = watchlist_id` AND the current user's identity. If the watchlist exists but belongs to a different user, return `403 Forbidden`. Return `404 Not Found` only when no watchlist with that `id` exists at all.
- Request: `multipart/form-data` with field `file` (`.csv`, max 1 MB enforced via `MAX_CONTENT_LENGTH`)
- **CSV encoding:** Decode the uploaded file as UTF-8 (using `errors='replace'`). If the result cannot be parsed as valid CSV, return `400 Bad Request`.
- Validates: file extension `.csv`, size ≤ 1 MB (pre-read via `MAX_CONTENT_LENGTH`), row count ≤ 500
- Parses: finds first case-insensitive `symbol` header; strips whitespace; uppercases values
- **CSV injection prevention:** Reject any symbol value whose first character is `=`, `+`, `-`, or `@`. These prefixes are interpreted as formula expressions by spreadsheet applications (Excel, Google Sheets, LibreOffice Calc) and can execute arbitrary commands if the watchlist is later exported to CSV. Rejected values are counted in `skipped_invalid` and included in `invalid_symbols`.
- Validates each symbol: `SELECT 1 FROM stocks WHERE ticker = ?` — unknown → skipped_invalid
- Inserts via `add_stock_to_watchlist()`; catches `IntegrityError` (PRIMARY KEY) → skipped_duplicates

**Success `200`:**
```json
{
  "added": 12,
  "skipped_duplicates": 3,
  "skipped_invalid": 1,
  "invalid_symbols": ["FOOBAR"]
}
```
**Errors:**
- `400` — bad file type, empty file, no symbol column, or undecodable content
- `403` — authenticated user does not own the target watchlist
- `404` — watchlist not found
- `413` — file exceeds `MAX_CONTENT_LENGTH`; returned by Flask before the body is read

---

### 5. Frontend Component Spec

**Component:** `WatchlistImportModal` — `frontend/src/components/dashboard/WatchlistImportModal.tsx`

| UI Element | Data Source |
|---|---|
| File drop zone / `<input type="file" accept=".csv">` | local state |
| "Import" submit button | triggers `importWatchlistCsv(watchlistId, file)` |
| Result summary line | `"12 added, 3 duplicates skipped, 1 invalid"` from `WatchlistImportResult` |
| Invalid symbols list | `result.invalid_symbols[]` shown as inline warning chips |
| Loading spinner | `isLoading` state during fetch |
| Error banner | API error message string |

**Renders from:** `StockGrid.tsx` — "Import CSV" button added next to existing "Add Stock" control; opens modal via `showImportModal` boolean state. On successful import, calls the existing `onRefresh` / stock-list refetch callback.

**`WatchlistImportResult` type** (`types.ts`):
```typescript
export interface WatchlistImportResult {
  added: number;
  skipped_duplicates: number;
  skipped_invalid: number;
  invalid_symbols: string[];
}
```

**`importWatchlistCsv`** (`api.ts`): sends `FormData` with `file`; returns `WatchlistImportResult`.

---

### 6. Verification

1. Upload a CSV with 5 valid tickers, 2 already in the watchlist, and 1 nonsense symbol (`ZZZZZ`) — confirm summary reads "5 added, 2 skipped (duplicates), 1 skipped (invalid)" and `ZZZZZ` appears in the invalid list.
2. Upload a `.xlsx` file — confirm a clear "Unsupported file type" error is shown without a server crash.
3. Upload a CSV with a `Symbol` header (mixed case) and leading/trailing whitespace around tickers — confirm symbols are normalized to uppercase and successfully added.
4. Upload a CSV containing a symbol starting with `=` (e.g., `=HYPERLINK("http://evil.example","click")`). Confirm it is rejected and appears in `invalid_symbols`; the watchlist is not modified for that row.
5. Attempt to import into a watchlist owned by a different user — confirm `403 Forbidden` is returned and no data is written.
6. Upload a file larger than 1 MB — confirm Flask returns `413` before any parsing code runs (verify via server logs that the route handler body was not entered).
