# CI/CD Pipeline - Technical Design Specification

**Document**: Technical Architecture for GitHub Actions CI/CD Pipeline
**Scope**: TickerPulse AI (Flask backend + Next.js frontend + Electron desktop)
**Status**: Complete Architecture (Implementation: 95% done)
**Last Updated**: 2026-03-06

---

## 1. APPROACH

### High-Level Strategy

**Fail-fast pipeline** with staged validation:

```
Code Push → Lint (2m) → Test (3m) → Security (2m) → Build (2m) → Deploy
          ↓
       [Parallel Jobs]  [Blocking]  [Blocking]      [Blocking]
                        (all fail if any step fails)
```

**Three separate workflows** for separation of concerns:
1. **CI Pipeline** (`ci.yml`): Lint, test, build, security on every push/PR
2. **Deploy Pipeline** (`deploy.yml`): Auto-deploy staging, manual prod approval
3. **Security Pipeline** (`security.yml`): Daily dependency scans + scheduled analysis

**Principles**:
- Block merges on test/lint/security failures (pre-commit hooks enforce locally)
- Parallel job execution to minimize feedback loop (3-5 min total)
- Branch protection on `main`: require CI status ✅ + code review ✅
- Automatic rollback on production deployment failure

---

## 2. FILES TO MODIFY/CREATE

### Workflow Files (.github/workflows/)
| File | Status | Purpose |
|------|--------|---------|
| `ci.yml` | ✅ Created | Main CI: lint → test → build → security (9 jobs) |
| `deploy.yml` | ✅ Created | Staging (auto) + Production (manual approval) |
| `security.yml` | ✅ Created | Bandit, Semgrep, Gitleaks, npm audit (daily) |
| `build-windows.yml` | ✅ Created | Windows build for Electron desktop (nightly) |

### Configuration Files
| File | Status | Changes |
|------|--------|---------|
| `.pre-commit-config.yaml` | ✅ Created | Local hooks: Black, isort, ESLint, Prettier, Bandit |
| `.bandit` | ✅ Created | Bandit config: exclude tests, skip assertions |
| `requirements.txt` | ✅ Updated | Added: black, isort, pytest-cov, bandit |
| `frontend/package.json` | ✅ Updated | Added: ESLint, Prettier, Vitest scripts |

### Documentation Files
| File | Status | Purpose |
|------|--------|---------|
| `.github/CICD_OVERVIEW.md` | ✅ Created | Pipeline overview + troubleshooting |
| `.github/WORKFLOW_SETUP.md` | ✅ Created | Setup guide + deployment config |
| `.github/CONTRIBUTING.md` | ✅ Created | Developer guidelines for CI |
| `.github/pull_request_template.md` | ✅ Created | PR checklist |

---

## 3. DATA MODEL CHANGES

**None** - CI/CD is infrastructure, not application code.

---

## 4. API CHANGES

**None** - No new endpoints. Pipeline only validates existing APIs.

Health check endpoints assumed:
- Frontend: `https://tickerpulse.example.com/` (HTTP 200)
- Backend: `https://api.tickerpulse.example.com/health` (HTTP 200)

---

## 5. FRONTEND CHANGES

**No UI changes** - CI/CD is backend infrastructure.

Build artifacts:
- Next.js output: `.next/` directory
- Deployment: Vercel (staging + prod)
- Environment variables: Injected at build time from GitHub secrets

---

## 6. TESTING STRATEGY

### Unit Tests (Blocking)
- **Backend**: `pytest backend/tests/test_*.py` (1-2 min)
  - Must pass: ✅ 36+ focused tests covering analysis, stocks, research APIs
  - Coverage target: 80%+ on critical paths
  - Mocked dependencies (no database I/O)

- **Frontend**: `npm run test:unit` via Vitest (2-3 min)
  - Must pass: ✅ AgentCard (8 tests), Toast (14 tests), a11y (37+ tests)
  - Coverage: Components, hooks, state management
  - Mocked API calls

### E2E Tests (Warning, PR/main only)
- **Playwright**: `npm run test:e2e` (5-10 min)
  - Websocket integration tests (11 tests)
  - Settings persistence (3 tests)
  - Dashboard workflows
  - Skipped on feature branches (optional)

### Linting/Formatting (Blocking)
- **Backend**: Black, isort, Bandit
  - Auto-fix: `black backend/` + `isort backend/`
- **Frontend**: ESLint, Prettier, TypeScript strict
  - Auto-fix: `npm run lint -- --fix`

### Security Tests (Blocking)
- **Secrets**: Gitleaks (detects API keys, passwords, tokens)
- **SAST**: Bandit (Python), Semgrep (patterns), ESLint security (JS)
- **Dependencies**: Safety (Python), npm audit (JavaScript)
- **Container**: Trivy (if Docker image used)

### Coverage Gates
- Pytest: `--cov=backend --cov-fail-under=80` (configurable)
- Reports: GitHub Actions → artifacts

---

## 7. DEPLOYMENT STRATEGY

### Staging (Automatic on Main)
1. Build Next.js frontend
2. Deploy to Vercel staging environment
3. Run health checks
4. Accessible to team for QA

### Production (Manual Approval Required)
1. Requires GitHub environment approval
2. Builds both frontend + backend
3. Deploys to Vercel production
4. Post-deployment health checks
5. Automatic rollback on failure

### Secrets Management
- GitHub Actions secrets (never in code): `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID_*`
- Environment variables: `.env.example` checked in, sensitive values via secrets
- Pre-commit hooks prevent accidental secret commits

---

## 8. STATUS CHECKS & BRANCH PROTECTION

### Required (Blocking) Checks
- ✅ backend-lint
- ✅ backend-tests
- ✅ backend-build
- ✅ frontend-lint
- ✅ frontend-tests
- ✅ frontend-build
- ✅ security

### Optional (Warning) Checks
- ⚠️ e2e-tests
- ⚠️ code-coverage

### Merge Requirements
1. All blocking checks ✅ passed
2. At least 1 code review approval
3. Branch up-to-date with main
4. No unresolved conversations

---

## 9. MONITORING & ALERTS

### What Gets Tracked
| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| Build time | GitHub Actions | >5 min (slow build) |
| Test coverage | pytest-cov | <80% (configure fail threshold) |
| Failed workflows | GitHub | Any failure blocks merge |
| Security issues | Bandit/Semgrep | Any issue blocks merge |

### Notifications
- GitHub: PR status checks (green/red)
- Optional: Slack webhook on failure
- Optional: Email on production deployment

---

## 10. CONFIGURATION CHECKLIST

- [ ] GitHub secrets added: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID_STAGING`, `VERCEL_PROJECT_ID_PROD`
- [ ] Branch protection rule on `main`: require status checks + code review
- [ ] Pre-commit hooks installed locally: `pre-commit install`
- [ ] Deploy URLs updated: Replace `tickerpulse.example.com` with actual domain
- [ ] Health check endpoints verified and working
- [ ] `.env.example` in repo, sensitive values in GitHub secrets
- [ ] Slack webhook added (optional) for notifications

---

## 11. RELATED DOCUMENTATION

- **Implementation Guides**: [WORKFLOW_SETUP.md](.github/WORKFLOW_SETUP.md)
- **Architecture Overview**: [CICD_OVERVIEW.md](.github/CICD_OVERVIEW.md)
- **Contributing**: [CONTRIBUTING.md](.github/CONTRIBUTING.md)
- **Development Governance**: [CLAUDE.md](../CLAUDE.md)
