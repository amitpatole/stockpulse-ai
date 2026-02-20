# VO-004: Research Brief Export (PDF & Markdown)

## Technical Design

---

### 1. Approach

Add a single new route to the existing `research.py` blueprint. For Markdown, return `content` directly with appropriate headers — no library needed. For PDF, use `reportlab` (pure Python, no system-level Cairo/Pango deps that would complicate Docker) to build a styled document with TickerPulse header, brief body, and metadata footer.

Frontend adds two action buttons per brief card in the existing detail-pane. "Copy as Markdown" uses the browser Clipboard API directly — no fetch required. "Download PDF" triggers a `fetch` to the export endpoint, receives the blob, and uses an ephemeral `<a>` to initiate the download. Per-brief loading state via `useState<number | null>` tracks which brief is in-flight.

No schema changes. All required fields (`content`, `agent_name`, `model_used`, `created_at`, `ticker`, `title`) already exist in `research_briefs`.

---

### 2. Files to Modify / Create

| Action | Path |
|---|---|
| **Modify** | `backend/api/research.py` — add `GET /api/research/briefs/<id>/export` route |
| **Modify** | `backend/requirements.txt` — add `reportlab>=4.0` |
| **Modify** | `frontend/src/app/research/page.tsx` — add export buttons + clipboard/download handlers |
| **Modify** | `frontend/src/lib/api.ts` — add `exportResearchBriefUrl(id, format)` helper |
| **Create** | `backend/tests/test_research_export.py` — backend export tests |

---

### 3. Data Model Changes

**None.** `research_briefs` already stores `content`, `agent_name`, `model_used`, `created_at`, `ticker`, and `title` — everything required for both export formats.

---

### 4. API Changes

**New endpoint:** `GET /api/research/briefs/<int:id>/export`

Query params: `format` — `md` or `pdf` (required; 400 otherwise)

| Format | Content-Type | Content-Disposition |
|---|---|---|
| `md` | `text/markdown` | `attachment; filename="<ticker>-brief-<id>.md"` |
| `pdf` | `application/pdf` | `attachment; filename="<ticker>-brief-<id>.pdf"` |

Error responses: `400 {"error": "format must be md or pdf"}`, `404 {"error": "Brief not found"}`.

PDF layout via `reportlab` (three sections): TickerPulse header bar with ticker + title, body text with heading styles parsed from Markdown `##` markers, footer line with `agent_name | model_used | created_at`.

Authentication follows the same pattern as existing `/api/research/` routes.

---

### 5. Frontend Changes

**`research/page.tsx`:** In the selected-brief detail pane (below the title/metadata row), add two `<button>` elements:

- **"Copy as Markdown"** — calls `navigator.clipboard.writeText(brief.content)`, then sets a `copied` state that shows a "Copied!" label for 2s. No fetch needed.
- **"Download PDF"** — sets `downloadingId` state to `brief.id`, fetches `/api/research/briefs/<id>/export?format=pdf`, creates a blob URL, clicks an ephemeral `<a download>`, then clears state. Button shows `<Loader2>` icon while in-flight.

Buttons use `lucide-react` icons (`Copy`, `Download`, `Loader2`) matching existing icon usage. Both have `aria-label` attributes for screen-reader accessibility and are keyboard-navigable as native `<button>` elements.

**`api.ts`:** Add `exportResearchBriefUrl(id: number, format: 'md' | 'pdf'): string` — a simple URL builder (not a fetch wrapper) used by the download handler.

---

### 6. Testing Strategy

**Backend (`test_research_export.py`):**
- Seed a row into in-memory SQLite; assert `?format=md` returns 200, correct `Content-Type`, brief content in body
- Assert `?format=pdf` returns 200, `application/pdf` content-type, non-empty bytes starting with `%PDF`
- Assert `?format=csv` returns 400 with error message
- Assert unknown `id` returns 404
- Assert PDF contains ticker and agent_name strings (parse with `pypdf`, already a dependency)

**Frontend (manual / Playwright):**
- "Copy as Markdown" → clipboard contains full `content` string; "Copied!" label appears then disappears
- "Download PDF" → file download dialog triggered; button enters and exits loading state
- Keyboard: Tab to button, Enter activates; aria-labels present in DOM
