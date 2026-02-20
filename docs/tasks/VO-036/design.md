# VO-036: Fix XSS Vulnerabilities in Dashboard Templates

## Technical Design Spec

---

### Approach

Surgical DOM construction rewrites at 4 known locations. All four vulnerabilities follow the same root cause: dynamic string data concatenated into `innerHTML` or template literals that feed `innerHTML`, with no HTML escaping. None of these locations require actual HTML rendering — every insertion is plain text or a fixed-structure component. The fix strategy is therefore:

- **Replace `innerHTML` string concatenation with `createElement` + `textContent`** for all four sites. This eliminates XSS at the DOM level without introducing a new sanitization library dependency.
- **Replace inline `onclick` attribute string-building** in `searchStocks` with `addEventListener`, which removes the secondary attack surface (attribute injection).
- **No DOMPurify needed** — no site genuinely requires untrusted HTML rendering. If rich text is added later, that decision should introduce DOMPurify at that point with a strict allowlist.

---

### Files to Modify

| File | Lines | Function | Change |
|---|---|---|---|
| `templates/dashboard.html` | 1924 | `loadStockAIAnalysis` | Replace `innerHTML` spinner string (with `ticker` concatenated) with `createElement` + `textContent` |
| `templates/dashboard.html` | 1798–1809 | `searchStocks` | Replace template-literal `innerHTML` block (incomplete `replace(/'/g, "\\'")`  sanitization + unescaped `stock.*` fields) with DOM-constructed result items using `textContent` and `addEventListener` |
| `templates/dashboard.html` | 2738–2745 | `addChatMessage` | Replace `innerHTML = contentHTML` (where `text` is embedded raw) with `createElement` + `textContent` for the message body; create AI badge element separately |
| `electron/wizard/wizard.js` | 195–203 | `buildSummary` | Replace `grid.innerHTML = items.map(...)` template literal (with `item.value` unescaped) with a loop that creates `.summary-item` elements via `createElement` + `textContent` |

No new files created.

---

### Data Model Changes

None.

---

### API Changes

None. All fixes are client-side rendering changes only. API responses and payloads are unchanged.

---

### Frontend Changes

Four localized rewrites, all within existing functions:

**`loadStockAIAnalysis` (dashboard.html:1924)**
```js
// Before
container.innerHTML = '<div class="loading-spinner">Analyzing ' + ticker + ' with AI...</div>';
// After
const spinner = document.createElement('div');
spinner.className = 'loading-spinner';
spinner.textContent = `Analyzing ${ticker} with AI...`;
container.replaceChildren(spinner);
```

**`searchStocks` (dashboard.html:1798–1809)**
Replace `.map()` → `innerHTML` with a `DocumentFragment` loop. Each `stock.ticker`, `stock.name`, `stock.exchange`, `stock.type` assigned via `textContent`. The Add button wired with `addEventListener('click', () => addStock(stock.ticker, stock.name))` — no inline handler string.

**`addChatMessage` (dashboard.html:2738–2745)**
```js
const contentDiv = document.createElement('div');
contentDiv.className = 'chat-message-content';
if (sender === 'ai' && isPowered) {
    const badge = document.createElement('span');
    badge.className = 'ai-badge';
    badge.textContent = '🤖 AI';
    contentDiv.appendChild(badge);
}
contentDiv.appendChild(document.createTextNode(text));
messageDiv.appendChild(contentDiv);
```

**`buildSummary` (wizard.js:195–203)**
Replace the `innerHTML = items.map(...)` block with a loop that constructs `.summary-item` > `.label` + `.value` elements via `createElement` and assigns `textContent` on each leaf.

---

### Testing Strategy

**Manual smoke tests** (no new test infrastructure needed):
- In `searchStocks`: Enter a search query, inspect that results render correctly with real stock data. Verify the Add button still calls `addStock` correctly.
- In `addChatMessage`: Send a chat message and an AI response; confirm both render in the UI without escaping artifacts.
- In `loadStockAIAnalysis`: Select a stock from the AI selector; confirm the loading spinner appears and is replaced by results.
- In wizard `buildSummary`: Complete wizard setup and confirm summary step shows correct config values.

**XSS regression test** (manual):
Inject `<img src=x onerror="alert(1)">` as a ticker value, stock name (mock API response), chat message, and config value. Confirm the string renders as literal text, no alert fires.

**Static analysis**:
Re-run CodeQL on `templates/dashboard.html` and `electron/wizard/wizard.js` post-fix. Expect zero `js/xss-through-dom` and zero `js/incomplete-sanitization` alerts on the patched lines.

No new unit tests required — this is a rendering-layer change with no logic branching. The existing smoke test suite (if any) should pass unchanged.
