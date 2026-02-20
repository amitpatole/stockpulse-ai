# VO-002: Add watchlist portfolio groups with CRUD

## User Story

# User Story: Watchlist Portfolio Groups

## User Story

As a **stock trader**, I want to organize my stocks into named watchlists, so that I can track different investment strategies or sectors without a cluttered, undifferentiated list.

---

## Acceptance Criteria

**Watchlist Management**
- [ ] A default watchlist named "My Watchlist" is auto-created for new and existing users
- [ ] Users can create a new watchlist via a "+ New Watchlist" button (requires a unique, non-empty name)
- [ ] Users can rename an existing watchlist inline
- [ ] Users can delete a watchlist (with confirmation prompt); stocks are not deleted globally
- [ ] Maximum of 20 watchlists per user

**Navigation**
- [ ] A dropdown or tab selector above `StockGrid` lets users switch between watchlists
- [ ] Active watchlist persists across page refresh (stored in localStorage or user session)
- [ ] Empty watchlist shows an empty state with a prompt to add stocks

**Stock Assignment**
- [ ] Users can add a stock to any watchlist (from search or existing list)
- [ ] Users can remove a stock from a watchlist without deleting it from others
- [ ] Users can drag a stock from one watchlist and drop it into another
- [ ] A stock can exist in multiple watchlists simultaneously

**API**
- [ ] `GET /api/watchlists` returns all watchlists with stock counts
- [ ] `POST /api/watchlists` creates a new watchlist
- [ ] `GET /PUT /DELETE /api/watchlists/<id>` reads, renames, or deletes a watchlist
- [ ] `POST /DELETE /api/watchlists/<id>/stocks` adds or removes a stock ticker

**Data Integrity**
- [ ] Deleting a watchlist does not affect stocks in other watchlists
- [ ] Junction table enforces no duplicate tickers per watchlist

---

## Priority Reasoning

**High priority.** The current flat list is a known retention friction point — power users managing multiple strategies abandon the product for tools that support organization. This is table-stakes functionality for anyone tracking more than ~10 tickers. Unblocks future features (portfolio performance comparison, alerts per watchlist).

---

## Estimated Complexity: **4 / 5**

| Area | Complexity Driver |
|---|---|
| Backend | New tables + 8 endpoints, migration safety for existing users |
| Frontend | Tab/dropdown UI, drag-and-drop between lists, empty states |
| Data | Junction table logic, default watchlist migration for existing data |
| Edge cases | Multi-list membership, delete cascades, name uniqueness |

Drag-and-drop alone adds ~1 point of complexity. If timeline is tight, ship without drag-and-drop as v1 — add it in a follow-up.
