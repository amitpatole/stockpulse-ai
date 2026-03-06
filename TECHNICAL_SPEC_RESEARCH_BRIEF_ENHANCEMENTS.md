# Technical Design Spec: Research Brief Enhancements
## Executive Summary, Key Metrics & PDF Export

**Status**: Design Phase
**Scope**: Add executive summary, key metrics display, and PDF export to research briefs
**Priority**: Medium
**Complexity**: Medium (backend exists, needs frontend integration)

---

## 1. Approach

**Three-phase integration strategy:**
1. **Backend API Enhancement**: Expand endpoint payloads to include executive summary and metrics
2. **Frontend Type Updates**: Extend TypeScript types with new fields
3. **UI Components**: Build metrics display card + PDF export button

---

## 2. Files to Modify/Create

### Backend (Python/Flask)
- **Modify**: `backend/api/research.py`
  - Update `list_briefs()` to include `executive_summary` in response
  - Ensure `GET /research/briefs/<id>` returns `executive_summary` + `metrics`
  - Verify `export_brief_pdf()` generates complete PDF with all sections

### Frontend (TypeScript/React)
- **Modify**: `frontend/src/lib/types.ts`
  - Extend `ResearchBrief` interface with: `executive_summary`, `has_metrics`, `created_at`
  - Add new `ResearchBriefDetail` type for full brief with metrics

- **Modify**: `frontend/src/lib/api.ts`
  - Add `getResearchBriefDetail(id)` function to fetch full brief
  - Add `exportBriefPDF(id)` function to trigger PDF download

- **Modify**: `frontend/src/app/research/page.tsx`
  - Update brief selection to load full detail (with metrics)
  - Add executive summary section display
  - Add metrics card component
  - Add PDF export button

- **Create**: `frontend/src/components/research/MetricsCard.tsx`
  - Display key metrics in visual grid
  - Show current price, RSI, sentiment, 7-day news count
  - Color-coded sentiment indicator (bullish/neutral/bearish)

---

## 3. Data Model Changes

### Database (Already Exists)
- `research_briefs`: Has `executive_summary` column ✓
- `research_brief_metadata`: Stores `key_metrics` (JSON), `key_insights` (JSON) ✓

**No schema changes needed** — fully backward compatible

---

## 4. API Changes

### GET /api/research/briefs (List)
**Updated Response:**
```json
{
  "data": [
    {
      "id": 1,
      "ticker": "AAPL",
      "title": "...",
      "content": "...",
      "executive_summary": "Apple shows strong technical setup...",
      "agent_name": "researcher",
      "model_used": "claude-sonnet-4-6",
      "has_metrics": true,
      "created_at": "2026-03-06T..."
    }
  ],
  "meta": { "total": 10, "limit": 25, "offset": 0, "has_next": false, "has_previous": false }
}
```

### GET /api/research/briefs/<id> (Detail)
**Already Correct** — returns full brief with metrics and summary
```json
{
  "data": {
    "id": 1,
    "ticker": "AAPL",
    "title": "...",
    "content": "...",
    "executive_summary": "...",
    "metrics": {
      "current_price": 195.50,
      "price_change_24h_pct": 1.25,
      "rsi": 65,
      "sentiment_label": "bullish",
      "news_count_7d": 12
    },
    "metric_sources": ["stocks", "ai_ratings", "news"]
  },
  "meta": {
    "has_pdf": true,
    "pdf_url": "/api/research/briefs/1/pdf/ticker-pulse-AAPL-20260306.pdf",
    "pdf_generated_at": "2026-03-06T..."
  }
}
```

### POST /api/research/briefs/<id>/export-pdf (Download)
**Already Correct** — generates and streams PDF file with executive summary and metrics

---

## 5. Frontend Changes

### Type Updates (`lib/types.ts`)
```typescript
export interface ResearchBrief {
  id: number;
  ticker: string;
  title: string;
  content: string;
  executive_summary?: string;  // NEW
  has_metrics?: boolean;        // NEW
  agent_name: string;
  created_at: string;
  model_used?: string;
}

export interface ResearchBriefMetrics {
  current_price?: number;
  price_change_24h_pct?: number;
  rsi?: number;
  sentiment_score?: number;
  sentiment_label?: string;
  technical_score?: number;
  fundamental_score?: number;
  news_count_7d?: number;
  recent_sentiment_avg?: number;
  metric_sources: string[];
}

export interface ResearchBriefDetail extends ResearchBrief {
  metrics: ResearchBriefMetrics;
}
```

### API Helpers (`lib/api.ts`)
```typescript
export async function getResearchBriefDetail(id: number): Promise<ResearchBriefDetail> {
  const res = await fetch(`/api/research/briefs/${id}`);
  // ...
  return res.data as ResearchBriefDetail;
}

export async function exportBriefPDF(id: number): Promise<void> {
  const res = await fetch(`/api/research/briefs/${id}/export-pdf`, { method: 'POST' });
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ticker-pulse-${id}.pdf`;
  a.click();
}
```

### UI Component: MetricsCard
```typescript
// frontend/src/components/research/MetricsCard.tsx
export default function MetricsCard({ metrics }: { metrics: ResearchBriefMetrics }) {
  return (
    <div className="grid grid-cols-2 gap-4 rounded-lg bg-slate-700/30 p-4">
      {/* Current Price */}
      {metrics.current_price && (
        <Metric label="Price" value={`$${metrics.current_price.toFixed(2)}`} />
      )}

      {/* 24H Change */}
      {metrics.price_change_24h_pct !== undefined && (
        <Metric
          label="24H Change"
          value={`${metrics.price_change_24h_pct:+.2f}%`}
          variant={metrics.price_change_24h_pct > 0 ? 'bullish' : 'bearish'}
        />
      )}

      {/* RSI */}
      {metrics.rsi && (
        <Metric label="RSI (14)" value={`${metrics.rsi.toFixed(1)}`} />
      )}

      {/* Sentiment */}
      {metrics.sentiment_label && (
        <Metric
          label="Sentiment"
          value={metrics.sentiment_label.capitalize()}
          variant={metrics.sentiment_label.toLowerCase()}
        />
      )}

      {/* News Count */}
      {metrics.news_count_7d && (
        <Metric label="News (7D)" value={`${metrics.news_count_7d}`} />
      )}
    </div>
  );
}
```

### Research Page Updates (`app/research/page.tsx`)
```typescript
export default function ResearchPage() {
  // ... existing code ...

  const [selectedBriefDetail, setSelectedBriefDetail] = useState<ResearchBriefDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load full detail when brief is selected
  const handleSelectBrief = async (brief: ResearchBrief) => {
    setSelectedBrief(brief);
    setDetailLoading(true);
    try {
      const detail = await getResearchBriefDetail(brief.id);
      setSelectedBriefDetail(detail);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if (!selectedBrief) return;
    try {
      await exportBriefPDF(selectedBrief.id);
      // Show toast: "PDF downloaded"
    } catch (err) {
      // Show error toast
    }
  };

  return (
    // ... existing toolbar ...
    {selectedBriefDetail && (
      <div>
        {/* Executive Summary Section */}
        {selectedBriefDetail.executive_summary && (
          <div className="rounded-lg bg-blue-500/10 border border-blue-500/30 p-4 mb-4">
            <h3 className="font-semibold text-blue-400 text-sm mb-2">Executive Summary</h3>
            <p className="text-sm text-slate-300">{selectedBriefDetail.executive_summary}</p>
          </div>
        )}

        {/* Metrics Card */}
        {selectedBriefDetail.metrics && (
          <MetricsCard metrics={selectedBriefDetail.metrics} />
        )}

        {/* PDF Export Button */}
        <button onClick={handleExportPDF} className="mt-4 flex items-center gap-2 ...">
          <Download className="h-4 w-4" />
          Export PDF
        </button>

        {/* Research Content */}
        <MarkdownContent content={selectedBriefDetail.content} />
      </div>
    )}
  );
}
```

---

## 6. Testing Strategy

### Unit Tests
- **MetricsCard component**: Render different metric combinations, sentiment colors
- **API helpers**: Mock fetch calls for detail endpoint and PDF export
- **Type safety**: Verify TypeScript compilation with new types

### Integration Tests
- **E2E flow**: Select brief → Load detail → Show executive summary → Show metrics → Export PDF
- **Fallback handling**: Brief without executive_summary or metrics (graceful degradation)
- **PDF download**: Verify correct blob generation and filename

### Test Files
- `frontend/src/components/research/__tests__/MetricsCard.test.tsx` (new)
- Update `frontend/src/__tests__/research.test.tsx` with detail endpoint tests
- Add E2E test: `e2e/research-briefs.spec.ts` (new)

---

## 7. Implementation Checklist

- [ ] **Backend API**: Verify list endpoint returns executive_summary
- [ ] **Types**: Add ResearchBriefDetail, ResearchBriefMetrics interfaces
- [ ] **API Helpers**: Create getResearchBriefDetail, exportBriefPDF functions
- [ ] **MetricsCard Component**: Build with visual metrics grid
- [ ] **Research Page**: Integrate executive summary + metrics + PDF button
- [ ] **Unit Tests**: 15+ tests for components and API
- [ ] **E2E Tests**: Full user workflow tests
- [ ] **Manual QA**: Test in Electron app, verify PDF quality
- [ ] **Documentation**: Update research briefs feature doc

---

## 8. Performance Considerations

- **Caching**: Metrics cached 5min via existing endpoint (line 213 in research.py)
- **Lazy Loading**: Load full detail only when brief is selected
- **PDF Generation**: Async on-demand (not pre-generated)
- **No N+1 Queries**: Single query per brief detail via optimized endpoint

---

## 9. Rollout

**Phase 1**: Deploy API changes (backward compatible)
**Phase 2**: Deploy frontend type + component updates
**Phase 3**: Roll out UI to users with feature flag (optional)

**Rollback**: Simple revert of frontend components; API changes have no breaking impact

---

## 10. Acceptance Criteria

- ✅ Executive summary displays when available
- ✅ Key metrics show in visual grid format
- ✅ PDF export downloads with proper filename
- ✅ Graceful fallback when data missing
- ✅ No performance regression (<500ms load time)
- ✅ All tests pass (unit + E2E)
- ✅ Accessibility: WCAG AA compliant
