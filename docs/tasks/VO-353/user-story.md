# VO-353: Support CSV import in watchlist management

## User Story

# VO-400: CSV Import for Watchlist Management

## User Story

As a **power user managing a watchlist**, I want to **import a CSV file of ticker symbols into my watchlist**, so that I can **bulk-add stocks without manual entry and migrate seamlessly from other tools like Excel or Bloomberg exports**.

---

## Acceptance Criteria

**Happy Path**
- User can upload a `.csv` file from the watchlist management UI
- System accepts CSVs with at least a `symbol` column (case-insensitive header matching)
- Successfully imported symbols are added to the active watchlist
- Duplicate symbols (already in watchlist) are skipped silently, not errored
- A summary is shown post-import: "X added, Y skipped (duplicates), Z skipped (invalid)"

**Validation**
- Invalid/unrecognized ticker symbols are skipped with a warning (not a hard failure)
- File size capped at 1MB; rows capped at 500 symbols
- Unsupported file types (`.xlsx`, `.txt`) return a clear error message
- Empty files or CSVs with no valid symbols return a user-facing error

**Edge Cases**
- Handles extra columns gracefully (only `symbol` column is consumed)
- Strips whitespace and normalizes symbols to uppercase
- Import is atomic per-row (one bad row doesn't block the rest)

---

## Priority Reasoning

**Medium-High.** Watchlist management is a core daily workflow. Users migrating from Bloomberg, Schwab, or their own spreadsheets face a painful manual re-entry problem. This unlocks a meaningful onboarding and retention lever with relatively low backend complexity. Theo's instinct here is sound — it's a table-stakes feature for pro users.

---

## Complexity: 3 / 5

- Frontend: file input UI + result summary modal (~1)
- Backend: CSV parsing, validation, dedup logic (~1.5)
- Symbol validation against known instruments adds the bulk of complexity (~0.5)
- No schema changes needed if watchlist table already exists (~0)
