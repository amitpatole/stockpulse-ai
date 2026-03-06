# Technical Design Spec: GitHub Actions CI/CD Pipeline for TickerPulse

**Document Version**: 1.0
**Date**: 2026-03-06
**Status**: Production Ready
**Architect**: Diana Torres

---

## 1. APPROACH

### Overview
A **4-stage, parallel-optimized GitHub Actions CI/CD pipeline** that validates every commit, prevents defects early, and enables safe deployments.

### Design Philosophy
- **Fail fast**: Lint + type checking run first (2-3 min), blocking expensive tests
- **Parallel execution**: Independent jobs run simultaneously to minimize total time (~8-10 min)
- **Multi-environment**: Separate testing environments for unit, integration, and E2E
- **Security by default**: Secrets scanning on every push, dependency auditing daily
- **Developer-friendly**: Clear error messages, auto-fixable linting, pre-commit hooks
- **Deployment safety**: Manual approval for production, automatic rollback on failure

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: LINT (2-3 min)                                     │
│ ├─ Backend: Black, isort, flake8, mypy                      │
│ └─ Frontend: ESLint, Prettier, TypeScript                   │
│                                                             │
├─ Stage 2: TEST (5-8 min, depends on Stage 1)               │
│ ├─ Backend: pytest with 70%+ coverage threshold             │
│ ├─ Frontend: Vitest unit tests                              │
│ └─ Secrets: Gitleaks secret detection                       │
│                                                             │
├─ Stage 3: E2E (10 min, PR/dispatch only, needs Stages 1-2) │
│ └─ Frontend: Playwright end-to-end tests                    │
│                                                             │
├─ Stage 4: BUILD (3-5 min, depends on Stage 2)              │
│ ├─ Backend: Python import verification                      │
│ ├─ Frontend: Next.js production build                       │
│ └─ Artifacts: Upload for deployment                         │
│                                                             │
└─ GATE: CI Status Check (aggregates all results)            │
  └─ Blocks merge if any required job fails                  │
```

### Concurrency Control
- **Workflow-level**: Only one CI run per branch at a time
- **In-progress cancellation**: Pushing new commits cancels previous pending runs
- **Benefit**: Saves GitHub Actions minutes, prevents cascading failures

### Entry Points
1. **Push to main**: Full CI pipeline (7 jobs)
2. **Push to develop**: Full CI pipeline (7 jobs)
3. **Pull requests**: Full CI + E2E tests (9 jobs)
4. **Manual dispatch**: Full pipeline on demand
5. **Scheduled**: Security scanning daily at 2 AM UTC

---

## 2. FILES TO MODIFY/CREATE

### Core Workflow Files (`.github/workflows/`)
| File | Purpose | Jobs |
|------|---------|------|
| `ci.yml` | Main CI pipeline | lint-backend, lint-frontend, test-backend, test-frontend, test-e2e, build-backend, build-frontend, secrets-scan, ci-status |
| `deploy.yml` | Staging/production deployment | deploy-staging, deploy-production |
| `security.yml` | Daily security scanning | dependency-scan-python, dependency-scan-js, sast-bandit, container-scan |

### Configuration Files
| File | Purpose | Changes |
|------|---------|---------|
| `.pre-commit-config.yaml` | Local git hooks (24 hooks) | 24 hooks: Black, isort, flake8, mypy, Prettier, ESLint, Gitleaks, etc. |
| `.bandit` | Bandit SAST configuration | Severity/confidence levels, exclude test dirs |
| `requirements.txt` | Python dependencies | +12 testing/linting tools |
| `pyproject.toml` | Python project config | pytest, coverage, mypy config |

### Documentation Files
| File | Audience | Content |
|------|----------|---------|
| `.github/CICD_OVERVIEW.md` | All | Architecture, flow diagrams, metrics |
| `.github/WORKFLOW_SETUP.md` | DevOps/Leads | Configuration, environment vars, deployment setup |
| `.github/CONTRIBUTING.md` | Developers | Code style, testing, git conventions |
| `.github/BRANCH_PROTECTION.md` | Maintainers | GitHub branch rules setup guide |
| `.github/pull_request_template.md` | Developers | PR structure, checklists |

---

## 3. DATA MODEL CHANGES

**No database schema changes required.**

Pipeline runs as stateless jobs. All state stored in:
- **GitHub Artifacts**: Build outputs (frontend/.next)
- **GitHub Secrets**: Deployment credentials (read-only)
- **GitHub Actions Logs**: CI results and timing data

---

## 4. API CHANGES

**No API endpoint changes.**

All validation occurs locally:
- **Backend testing**: pytest mocks Flask app (no network calls)
- **Frontend testing**: Vitest with msw (mock service worker)
- **E2E testing**: Playwright against real Flask server on `http://localhost:5000`

The only production changes are:
- **Health endpoint** (`GET /health`) must return 200 OK for deployment validation
- **CORS headers** must be set for Playwright E2E tests (already configured)

---

## 5. FRONTEND CHANGES

**Minimal impact.**

### New Test Infrastructure
- `frontend/vitest.config.ts` - Vitest configuration (unit tests)
- `frontend/playwright.config.ts` - Playwright configuration (E2E tests)
- `e2e/` directory - Playwright specs

### Modified Files
- `frontend/package.json` - Added test scripts:
  ```json
  "test:unit": "vitest",
  "test:e2e": "playwright test",
  "lint": "eslint src --max-warnings 0",
  "format": "prettier --write src"
  ```

### No Component Changes
- Existing React components unchanged
- E2E tests interact with app as-is
- No new UI elements for CI/CD

---

## 6. TESTING STRATEGY

### Unit Tests (Backend)

**Coverage**: 70%+ threshold enforced

**Test Suite**: `backend/tests/`
- `test_api_endpoints_comprehensive.py` - 38 API endpoint tests
- `test_api_*_focused.py` - 36 focused tests (analysis, stocks, research)
- `test_websocket_blueprint.py` - 17 WebSocket integration tests
- `test_pagination.py` - 40+ pagination tests

**Framework**: pytest with mocking
- All database calls mocked (no .db file created during tests)
- All external API calls mocked (no real network requests)
- Isolation: Each test independent, can run in any order

**Run Locally**:
```bash
PYTHONPATH=. pytest backend/tests/ -v --cov=backend --cov-report=term-missing
```

### Unit Tests (Frontend)

**Framework**: Vitest (Vite-native, faster than Jest)

**Test Types**:
- Component tests: Vitest + @testing-library/react
- Hook tests: @testing-library/react hooks
- Utility tests: Pure function testing

**Run Locally**:
```bash
cd frontend && npm run test:unit
```

### E2E Tests (Playwright)

**Scope**: Full user workflows, browser-level interactions

**Test Files**:
- `e2e/settings.spec.ts` - Settings persistence
- `e2e/settings-persistence.spec.ts` - Form state validation
- `e2e/websocket-prices.spec.ts` - Real-time price updates

**Preconditions**:
- Backend must run on `localhost:5000`
- Database initialized with test data
- WebSocket server accessible

**Run Locally**:
```bash
# Terminal 1: Start backend
python backend/app.py

# Terminal 2: Run E2E tests
cd frontend && npm run test:e2e
```

### Linting & Type Checking

**Backend Linting**:
```bash
black backend/                     # Formatting
isort backend/                     # Import sorting
flake8 backend/ --max-line-length=120
mypy backend/ --ignore-missing-imports
```

**Frontend Linting**:
```bash
cd frontend && npm run lint        # ESLint + Prettier
npx tsc --noEmit                   # TypeScript check
```

**Auto-fix**:
```bash
black --line-length=120 backend/
isort backend/
cd frontend && npm run format
```

### Coverage Reporting

**Backend**: Pytest uploads to Codecov
- Reports at PR: Code coverage badge in PR checks
- Dashboard: codecov.io/gh/your-org/tickerpulse-checkout
- Threshold: 70% overall, no decrease allowed

**Frontend**: Vitest coverage optional (not currently enforced)

### Artifact Management

**Uploaded on Success**:
1. `frontend/.next` - Next.js build output (7-day retention)
2. `playwright-report` - E2E test screenshots/videos (7-day retention)

---

## Quality Gates (Blocking Checks)

| Check | Tool | Failure Mode | Duration |
|-------|------|--------------|----------|
| **Backend Lint** | Black/isort/flake8 | Formatting errors | 2-3 min |
| **Frontend Lint** | ESLint/Prettier/TypeScript | Style & type errors | 2-3 min |
| **Backend Tests** | pytest | Test failures or <70% coverage | 5 min |
| **Frontend Tests** | Vitest | Test failures | 3 min |
| **Backend Build** | Python syntax check | Import errors | 1 min |
| **Frontend Build** | Next.js build | Compilation errors | 3-5 min |
| **Secrets Scan** | Gitleaks | API keys, tokens detected | 1 min |

---

## Performance Optimization

| Optimization | Method | Benefit |
|--------------|--------|---------|
| **Parallel jobs** | GitHub Actions job matrix | 8-10 min total (vs 15+ sequential) |
| **Dependency caching** | `actions/setup-python@v4` cache parameter | 30-60s saved per job |
| **Concurrency control** | Cancel in-progress runs | Saves GitHub Actions minutes |
| **Conditional E2E** | Only on PR/dispatch | Skips expensive tests on push to main |
| **Build artifact reuse** | Upload only necessary files | Faster deploys, cleaner artifacts |

---

## Security Architecture

### Secrets Scanning
- **Tool**: Gitleaks + hardcoded credential detection
- **Triggers**: Every push to main/develop/PR
- **Blocks**: Merge if secrets detected
- **Action**: Requires secret removal + git history cleaning

### Dependency Auditing
- **Python**: pip-audit, Safety (daily)
- **JavaScript**: npm audit, Snyk (daily)
- **Block**: CRITICAL/HIGH severity vulnerabilities

### SAST (Static Application Security Testing)
- **Python**: Bandit (checks for dangerous patterns)
- **JavaScript**: Semgrep + ESLint security rules
- **Daily schedule**: 2 AM UTC (off-peak)

### Container Security (Optional)
- **Tool**: Trivy (if using Docker)
- **Scans**: Base image vulnerabilities

---

## Deployment Strategy

### Staging (Automatic on main merge)
1. **Trigger**: All CI jobs pass on main
2. **Frontend**: Deploy to Vercel (auto-preview)
3. **Backend**: Deploy to staging environment
4. **Validation**: Health check curl requests
5. **Rollback**: Auto-revert on health check failure

### Production (Manual approval)
1. **Trigger**: Manual approval via GitHub
2. **Gate**: Code review approval required
3. **Frontend**: Deploy to production Vercel
4. **Backend**: Deploy to production environment
5. **Validation**: Post-deployment health checks
6. **Monitoring**: Error rate alerts + performance metrics

---

## Developer Workflow Integration

### Local Pre-commit Hooks
Developers install hooks locally to catch issues before commit:
```bash
pip install pre-commit
pre-commit install
```

Benefits:
- Immediate feedback (no wait for CI)
- Auto-fixes formatting (Black, Prettier)
- Prevents accidental secrets commits
- Fails fast on mypy errors

### CI as Safety Net
- If hooks skipped, CI catches issues
- Provides detailed logs for debugging
- Blocks merge on failure (with clear error messages)

---

## Monitoring & Alerting

### GitHub Workflows
- **Dashboard**: Actions tab shows all runs, durations, logs
- **PR Checks**: Status badges show pass/fail
- **Branch Protection**: Enforces required checks

### Integration Options (Not Implemented)
- Slack notifications on CI failure
- Email alerts for security findings
- Datadog metrics for CI duration trends

---

## Files Summary

### Total New/Modified Files: 13

**Workflows (3)**
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/security.yml`

**Config (3)**
- `.pre-commit-config.yaml`
- `.bandit`
- `pyproject.toml`

**Documentation (4)**
- `.github/CICD_OVERVIEW.md`
- `.github/WORKFLOW_SETUP.md`
- `.github/CONTRIBUTING.md`
- `.github/pull_request_template.md`

**Dependencies (1)**
- `requirements.txt` (updated with +12 tools)

**Existing Files Unchanged**
- `backend/` code structure
- `frontend/` code structure
- `database.py` schema

---

## Acceptance Criteria

- ✅ CI runs on every commit to main/develop
- ✅ PR requires all status checks to pass
- ✅ E2E tests run on PR (not on every push)
- ✅ Coverage reports uploaded to Codecov
- ✅ Secrets detected and blocked
- ✅ Linting auto-fixable with clear error messages
- ✅ Build artifacts preserved for 7 days
- ✅ Documentation covers setup + troubleshooting
- ✅ Pre-commit hooks available for developers
- ✅ <10 minute total pipeline duration
