# Technical Design Spec: Settings Save Functionality Fix

**Status**: Design Phase
**Priority**: High (Audit Finding)
**Complexity**: Medium
**Estimated Effort**: 8-16 hours

---

## 🎯 Problem Statement

Settings form submissions are non-functional. Users can configure AI providers, select agent frameworks, and set budget limits, but changes are silently discarded with no user feedback. Root causes:

1. **API Provider Card uses raw fetch()** instead of centralized API client
2. **Inconsistent error handling** across three settings sections (Providers, Framework, Budget)
3. **No error feedback to users** when saves fail (toasts exist but aren't wired correctly in Provider card)
4. **No persistence verification** - settings may not be saved even after success responses

---

## 🛠️ Implementation Approach

### Phase 1: Consolidate API Client
- Replace direct `fetch()` calls in ProviderCard with centralized API functions
- Add missing `testAIProvider()` wrapper to api.ts (currently direct fetch in component)
- Ensure all requests go through `request()` function for consistent error handling

### Phase 2: Fix Error Handling
- Ensure `saveBudgetSettings()` and `setAgentFramework()` properly throw errors on failure
- Wire error messages to toast system in all three sections
- Add try-catch around all async operations

### Phase 3: Add Testing
- Create E2E test that saves each setting type and verifies persistence
- Test: Save budget → reload page → verify values persisted
- Test: Save provider → test connection works with saved config
- Test: Change framework → verify new selection persists

---

## 📋 Files to Modify/Create

### Backend (No Changes Required)
Settings endpoints already functional:
- `POST /api/settings/budget` - saves monthly_budget, daily_warning
- `POST /api/settings/ai-provider` - saves provider config
- `POST /api/settings/agent-framework` - saves framework selection
- `POST /api/settings/ai-provider/{name}/test` - tests stored config

### Frontend

#### Modify: `frontend/src/lib/api.ts`
- **Line ~215**: Add wrapper function `testAIProvider(providerName: string)` that calls `/api/settings/ai-provider/{name}/test` endpoint
- Purpose: Centralize all API calls (currently ProviderCard uses raw fetch)

#### Modify: `frontend/src/app/settings/page.tsx`
- **Line 44-86 (ProviderCard handleTest)**: Replace direct `fetch()` with new `testAIProvider()` from api.ts
- **Line 214-216 (handleSaveProvider)**: Change from async wrapper to direct call to `saveAIProvider()` and handle error response
- **Add error handling**: Wrap all save operations in try-catch that calls `onError()`

#### Create: `e2e/settings-persistence.spec.ts`
- Test: "Should save budget settings and persist on page reload"
  - Fill form → Save → Assert success toast → Reload → Assert values present
- Test: "Should save AI provider and test connection works"
  - Add provider → Save → Test Connection → Verify success
- Test: "Should save agent framework selection"
  - Change framework → Save → Reload → Verify selection persists
- Test: "Should show error toast on invalid budget"
  - Enter negative value → Save → Assert error toast
- Test: "Should disable save button during submission"
  - Click Save → Assert button disabled with spinner

---

## 📊 Data Model Changes

**None** - All data already persisted in backend:
- `budget_settings` table: monthly_budget, daily_warning
- `ai_providers` table: provider_name, api_key, model, is_active
- `agent_framework` setting: stored in config or database

---

## 🔌 API Changes

**No new endpoints required.** All existing endpoints work correctly:

```
POST /api/settings/budget
├─ Request: {monthly_budget: number, daily_warning: number}
└─ Response: {success: bool, monthly_budget, daily_warning}

POST /api/settings/ai-provider
├─ Request: {provider: string, api_key: string, model?: string}
└─ Response: {success: bool}

POST /api/settings/ai-provider/{name}/test
├─ Request: {method: POST, body: {}}
└─ Response: {success: bool, error?: string}

POST /api/settings/agent-framework
├─ Request: {framework: string}
└─ Response: {success: bool, framework: string}
```

---

## 🎨 Frontend Changes

### ProviderCard Component (`settings/page.tsx:44-200`)
**Current Issues**:
- Uses raw `fetch()` instead of api.ts
- No try-catch around handleSave
- Error messages only logged, not shown to user

**Fixes**:
```tsx
// Before
const handleTest = async () => {
  setTesting(true);
  try {
    const res = await fetch(`/api/settings/ai-provider/${provider.name}/test`, ...);
    const data = await res.json();
    setTestResult(data.success ? 'success' : 'error');
  } catch { setTestResult('error'); }
}

// After
const handleTest = async () => {
  setTesting(true);
  try {
    const data = await testAIProvider(provider.name);
    setTestResult(data.success ? 'success' : 'error');
  } catch (err) {
    onError(`Failed to test ${provider.display_name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
    setTestResult('error');
  } finally {
    setTesting(false);
  }
}

// Same fix pattern for handleSave
```

### Settings Page (`settings/page.tsx:202-454`)
**Already working correctly** for framework and budget sections. Just ensure:
- Framework error handling explicit: catch errors from `setAgentFramework()`
- Budget error handling explicit: catch errors from `saveBudgetSettings()`
- Both show proper error messages via `showError()`

---

## ✅ Testing Strategy

### Unit Tests (Optional)
Already covered by existing test files - focus on E2E.

### E2E Tests: `e2e/settings-persistence.spec.ts`
Create comprehensive test suite using Playwright:

```typescript
test.describe('Settings Form Persistence', () => {
  test('should save budget settings and verify persistence', async ({ page }) => {
    // 1. Navigate to settings
    // 2. Fill monthly budget: $500, daily warning: $50
    // 3. Click Save Budget button
    // 4. Assert success toast appears
    // 5. Wait 2 seconds
    // 6. Reload page
    // 7. Assert values still show $500 and $50
  });

  test('should save AI provider configuration', async ({ page }) => {
    // 1. Fill provider: Anthropic, API key: test_key_123
    // 2. Select model: claude-opus-4-6
    // 3. Click Save
    // 4. Assert success toast
    // 5. Click Test Connection
    // 6. Assert success indicator shows
  });

  test('should show error for invalid budget', async ({ page }) => {
    // 1. Fill negative monthly budget: -100
    // 2. Click Save
    // 3. Assert error toast with message about non-negative
  });

  test('should disable save button during submission', async ({ page }) => {
    // 1. Fill form
    // 2. Click Save
    // 3. Assert button is disabled and shows spinner
    // 4. Wait for response
    // 5. Assert button re-enabled
  });
});
```

### Manual Testing Checklist
- [ ] Save budget → Reload page → Values persist
- [ ] Save provider → Reload page → Status shows "Configured"
- [ ] Test connection → Shows success/error indicator
- [ ] Error messages appear in toast for validation failures
- [ ] Save buttons have loading state during submission
- [ ] Multiple rapid saves don't cause race conditions

---

## 🔐 Security Considerations

**No new vulnerabilities introduced**:
- API keys still masked in UI (password input type)
- CSRF tokens handled by Flask session middleware
- All inputs validated by backend
- No secrets logged to console

---

## 📈 Success Criteria

- ✅ All three settings sections (Provider, Framework, Budget) save successfully
- ✅ Success/error toasts appear for all operations
- ✅ Settings persist after page reload
- ✅ E2E test covers full happy path and error scenarios
- ✅ No console errors during form submission
- ✅ Buttons show loading state during requests

---

## ⏱️ Timeline

| Phase | Task | Hours |
|-------|------|-------|
| 1 | Add `testAIProvider()` to api.ts | 1 |
| 2 | Fix ProviderCard error handling | 2 |
| 3 | Verify Framework & Budget handling | 1 |
| 4 | Write E2E tests (Playwright) | 4 |
| 5 | Manual testing & bug fixes | 3 |
| 6 | Code review & polish | 2 |
| **Total** | | **13 hours** |

