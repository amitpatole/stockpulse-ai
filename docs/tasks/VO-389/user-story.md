# VO-389: Stale cache in stock detail page shows outdated data

## User Story

# VO-350: Stale Cache in Stock Detail Page

---

## User Story

**As a** trader using the stock detail page,
**I want** the displayed stock data to always reflect the latest available information,
**so that** I can make informed decisions without acting on outdated prices, metrics, or sentiment data.

---

## Acceptance Criteria

- [ ] Stock detail page data refreshes within the expected cache TTL (no stale data served beyond TTL)
- [ ] Cache is invalidated/updated when underlying data changes (price, fundamentals, sentiment)
- [ ] Stale cache does not persist across page navigations or hard refreshes
- [ ] If cache miss occurs, fresh data is fetched and cached correctly — no race condition between concurrent requests serving stale state
- [ ] Cache key is scoped correctly per ticker symbol (no cross-ticker contamination)
- [ ] Relevant SSE/push events trigger cache invalidation where applicable
- [ ] No regression on page load performance — cache still serves requests efficiently

---

## Priority Reasoning

**Priority: High**

This is a data integrity bug on a core feature. Traders acting on stale stock data face real financial decision risk. QA already caught this — it will be caught by users in production too. Fixes that touch cache invalidation also carry regression risk, so we want this resolved and tested before it ships.

---

## Estimated Complexity

**3 / 5**

Cache invalidation bugs are classically subtle. The fix itself may be small, but we need to audit the cache layer, confirm TTL behavior, handle concurrent request edge cases (similar pattern to VO-344 scheduler stale cache), and write regression tests. Not a one-liner.

---

**Assign to:** Backend engineer familiar with the cache/scheduler layer.
**Ref:** Mirrors root cause patterns from VO-344 — check `_extract_trigger_args`-style stale-read patterns in the stock detail data pipeline.
