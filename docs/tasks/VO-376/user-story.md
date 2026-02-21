# VO-376: Stale cache in SSE event streaming shows outdated data

## User Story

Now I have enough context. The SSE stream queues events to live clients only — no snapshot on connect, and data feeding SSE events (sentiment, AI ratings) is sourced from caches with significant TTLs. Here's the user story:

---

## VO-375: Stale cache in SSE event streaming shows outdated data

### User Story

**As a** trader watching the live dashboard,
**I want** the SSE event stream to deliver data that reflects current market conditions,
**so that** I can act on accurate, timely signals rather than decisions based on stale cached values.

---

### Acceptance Criteria

- [ ] SSE events sourced from the sentiment cache (`sentiment_cache` table, 15-min TTL) must not broadcast values older than TTL without indicating staleness — either force-refresh before dispatch or include a `cached_at` timestamp in the payload
- [ ] When a new client connects to `/api/stream`, they receive a snapshot event containing current state (active alerts, last regime, last technical signal) — not just a bare heartbeat
- [ ] If a scheduled job fires an SSE event (`technical_alerts`, `regime_update`) using data from a DB-cached result, the cache is validated against TTL before the payload is built; stale cache triggers a recompute, not a broadcast of old values
- [ ] AI ratings cache (`ai_ratings` table) sourced into any SSE payload must be treated the same way — stale entries recomputed or marked with age
- [ ] No breaking changes to the SSE frame format or event type allowlist
- [ ] Unit tests cover: (a) a new client gets a snapshot event, (b) stale cache triggers recompute before SSE dispatch, (c) payload includes `cached_at` or equivalent field for cached-source events

---

### Priority Reasoning

**Medium-High.** This is a data integrity issue in the core real-time feed. Traders making decisions on `regime_update` or `technical_alerts` events could be acting on 15-minute-old data without knowing it. Not a security hole, but directly undermines the platform's value proposition. Fix before next release; doesn't block current VO-374 work.

---

### Estimated Complexity

**3 / 5** — Two sub-problems: (1) snapshot-on-connect requires reading current state at connection time across multiple tables — moderate DB coordination. (2) TTL enforcement before SSE dispatch requires touching each job that emits events, ensuring they validate cache age. No schema changes needed. Risk is in identifying every SSE emission point and ensuring consistent TTL handling without introducing latency spikes on high-traffic paths.
