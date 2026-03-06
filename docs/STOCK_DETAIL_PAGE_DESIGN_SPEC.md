# Technical Design Spec: Stock Detail Page

**Date**: 2026-03-06
**Status**: Design Phase
**Acceptance Criteria**: 7 defined below

---

## 1. Approach

Create a comprehensive single-stock view accessed from dashboard stock cards. The page will:
- Display real-time price + historical charts (1d, 5d, 1mo, 3mo, 1y, 5y)
- Show AI ratings, sentiment analysis, and technical indicators
- Render paginated news feed and research briefs for the ticker
- Provide quick actions: add/remove watchlist, generate research, ask AI
- Stream real-time updates via WebSocket when available (fallback to polling)

**Architecture Pattern**: Server-rendered page component with client-side interactivity, utilizing existing API endpoints where possible and adding lightweight aggregation endpoints where needed.

---

## 2. Files to Modify/Create

### Backend (Python/Flask)

**New Files:**
- `backend/api/stock_detail.py` - New Blueprint with stock detail endpoints

**Modified Files:**
- `backend/app.py` - Register new Blueprint
- `backend/database.py` - Add index if needed for stock info queries

### Frontend (TypeScript/React)

**New Files:**
- `frontend/src/app/stocks/[ticker]/page.tsx` - Dynamic stock detail page
- `frontend/src/components/stock-detail/PriceHeader.tsx` - Current price + key stats
- `frontend/src/components/stock-detail/ChartPanel.tsx` - OHLCV charts with period selector
- `frontend/src/components/stock-detail/AnalysisPanel.tsx` - AI ratings, technical scores
- `frontend/src/components/stock-detail/NewsPanel.tsx` - Paginated news articles
- `frontend/src/components/stock-detail/ResearchPanel.tsx` - Research briefs + generation
- `frontend/src/components/stock-detail/ActionButtons.tsx` - Watchlist, generate, chat actions

**Modified Files:**
- `frontend/src/components/dashboard/StockGrid.tsx` - Add click handler linking to detail page

### Tests

**New Files:**
- `backend/tests/test_api_stock_detail.py` - Stock detail endpoint tests
- `e2e/stock-detail.spec.ts` - E2E tests for stock detail workflows

---

## 3. Data Model Changes

**No new tables required.** Reuse existing:
- `stocks` - Ticker, company name, market
- `ai_ratings` - Rating, score, confidence, component scores
- `chart_data` - OHLCV historical prices (if separate table) OR fetch via Yahoo Finance API
- `news` - Articles with sentiment scores
- `research_briefs` - Generated analysis

**New Database Index** (if not already present):
```sql
-- Optimize stock info lookups for detail page
CREATE INDEX IF NOT EXISTS idx_stocks_ticker_market
ON stocks(ticker, market);
```

---

## 4. API Changes

### New Endpoint: `GET /api/stock/<ticker>/detail`

Aggregated endpoint combining multiple data sources into a single response.

**Request:**
```
GET /api/stock/AAPL/detail?period=1mo&news_limit=5&research_limit=3
```

**Response:** (200 OK)
```json
{
  "success": true,
  "data": {
    "stock": {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "market": "US",
      "active": true
    },
    "current_price": {
      "price": 215.45,
      "currency": "$",
      "change": 2.15,
      "change_percent": 1.01,
      "timestamp": "2026-03-06T16:00:00Z"
    },
    "ai_rating": {
      "rating": "BUY",
      "score": 8.5,
      "confidence": 0.92,
      "rsi": 65.3,
      "sentiment_score": 0.75,
      "technical_score": 0.8,
      "fundamental_score": 0.85
    },
    "chart": {
      "period": "1mo",
      "data": [{ "date": "...", "open": 210, "close": 215.45, ... }],
      "stats": { "min": 208, "max": 218, "avg": 212.5 }
    },
    "news": [
      {
        "id": 1,
        "title": "Apple Reports Q4 Results",
        "source": "Reuters",
        "published_date": "2026-03-05",
        "sentiment_label": "positive",
        "sentiment_score": 0.85
      }
    ],
    "research_briefs": [
      {
        "id": 1,
        "title": "Technical Analysis Update",
        "agent_name": "sentiment_analyst",
        "created_at": "2026-03-06T10:00:00Z"
      }
    ]
  }
}
```

**Query Parameters:**
- `period` (str, optional): Chart period (1d, 5d, 1mo, 3mo, 1y, 5y). Default: 1mo
- `news_limit` (int, optional): Max news items. Default: 5, Max: 20
- `research_limit` (int, optional): Max research briefs. Default: 3, Max: 10

**Errors:**
- 404: Ticker not found in watchlist
- 422: Invalid period or limits

---

## 5. Frontend Changes

### New Route: `/stocks/[ticker]`

Next.js dynamic route using App Router (replaces `[id]` patterns from legacy code).

**Page Component** (`frontend/src/app/stocks/[ticker]/page.tsx`):
- Fetch stock detail via `/api/stock/<ticker>/detail`
- Render layout with header, chart, analysis, news, research sections
- Handle loading/error states
- Integrate WebSocket for real-time price updates

**New Components:**

1. **PriceHeader** - Displays current price, change %, market cap indicator
2. **ChartPanel** - TradingView Lightweight Charts or similar, with period selector (1d/5d/1mo/3mo/1y/5y)
3. **AnalysisPanel** - Grid showing: AI Rating, RSI, Sentiment score, Technical/Fundamental/Sentiment breakdown
4. **NewsPanel** - Paginated list with filters (All/Positive/Negative), published_date descending
5. **ResearchPanel** - List of briefs by agent, with "Generate" button
6. **ActionButtons** - Add/Remove watchlist, Generate research, Chat with AI

**State Management:**
- React hooks (useState) for: selectedPeriod, currentPrice, chartData
- useEffect for: fetching detail data, WebSocket subscription
- useWebSocket hook for real-time price stream

**Navigation:**
- Update `StockGrid.tsx` to link stock cards to `/stocks/[ticker]`
- Add breadcrumb: Dashboard > AAPL in header

---

## 6. Testing Strategy

### Unit Tests (`backend/tests/test_api_stock_detail.py`)

- **Happy path**: GET /api/stock/AAPL/detail returns 200 with all fields
- **Missing ticker**: GET /api/stock/UNKNOWN/detail returns 404
- **Invalid period**: GET /api/stock/AAPL/detail?period=invalid returns 422
- **News limit boundary**: news_limit=0 returns empty array, news_limit=100 returns max 20
- **Aggregation**: Verify chart, news, briefs, rating are all included in response
- **Caching**: Verify responses are cached and reused (not re-fetched on every call)

### E2E Tests (`e2e/stock-detail.spec.ts`)

- **Navigation**: Click stock card on dashboard → navigates to /stocks/AAPL
- **Chart interaction**: Switch period selector (1d → 1mo → 1y) updates chart
- **Price streaming**: Real-time price updates via WebSocket when available
- **News pagination**: Scroll news feed → loads more articles
- **Research generation**: Click "Generate" button → calls API, shows loading state, displays result
- **Watchlist toggle**: Add/remove stock → updates watchlist, reflects on detail page
- **Responsive**: Page renders correctly on mobile (1 column), tablet, desktop (multi-column)

### Acceptance Criteria

| AC | Test Type | Requirement |
|----|-----------|-------------|
| AC1 | Unit | Stock detail page loads chart, news, ratings, briefs for selected ticker |
| AC2 | E2E | Chart displays with selectable time periods (1d/5d/1mo/3mo/1y/5y) |
| AC3 | E2E | Real-time price updates stream via WebSocket (<500ms latency) |
| AC4 | E2E | News feed paginates with 5 items per page, sentiment filter available |
| AC5 | Unit | AI ratings and technical analysis displayed with confidence scores |
| AC6 | E2E | User can generate new research brief via one-click button |
| AC7 | E2E | Stock can be added/removed from watchlist from detail page |

---

## 7. Performance Considerations

- **Index Usage**: Queries on ticker + market benefit from existing `idx_stocks_ticker_market`
- **Query Aggregation**: Single `/api/stock/<ticker>/detail` call reduces N+1 risk; backend batches news/briefs/ratings queries
- **Caching**: Cache aggregated detail response for 5 min (TTL) to avoid repeated fetches
- **Chart Data**: Lazy-load historical data only when period changes; cache per (ticker, period) pair
- **WebSocket**: Use existing WebSocket price stream from `backend/websocket/` module

---

## 8. Security & Validation

- **Input Validation**: Validate ticker format (alphanumeric + dots), period values against whitelist
- **Rate Limiting**: Apply 60 req/min per IP to `/api/stock/<ticker>/detail` to prevent scraping
- **XSS Prevention**: Sanitize news titles, research content using existing escaping
- **CSRF**: Include CSRF token on state-changing actions (Add/Remove watchlist, Generate research)

---

## 9. Rollout Strategy

1. **Phase 1**: Implement `/api/stock/<ticker>/detail` aggregation endpoint with tests
2. **Phase 2**: Build page components + integrate with existing APIs
3. **Phase 3**: Add WebSocket real-time integration
4. **Phase 4**: E2E tests + performance tuning
5. **Phase 5**: Merge to main with documentation

---

## 10. Documentation Updates Required

- Add `documentation/STOCK_DETAIL_PAGE.md` following CLAUDE.md template
- Update `docs/API_ENDPOINTS.md` with new endpoint
- Document WebSocket usage in existing WebSocket guide
