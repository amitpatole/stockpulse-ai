# CI/CD Pipeline Documentation

## Overview

This project uses **GitHub Actions** for continuous integration and deployment. The pipeline enforces code quality, security, and testing standards before code reaches production.

**Status**: ✅ Fully implemented across three workflow files
- `ci.yml` - Main CI pipeline (lint, type check, test, build)
- `security.yml` - Security scanning (dependencies, secrets, SAST)
- `deploy.yml` - Deployment to staging/production

---

## CI Pipeline Architecture

### Stage 1: Fast Validation (Lint + Type Check)
**Duration**: ~2-3 minutes | **Blocks**: Pull requests

Runs on all pushes and PRs to catch style/type issues early:

#### Backend
- **Black**: Code formatting check
- **isort**: Import organization check
- **flake8**: PEP 8 compliance
- **mypy**: Type safety validation

#### Frontend
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting check
- **TypeScript**: Compilation check (tsc --noEmit)

**Failure Mode**: `continue-on-error: true` - Non-blocking warnings, errors must be reviewed in logs

---

### Stage 2: Testing (Unit + Integration)
**Duration**: ~5-8 minutes | **Blocks**: Merges to main

Runs after linting passes:

#### Backend Tests
```bash
PYTHONPATH=. pytest backend/tests/ \
  -v \
  --tb=short \
  --cov=backend \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-fail-under=70 \
  --timeout=30
```

**Requirements**:
- ✅ 70% code coverage minimum (enforced)
- ✅ All tests must pass
- ✅ Individual tests timeout after 30 seconds
- ✅ Coverage reported to Codecov

**Test Files**: `backend/tests/*.py`

#### Frontend Tests
```bash
cd frontend && npm run test:unit -- --run --coverage
```

**Requirements**:
- ✅ All Vitest unit tests pass
- ✅ Coverage reported to Codecov
- ✅ Must complete in <10 minutes

**Test Files**: `frontend/src/**/__tests__/*.test.{ts,tsx}`

---

### Stage 3: E2E Tests
**Duration**: ~5-10 minutes | **Trigger**: Pull requests only (manual dispatch optional)

Runs Playwright browser tests against live backend:

```bash
# Backend starts on port 5000 (Flask)
cd backend && python -m flask run &

# Frontend E2E tests
cd frontend && npm run test:e2e
```

**Requirements**:
- ✅ Backend must start successfully
- ✅ All Playwright tests must pass
- ✅ Max 15 minutes total
- ✅ Report artifacts uploaded for debugging

**Test Files**: `e2e/**.spec.ts`

**Note**: Currently uses Flask - verify this matches your backend framework

---

### Stage 4: Build Artifacts
**Duration**: ~3-5 minutes | **Blocks**: Production deployment

#### Backend Build
- Python syntax validation (py_compile)
- Import checks (verify `backend.app` and `backend.database` load)
- Dependencies verified

#### Frontend Build
- Next.js production build
- Validates `.next/` directory creation
- Artifact uploaded (retention: 7 days)

---

### Status Check
**Final gate**: Aggregates all job results

If ANY required job fails, the entire pipeline fails and blocks merge to main.

```
Requirements for merge:
✅ lint-backend: PASS
✅ lint-frontend: PASS
✅ test-backend: PASS (70% coverage)
✅ test-frontend: PASS
✅ build-backend: PASS
✅ build-frontend: PASS
⚠️ test-e2e: Optional (PR only)
```

---

## Trigger Events

| Event | Branches | Runs | Purpose |
|-------|----------|------|---------|
| `push` | main, develop | All stages | Validate pushed code |
| `pull_request` | main, develop | All stages + E2E | Pre-merge validation |
| `workflow_dispatch` | any | All stages + E2E | Manual testing |

---

## Concurrency & Performance

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

**Behavior**:
- Only one CI run per branch at a time
- New push cancels older pending runs (faster feedback)
- Prevents resource waste on superseded commits

---

## Parallel Job Execution

Jobs run in parallel where possible:

```
┌─ lint-backend ─────┐
│                    ├─ test-backend ────┐
└─ lint-frontend ────┼─ test-frontend ───┼─ build-backend
                     │                    │
                     └─ test-e2e (PR only)┤
                                         └─ ci-status ✓/✗
```

**Estimated total time**: 8-10 minutes (vs 20+ if sequential)

---

## Code Coverage Requirements

### Backend
- **Minimum**: 70% coverage
- **Reported to**: Codecov
- **Failure**: Hard stop - cannot merge if <70%

### Frontend
- **No minimum** (informational only)
- **Reported to**: Codecov
- **Failure**: Soft stop - visible but not enforced

---

## Security Pipeline

Runs **independently** on push + scheduled (2 AM UTC daily):

### Scans Performed
1. **Dependency Scanning**
   - Python: `safety check` + pip-audit
   - Node: `npm audit`
   - Detects: Vulnerable packages

2. **SAST (Static Application Security Testing)**
   - Python: Bandit + Semgrep
   - JavaScript: ESLint + security plugin
   - Detects: Code injection, unsafe patterns

3. **Secret Scanning**
   - Gitleaks: Detects leaked credentials
   - Custom patterns: API keys, passwords
   - Detects: Hardcoded secrets

4. **Container Scanning** (if Dockerfile exists)
   - Trivy: Scans Docker image layers
   - Detects: Vulnerable base images

### Security Policy
- ⚠️ **Non-blocking**: Issues logged but don't fail CI
- 🔴 **High/Critical**: Must be addressed before production deploy
- 📊 **Reports**: Artifacts uploaded for review

---

## Deployment Pipeline

**Trigger**: Successful CI + push to main OR manual workflow_run

### Staging Deployment
1. Build frontend (Next.js)
2. Deploy to Vercel (staging project)
3. Send notification
4. Continue on error (non-blocking)

### Production Deployment
1. Requires manual approval (GitHub environment protection)
2. Run frontend tests one more time
3. Build frontend + backend
4. Deploy to Vercel (production project)
5. Post-deployment health check
6. Rollback on failure (automatic for Vercel)

---

## Debugging Failed Runs

### View Logs
1. Click workflow run on GitHub Actions tab
2. Click failed job name
3. Expand failed step
4. Review error output

### Common Failures

#### Backend Tests Fail
```bash
# Run locally to debug
PYTHONPATH=. pytest backend/tests/ -vv --pdb
```

**Check**:
- Python 3.11 installed?
- All dependencies in `requirements.txt`?
- Database fixtures setup?
- Tests timeout after 30s?

#### Frontend Tests Fail
```bash
# Run locally to debug
cd frontend && npm run test:unit -- --ui
```

**Check**:
- Node 20 installed?
- All dependencies in `package-lock.json`?
- Component props match snapshots?
- Mocks properly configured?

#### E2E Tests Fail
```bash
# Run locally with debug
cd frontend && npx playwright test --debug
```

**Check**:
- Backend server running on port 5000?
- Frontend .env.test configured?
- Playwright browsers installed?
- Page selectors match current UI?

#### Coverage Threshold Fails
- Minimum is 70% for backend
- Add test for uncovered lines
- Use `--cov-report=html` to view coverage map

#### Docker Build Fails
- Check Dockerfile exists in repo root
- Verify base image accessible
- Check all COPY paths are correct

---

## Performance Optimization

### Current Strategy
| Component | Strategy | Impact |
|-----------|----------|--------|
| Linting | Run in parallel (backend + frontend) | -2 min |
| Testing | Parallel jobs with caching | -3 min |
| Dependencies | GitHub caching (pip + npm) | -1 min |
| E2E Tests | PR-only (not on every push) | -5 min |

### Future Improvements
- Matrix strategy for multiple Python versions
- Conditional steps (only run E2E if code changed)
- Shard E2E tests across 3-4 workers
- Docker layer caching for builds

---

## Required Secrets

Store these in GitHub repository settings (`Settings > Secrets`):

### Deployment Secrets
| Secret | Used By | Example |
|--------|---------|---------|
| `VERCEL_TOKEN` | deploy.yml | `vercel_xxx...` |
| `VERCEL_ORG_ID` | deploy.yml | `team_xxx` |
| `VERCEL_PROJECT_ID_STAGING` | deploy.yml | `prj_xxx` |
| `VERCEL_PROJECT_ID_PROD` | deploy.yml | `prj_xxx` |

### Optional Secrets
| Secret | Used By | Purpose |
|--------|---------|---------|
| `CODECOV_TOKEN` | ci.yml | Enhanced Codecov integration |
| `SLACK_WEBHOOK` | Any workflow | Notifications to Slack |

---

## Enforcement

### Pre-Commit Hooks (Local)
Before pushing, ensure:
```bash
black backend/
isort backend/
flake8 backend/
mypy backend/ --ignore-missing-imports

cd frontend
npm run lint
npm run format:check
npx tsc --noEmit
```

### Branch Protection Rules (GitHub)
```
main branch requires:
✅ CI workflow status check (ci-status job)
✅ At least 1 code review approval
✅ Up-to-date with base branch
❌ Dismiss stale reviews on new push
❌ Force pushes allowed
```

---

## Maintenance

### Monthly Tasks
- [ ] Review and update dependencies
- [ ] Check GitHub Actions for deprecation warnings
- [ ] Verify secret rotation schedule
- [ ] Review security scan results
- [ ] Update test coverage baselines

### Quarterly Tasks
- [ ] Analyze CI performance (run times, failures)
- [ ] Update documentation with new patterns
- [ ] Review GitHub Actions pricing
- [ ] Test rollback procedures

---

## Related Documentation

- **API Guidelines**: `documentation/09-api-guidelines.md`
- **Testing Strategy**: `documentation/24-testing.md`
- **Security Checklist**: `documentation/10-security.md`
- **Git Operations**: `documentation/21-git-operations.md`

---

## Support

**Questions about CI/CD?**
1. Check this document (Ctrl+F)
2. Review the actual workflow files (`.github/workflows/`)
3. Check failed run logs on GitHub Actions tab
4. Open an issue with workflow diagnostics

**To run CI locally**:
```bash
# Install act (GitHub Actions locally)
brew install act

# Run full CI pipeline
act -j lint-backend -j lint-frontend

# Run single job
act -j test-backend
```

---

**Last Updated**: 2026-03-06
**Maintained By**: Backend Team (TickerPulse)
