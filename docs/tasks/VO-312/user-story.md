# VO-312: Support social sentiment badge in stock detail page

## User Story

# User Story: Social Sentiment Badge — Stock Detail Page

---

## User Story

**As a** retail trader viewing a stock detail page,
**I want** to see a real-time social sentiment badge (bullish/bearish/neutral) aggregated from social media and news signals,
**so that** I can quickly gauge market sentiment without leaving the platform or manually scanning external sources.

---

## Acceptance Criteria

- [ ] A sentiment badge is displayed prominently on the stock detail page (near price/ticker header)
- [ ] Badge shows one of three states: **Bullish**, **Bearish**, or **Neutral** with distinct color coding (green/red/grey)
- [ ] Badge includes a sentiment score (e.g., 72% bullish) derived from aggregated signals
- [ ] Sentiment data refreshes automatically — max 15-minute staleness
- [ ] Hovering/tapping the badge reveals a breakdown: source count, signal sources (Reddit, Twitter/X, news), and timestamp of last update
- [ ] If sentiment data is unavailable, badge displays a graceful "No data" state — no crash, no spinner loop
- [ ] Sentiment is stock-specific (ticker-scoped), not market-wide
- [ ] Backend endpoint returns sentiment payload; frontend renders it — clean separation

---

## Priority Reasoning

**Medium-High.** Sentiment data is a differentiator for retail traders who already consume this informally. Surfacing it natively increases session depth and positions Virtual Office as a full-context research tool, not just a data viewer. Low switching cost for users already checking Reddit/Twitter manually — this removes friction directly.

---

## Estimated Complexity

**3 / 5**

- Backend: New sentiment aggregation service or third-party API integration (moderate effort)
- Frontend: Badge component + tooltip UI (low effort)
- Data freshness/caching: Requires cache-invalidation strategy (moderate effort)
- Risk: Third-party API reliability and rate limits need evaluation before committing to a source

---

**Next step:** Engineering spike to evaluate sentiment data sources (Reddit API, Stocktwits, news NLP). Spike output should confirm data source, latency, and cost before full implementation begins.
