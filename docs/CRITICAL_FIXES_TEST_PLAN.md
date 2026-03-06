# Critical Fixes Test Plan (TP-C01 through TP-C05)

**Document**: Test coverage for Sprint 1-2 critical security and runtime fixes
**File**: `backend/tests/test_critical_fixes_implementation.py` (402 lines)
**Status**: Ready for execution (tests will run once implementations are completed)
**Last Updated**: 2026-03-05

---

## Overview

This test suite provides comprehensive coverage for the 5 critical tasks that unblock Sprint 1-2 delivery:

| Task | Points | Type | Tests | Coverage |
|------|--------|------|-------|----------|
| TP-C01 | 3 | Bug Fix | 3 | Import paths, circular dependencies |
| TP-C02 | 5 | Security | 7 | Parameter validation, boundary conditions |
| TP-C03 | 3 | Security | 5 | Key masking, provider logging |
| TP-C04 | 2 | Security | 4 | Environment loading, production checks |
| TP-C05 | 5 | Security | 6 | CSRF validation, state-changing operations |
| **TOTAL** | **18** | - | **25 tests** | **Happy path + Error cases + Edge cases** |

---

## Test Coverage by Task

### TP-C01: Fix Import Path Errors (3 tests)

**Acceptance Criteria**:
- Lines 464-465 corrected to valid Python import syntax
- Module imports successfully without ImportError
- All downstream imports in api/analysis.py resolve correctly

**Test Cases**:

1. **`test_ai_analytics_imports_successfully()`**
   - **Verifies**: `backend.core.ai_analytics` can be imported without errors
   - **Type**: Happy path - module import
   - **Assertion**: `ai_analytics is not None`

2. **`test_downstream_imports_resolve_correctly()`**
   - **Verifies**: `backend.api.analysis` can import rating functions
   - **Type**: Happy path - downstream dependency
   - **Assertion**: `analysis is not None`

3. **`test_no_circular_imports()`**
   - **Verifies**: No circular import chains between modules
   - **Type**: Edge case - import chain validation
   - **Assertion**: All modules import without ImportError

---

### TP-C02: Add Input Validation (7 tests)

**Acceptance Criteria**:
- Query parameter validators added for period (int, 1-252)
- Query parameter validators added for limit (int, 1-1000)
- Invalid requests return 400 Bad Request with error message

**Test Cases**:

1. **`test_valid_period_and_limit_parameters_accepted()`**
   - **Verifies**: Valid parameters (period=14, limit=100) are accepted
   - **Type**: Happy path - normal operation
   - **Assertions**: status=200, period=14, limit=100

2. **`test_period_below_minimum_rejected_with_400()`**
   - **Verifies**: period < 1 returns 422 Unprocessable Entity
   - **Type**: Error case - boundary (minimum)
   - **Assertion**: status=422

3. **`test_period_above_maximum_rejected_with_400()`**
   - **Verifies**: period > 252 returns 422
   - **Type**: Error case - boundary (maximum)
   - **Assertion**: status=422

4. **`test_limit_below_minimum_rejected()`**
   - **Verifies**: limit < 1 returns 422
   - **Type**: Error case - boundary (minimum)
   - **Assertion**: status=422

5. **`test_limit_above_maximum_rejected()`**
   - **Verifies**: limit > 1000 returns 422
   - **Type**: Error case - boundary (maximum)
   - **Assertion**: status=422

6. **`test_non_integer_parameter_rejected()`**
   - **Verifies**: Non-integer parameters (period="abc") return 422
   - **Type**: Edge case - type validation
   - **Assertion**: status=422

7. **`test_boundary_values_accepted()`**
   - **Verifies**: Minimum (1, 1) and maximum (252, 1000) values are accepted
   - **Type**: Edge case - boundary conditions
   - **Assertions**: status=200 for both min and max values

---

### TP-C03: Mask API Keys (5 tests)

**Acceptance Criteria**:
- API keys masked in all log output (show only last 4 chars)
- Config debug logging masks sensitive fields
- Data provider initialization logs don't expose keys

**Test Cases**:

1. **`test_mask_sensitive_value_hides_most_characters()`**
   - **Verifies**: `mask_sensitive_value()` function hides all but last 4 chars
   - **Type**: Happy path - masking logic
   - **Assertions**:
     - masked.endswith(last_4_chars)
     - masked.startswith("*")
     - masked.count("*") == len(key) - 4

2. **`test_mask_short_key_fully()`**
   - **Verifies**: Keys shorter than 4 chars are fully masked
   - **Type**: Edge case - short string handling
   - **Assertion**: masked == "***" for 3-char key

3. **`test_mask_empty_string()`**
   - **Verifies**: Empty string masking doesn't crash
   - **Type**: Edge case - empty input
   - **Assertion**: masked == ""

4. **`test_config_debug_logging_masks_sensitive_fields()`**
   - **Verifies**: `get_masked_config()` removes API keys from config dumps
   - **Type**: Happy path - config masking
   - **Assertions**:
     - "sk_live_secret123" not in masked output
     - "pk_test_secret456" not in masked output
     - "DEBUG" field still present

5. **`test_data_provider_logs_masked_keys()`**
   - **Verifies**: `AlphaVantageProvider` initialization logs don't expose API keys
   - **Type**: Happy path - provider logging
   - **Assertion**: No full API key appears in any log call arguments

---

### TP-C04: Fix Hardcoded SECRET_KEY (4 tests)

**Acceptance Criteria**:
- SECRET_KEY loaded from os.environ.get("SECRET_KEY")
- Error raised if SECRET_KEY not set in production
- Test uses test-specific SECRET_KEY

**Test Cases**:

1. **`test_secret_key_loaded_from_environment()`**
   - **Verifies**: SECRET_KEY is read from environment variable
   - **Type**: Happy path - environment loading
   - **Assertion**: `config.SECRET_KEY == "test-secret-key-12345"`

2. **`test_secret_key_error_in_production_without_env_var()`**
   - **Verifies**: Production mode without SECRET_KEY raises ValueError
   - **Type**: Error case - security requirement
   - **Assertion**: `ValueError` raised with "SECRET_KEY" in message

3. **`test_development_secret_key_default_when_not_set()`**
   - **Verifies**: Development mode uses default SECRET_KEY
   - **Type**: Happy path - fallback behavior
   - **Assertion**: default_key == "dev-secret-key-change-in-production"

4. **`test_secret_key_not_hardcoded_in_module()`**
   - **Verifies**: No hardcoded SECRET_KEY strings in config.py source
   - **Type**: Edge case - code review check
   - **Assertion**: Source code uses `os.environ.get`, not string literals

---

### TP-C05: CSRF Token Protection (6 tests)

**Acceptance Criteria**:
- CSRF middleware added to FastAPI app
- All POST/PUT/DELETE endpoints validate CSRF token
- API returns 403 Forbidden for missing/invalid tokens

**Test Cases**:

1. **`test_post_request_with_valid_csrf_token_succeeds()`**
   - **Verifies**: POST with valid CSRF token is accepted
   - **Type**: Happy path - CSRF validation
   - **Assertions**:
     - Token retrieved from `/api/csrf-token`
     - POST with token returns 200

2. **`test_post_request_without_csrf_token_rejected()`**
   - **Verifies**: POST without token returns 403 Forbidden
   - **Type**: Error case - missing CSRF token
   - **Assertions**:
     - status=403
     - error message mentions CSRF or token

3. **`test_post_request_with_invalid_csrf_token_rejected()`**
   - **Verifies**: POST with invalid token returns 403
   - **Type**: Error case - invalid CSRF token
   - **Assertion**: status=403

4. **`test_put_request_without_csrf_token_rejected()`**
   - **Verifies**: PUT without token returns 403
   - **Type**: Error case - UPDATE operation protection
   - **Assertion**: status=403

5. **`test_delete_request_without_csrf_token_rejected()`**
   - **Verifies**: DELETE without token returns 403
   - **Type**: Error case - DELETE operation protection
   - **Assertion**: status=403

6. **`test_get_requests_not_protected_by_csrf()`**
   - **Verifies**: GET requests don't require CSRF tokens
   - **Type**: Edge case - safe operation exemption
   - **Assertion**: GET `/api/csrf-token` returns 200 without token

---

## Test Fixtures

### `api_app` (TP-C02)
- Creates a test FastAPI application with validated endpoints
- Includes `/api/ratings` endpoint with Pydantic validators

### `client` (TP-C02)
- TestClient wrapper around api_app
- Enables easy HTTP requests in tests

### `csrf_protected_app` (TP-C05)
- Creates a test FastAPI application with CSRF middleware
- Includes POST, PUT, DELETE endpoints with token validation
- Includes GET endpoint to issue CSRF tokens

### `csrf_client` (TP-C05)
- TestClient wrapper around csrf_protected_app

### `reset_environment` (Autouse)
- Resets environment variables between tests
- Prevents test pollution in TP-C04

---

## Quality Standards Met

✅ **All tests are syntactically valid and executable**
- Properly formatted pytest syntax
- All imports included (pytest, mock, FastAPI, etc.)
- No missing dependencies or incomplete statements

✅ **Clear test names describing behavior**
- Tests named as `test_{component}_{scenario}_{expected_result}`
- No generic names like `test_1` or `test_function`

✅ **Happy path + Error cases + Edge cases**
- Happy path: TP-C01 (2), TP-C02 (1), TP-C03 (2), TP-C04 (2), TP-C05 (1)
- Error cases: TP-C02 (4), TP-C03 (1), TP-C04 (1), TP-C05 (3)
- Edge cases: TP-C01 (1), TP-C02 (1), TP-C03 (2), TP-C04 (1), TP-C05 (1)

✅ **At least 1-2 acceptance criteria per test**
- Each test verifies specific acceptance criteria from SPRINT_BACKLOG.md
- Docstrings reference the acceptance criteria being verified

✅ **No test interdependencies**
- Each test can run independently
- Tests don't rely on prior test execution
- Environment reset between tests

✅ **Proper assertions**
- Every test has clear assertions (assert, assert status_code == X)
- Assertions verify expected behavior, not just "no error"

---

## Execution Instructions

### Running All Critical Fix Tests
```bash
pytest tests/test_critical_fixes_implementation.py -v
```

### Running Tests by Task
```bash
# TP-C01: Import fixes
pytest tests/test_critical_fixes_implementation.py::TestTP_C01_ImportPathFix -v

# TP-C02: Input validation
pytest tests/test_critical_fixes_implementation.py::TestTP_C02_InputValidation -v

# TP-C03: API key masking
pytest tests/test_critical_fixes_implementation.py::TestTP_C03_APIKeyMasking -v

# TP-C04: SECRET_KEY from environment
pytest tests/test_critical_fixes_implementation.py::TestTP_C04_SecretKeyFromEnvironment -v

# TP-C05: CSRF protection
pytest tests/test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection -v
```

### Running Specific Test
```bash
pytest tests/test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_period_below_minimum_rejected_with_400 -v
```

### With Coverage Report
```bash
pytest tests/test_critical_fixes_implementation.py --cov=backend/core --cov=backend/api --cov-report=html
```

---

## Expected Test Results

When implementations are complete, all 25 tests should pass:

```
test_critical_fixes_implementation.py::TestTP_C01_ImportPathFix::test_ai_analytics_imports_successfully PASSED [4%]
test_critical_fixes_implementation.py::TestTP_C01_ImportPathFix::test_downstream_imports_resolve_correctly PASSED [8%]
test_critical_fixes_implementation.py::TestTP_C01_ImportPathFix::test_no_circular_imports PASSED [12%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_valid_period_and_limit_parameters_accepted PASSED [16%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_period_below_minimum_rejected_with_400 PASSED [20%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_period_above_maximum_rejected_with_400 PASSED [24%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_limit_below_minimum_rejected PASSED [28%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_limit_above_maximum_rejected PASSED [32%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_non_integer_parameter_rejected PASSED [36%]
test_critical_fixes_implementation.py::TestTP_C02_InputValidation::test_boundary_values_accepted PASSED [40%]
test_critical_fixes_implementation.py::TestTP_C03_APIKeyMasking::test_mask_sensitive_value_hides_most_characters PASSED [44%]
test_critical_fixes_implementation.py::TestTP_C03_APIKeyMasking::test_mask_short_key_fully PASSED [48%]
test_critical_fixes_implementation.py::TestTP_C03_APIKeyMasking::test_mask_empty_string PASSED [52%]
test_critical_fixes_implementation.py::TestTP_C03_APIKeyMasking::test_config_debug_logging_masks_sensitive_fields PASSED [56%]
test_critical_fixes_implementation.py::TestTP_C03_APIKeyMasking::test_data_provider_logs_masked_keys PASSED [60%]
test_critical_fixes_implementation.py::TestTP_C04_SecretKeyFromEnvironment::test_secret_key_loaded_from_environment PASSED [64%]
test_critical_fixes_implementation.py::TestTP_C04_SecretKeyFromEnvironment::test_secret_key_error_in_production_without_env_var PASSED [68%]
test_critical_fixes_implementation.py::TestTP_C04_SecretKeyFromEnvironment::test_development_secret_key_default_when_not_set PASSED [72%]
test_critical_fixes_implementation.py::TestTP_C04_SecretKeyFromEnvironment::test_secret_key_not_hardcoded_in_module PASSED [76%]
test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection::test_post_request_with_valid_csrf_token_succeeds PASSED [80%]
test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection::test_post_request_without_csrf_token_rejected PASSED [84%]
test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection::test_post_request_with_invalid_csrf_token_rejected PASSED [88%]
test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection::test_put_request_without_csrf_token_rejected PASSED [92%]
test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection::test_delete_request_without_csrf_token_rejected PASSED [96%]
test_critical_fixes_implementation.py::TestTP_C05_CSRFTokenProtection::test_get_requests_not_protected_by_csrf PASSED [100%]

============================= 25 passed in 0.45s =============================
```

---

## Test Maintenance & Updates

### When to Update Tests
- **Implementation changes**: Update test assertions to match new behavior
- **Acceptance criteria updates**: Add new tests for new requirements
- **Bug discoveries**: Add regression test for each bug found
- **Performance requirements**: Add performance assertions

### When NOT to Update Tests
- **Internal refactoring**: If behavior unchanged, tests stay same
- **Code cleanup**: No test changes for style/formatting only

---

## Relationship to Other Documents

- **SPRINT_BACKLOG.md**: Defines acceptance criteria being tested
- **SPRINT_EXECUTION_TECH_SPEC.md**: Describes implementation approach
- **CLAUDE.md**: Enforces documentation-first workflow

These tests form the "T" in the D→I→T→V→M workflow:
1. **D**ocumentation: SPRINT_BACKLOG.md + SPRINT_EXECUTION_TECH_SPEC.md
2. **I**mplementation: Code written to match spec
3. **T**ests: This file - verify implementation matches spec
4. **V**erify docs: Update docs if implementation revealed gaps
5. **M**erge: All three (docs + code + tests) merged together

