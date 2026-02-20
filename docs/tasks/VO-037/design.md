# VO-037: Fix code scanning: XSS vulnerabilities in dashboard templates

## Technical Design

Here's a summary of the design spec written to `docs/tasks/VO-036/design.md`:

---

**Approach**: All 4 sites use the same root-cause pattern — dynamic text concatenated into `innerHTML`. Since none of them need actual HTML rendering (they're all plain text or fixed-structure components), the fix is DOM construction with `textContent` across the board. No DOMPurify dependency needed.

**The 4 fixes:**

| Site | Issue | Fix |
|---|---|---|
| `dashboard.html:1924` | `ticker` (user input) concatenated into loading spinner `innerHTML` | `createElement` + `textContent` |
| `dashboard.html:1805` | API fields (`stock.ticker`, `.name`, `.exchange`, `.type`) in template literal `innerHTML`; `replace(/'/g, "\\'")`  is incomplete | DOM fragment loop + `textContent` + `addEventListener` (no inline `onclick`) |
| `dashboard.html:2745` | Raw `text` parameter (from chat API/user) embedded in `innerHTML` | `createElement` + `createTextNode` for message body |
| `wizard.js:195` | Config values (`market_timezone`, budget fields) in template literal `innerHTML` | `createElement` loop + `textContent` on each leaf |

**Key architectural decision**: Rejecting DOMPurify here — it adds a dependency for a problem that doesn't require HTML rendering. If rich text ever lands (e.g. markdown in chat), that's the right time to introduce it with a strict allowlist config.
