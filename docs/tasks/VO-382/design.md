# VO-382: Missing input validation in data provider fallback chain allows injection

## Technical Design

Now I have everything I need. Here is the technical design spec:

---

## Technical Design Spec: Input Validation — Data Provider Fallback Chain (VO-XXX)

---

### 1. Approach

Add a dedicated validator module mirroring the established pattern in `backend/api/validators/scheduler_validators.py`: regex/allowlist checks at the HTTP boundary, before any business logic runs. The two stub POST endpoints in `settings.py` accept `provider_id`, `api_key`, and `config` with no sanitization; we gate each field with explicit type checks, an enum allowlist, and length/character constraints that reject injection payloads. No changes to `DataProviderRegistry` or the fallback chain internals — all enforcement happens at the API layer.

---

### 2. Files to Create/Modify

- **CREATE**: `backend/api/validators/provider_validators.py`
- **MODIFY**: `backend/api/settings.py` (wire validators into `add_data_provider` and `test_data_provider`)
- **CREATE**: `backend/tests/test_provider_input_validation.py`

---

### 3. Data Model

No new tables or columns. The existing `data_providers_config` schema is unchanged. Validation fires before any read/write touches the DB.

---

### 4. API Spec

Both endpoints already exist; validation changes only the error responses for bad input.

**`POST /api/settings/data-provider`**
```
Request:  { "provider_id": str, "api_key": str (optional), "config": {} (optional) }
Success:  200 { "success": true, "message": "..." }
Error:    400 { "success": false, "error": "<field>: <reason>" }
```

**`POST /api/settings/data-provider/test`**
```
Request:  { "provider_id": str, "api_key": str (optional) }
Success:  200 { "success": true, "provider": str, "message": "..." }
Error:    400 { "success": false, "error": "<field>: <reason>" }
```

**Validation rules enforced (both endpoints):**

| Field | Rule |
|---|---|
| `provider_id` | Required. Must be one of: `yahoo_finance`, `alpha_vantage`, `finnhub`, `polygon`, `newsapi`. No other values accepted. |
| `api_key` | Optional. If present, must be a string, 8–512 characters, matching `^[A-Za-z0-9_\-]+$`. |
| `config` | Optional. If present, must be a dict. Keys must match `^[A-Za-z0-9_]{1,32}$`. Values must be str/int/bool (no nested objects). |

Any unknown top-level key in the request body returns 400.

---

### 5. Frontend Component Spec

No new frontend component is required for this fix. The validation is purely backend-side. Existing error responses (the `error` string in the 400 body) propagate naturally to whatever settings UI calls these endpoints — the field already exists in both stubs' response shape.

---

### 6. Verification

1. **Injection rejected**: `POST /api/settings/data-provider` with `{"provider_id": "yahoo_finance'; DROP TABLE data_providers_config;--"}` must return `400` with `"error"` containing `"provider_id"`. The body must not echo the payload or include a stack trace.

2. **Allowlist enforced**: `POST /api/settings/data-provider/test` with `{"provider_id": "../../etc/passwd"}` must return `400`. `{"provider_id": "polygon"}` (valid) must return `200`.

3. **Regression — valid config passes**: `POST /api/settings/data-provider` with `{"provider_id": "alpha_vantage", "api_key": "ABCD1234"}` must return `200 {"success": true}` unchanged from current behavior.
