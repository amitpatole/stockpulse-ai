# VO-035: Fix code scanning: clear-text logging of sensitive data

## Technical Design

Now I have enough context. Let me write the technical design spec.

---

## Technical Design Spec: VO-035 — Prevent Clear-Text Logging of Sensitive Data

### Approach

The `_mask_key()` utility already exists in both `ai_providers.py` files (line 16). The problem is incomplete application: CodeQL traces `api_key` data flow through two vectors that currently land in logging sinks:

1. **URL construction** — `GoogleProvider` embeds the key directly in the request URL (`?key={self.api_key}`). If `requests.post()` raises, the exception message may include the full URL, and `logger.error(f"Google API error: {e}")` logs it verbatim.
2. **Exception propagation** — All four providers log `str(e)` in error handlers. HTTP library exceptions can include auth headers or request URLs in their string representation, exposing the key indirectly.
3. **Root-level files are actively in use** — `dashboard.py`, multiple `backend/agents/`, and even `backend/core/ai_analytics.py` import from the root-level files. They cannot be deleted; they need the same fixes as the `backend/core/` versions.
4. **`ai_analytics.py` line 477** — Safe (logs a static string). No fix needed; suppress with a `# nosec` annotation and comment.

### Files to Modify

| File | Change |
|---|---|
| `backend/core/ai_providers.py` | Fix Google URL construction; sanitize exception logging in all 4 providers |
| `ai_providers.py` (root) | Identical fix — files are in sync |
| `backend/core/ai_analytics.py` | Add `# nosec` + comment at line 477 |
| `ai_analytics.py` (root) | Same annotation at the equivalent line |
| `tests/test_ai_providers.py` | New file: unit tests for masking and safe logging |

### Data Model Changes

None.

### API Changes

None.

### Frontend Changes

None.

### Implementation Details

**Google URL construction** — Replace inline key interpolation with a `params` dict (requests handles query params separately from the URL string, keeping it out of exception messages):

```python
# Before
response = requests.post(f"{self.base_url}?key={self.api_key}", ...)

# After
response = requests.post(self.base_url, params={"key": self.api_key}, ...)
```

**Exception handlers** — Wrap `str(e)` to strip any token-shaped strings, or log only `type(e).__name__` at error level and gate the full message behind a safe scrubber. Simplest safe pattern: log the exception type, not its string representation, unless we can confirm the message is clean.

**`ai_analytics.py` line 477** — Annotate:
```python
logger.info("Generating summary using configured AI provider")  # nosec — no sensitive data logged
```

### Testing Strategy

New `tests/test_ai_providers.py`:

1. **`test_mask_key`** — parametrized unit test covering normal key, short key (`< 4` chars), and empty string.
2. **`test_google_provider_no_key_in_log`** — mock `requests.post` to raise a `ConnectionError`; capture log output with `pytest`'s `caplog`; assert `api_key` value does not appear in any log record.
3. **`test_all_providers_exception_no_key_in_log`** — same pattern for OpenAI, Anthropic, Grok.
4. **`test_grok_debug_log_masked`** — enable DEBUG level; assert log contains `...` prefix and only last 4 chars of the test key, not the full value.

All existing tests must continue to pass with no changes to behaviour — this fix is purely about what reaches the logging sink.
