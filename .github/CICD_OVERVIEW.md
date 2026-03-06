# CI/CD Pipeline Overview

This document provides a comprehensive overview of the TickerPulse CI/CD pipeline built with GitHub Actions.

## 🎯 Pipeline Goals

1. **Automated Testing** - Run all tests automatically on every push/PR
2. **Code Quality** - Enforce linting, formatting, and type checking
3. **Security** - Detect secrets, vulnerabilities, and security issues
4. **Continuous Deployment** - Automatically deploy to staging/production
5. **Reliability** - Catch bugs early before they reach production

## 📊 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Developer Commits Code                                         │
│  git push origin feat/new-feature                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Webhook Triggered                                       │
│  ✓ PR opened / Commit pushed                                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  CI Pipeline Starts (3-5 minutes)                               │
│                                                                  │
│  ┌────────────────────────┐  ┌────────────────────────┐         │
│  │ Backend Lint           │  │ Frontend Lint          │         │
│  │ - Black                │  │ - ESLint               │         │
│  │ - isort                │  │ - Prettier             │         │
│  │ - flake8               │  │ - TypeScript check     │         │
│  │ Result: ⚠️ Warning     │  │ Result: ⚠️ Warning     │         │
│  └────────────────────────┘  └────────────────────────┘         │
│                               │                                  │
│  ┌────────────────────────┐  ┌────────────────────────┐         │
│  │ Backend Tests          │  │ Frontend Tests         │         │
│  │ pytest ..................│  │ Vitest ............   │         │
│  │ ✓ Runs in 1-2 min      │  │ ✓ Runs in 2-3 min     │         │
│  │ Result: 🛑 Blocking    │  │ Result: 🛑 Blocking   │         │
│  └────────────────────────┘  └────────────────────────┘         │
│                               │                                  │
│  ┌────────────────────────┐  ┌────────────────────────┐         │
│  │ Backend Build          │  │ Frontend Build         │         │
│  │ Python syntax check    │  │ Next.js compile        │         │
│  │ Result: 🛑 Blocking    │  │ Result: 🛑 Blocking    │         │
│  └────────────────────────┘  └────────────────────────┘         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Security Checks (Parallel)                           │      │
│  │ - Gitleaks (secrets detection)                       │      │
│  │ - Hardcoded credentials scan                         │      │
│  │ Result: 🛑 Blocking                                  │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ E2E Tests (PR & main only)                           │      │
│  │ Playwright tests                                     │      │
│  │ ✓ Runs in 5-10 min                                   │      │
│  │ Result: ⚠️ Warning                                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Final Status Check                                   │      │
│  │ All blocking checks must pass: ✅                     │      │
│  └──────────────────────────────────────────────────────┘      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                            │
                ▼                            ▼
    ┌────────────────────┐      ┌────────────────────┐
    │ All Checks Pass ✅ │      │ Check Fails ❌     │
    │ PR ready to merge  │      │ PR blocked         │
    │ Awaiting review    │      │ Fix issues         │
    │                    │      │ Push new commit    │
    └────────────────────┘      │ Re-run CI          │
                                └────────────────────┘
                                         │
                ┌────────────────────────┘
                │ (CI runs again on new push)
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Merge to Main Branch                                           │
│  ✓ Code review approved                                         │
│  ✓ All checks passing                                           │
│  ✓ Branch up to date                                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Deploy Pipeline Triggers                                       │
│  - Frontend: Deploy to Vercel staging                           │
│  - Backend: Deploy to Railway/Render (if configured)            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Staging Deployment (Automatic)                       │      │
│  │ - Build frontend                                     │      │
│  │ - Deploy to Vercel staging                           │      │
│  │ - Run health checks                                  │      │
│  │ ✓ Live on https://staging.tickerpulse.example.com   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Production Deployment (Requires Manual Approval)    │      │
│  │ - Await deployment approval from maintainers         │      │
│  │ - Deploy to Vercel production                        │      │
│  │ - Run post-deployment health checks                  │      │
│  │ - Rollback on failure                                │      │
│  │ ✓ Live on https://tickerpulse.example.com           │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Workflow Files Structure

```
.github/
├── workflows/
│   ├── ci.yml                    # Main CI pipeline
│   ├── deploy.yml                # Deployment pipeline
│   └── security.yml              # Security scanning
├── CICD_OVERVIEW.md             # This file
├── WORKFLOW_SETUP.md            # Setup & configuration guide
├── CONTRIBUTING.md              # Contributing guidelines
├── pull_request_template.md     # PR template
└── issue_template.md            # Issue template (optional)

Requirements:
├── requirements.txt             # Python dependencies (updated)
└── .pre-commit-config.yaml      # Pre-commit hooks
```

## 🔄 Workflow Files

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Purpose**: Test and validate every commit

**Triggers**:
- Every push to `main` or `develop`
- Every pull request to `main` or `develop`

**Jobs** (9 total):
1. `backend-lint` - Python formatting & linting
2. `backend-tests` - Run pytest test suite
3. `backend-build` - Verify Python syntax
4. `frontend-lint` - TypeScript & ESLint
5. `frontend-tests` - Run Vitest unit tests
6. `frontend-build` - Build Next.js
7. `security` - Gitleaks & secret detection
8. `e2e-tests` - Playwright E2E (PR & main only)
9. `status-check` - Final CI status validation

**Duration**: ~3-5 minutes

**Requirements**:
- Python 3.11
- Node.js 20
- All dependencies installed

### 2. Deploy Workflow (`.github/workflows/deploy.yml`)

**Purpose**: Automatically deploy on successful CI

**Triggers**:
- Successful CI on `main` branch
- Manual workflow dispatch

**Jobs** (4 total):
1. `deploy-staging` - Deploy to staging (automatic)
2. `deploy-production` - Deploy to prod (requires approval)
3. `post-deploy-health-check` - Verify deployment
4. `rollback-on-failure` - Automatic rollback

**Duration**: ~2-3 minutes per environment

**Requirements**:
- Vercel API token (staging & prod)
- AWS/Railway/Render credentials (if using backend deployment)

### 3. Security Workflow (`.github/workflows/security.yml`)

**Purpose**: Continuous security scanning

**Triggers**:
- Every push to `main` or `develop`
- Every pull request
- Daily schedule (2 AM UTC)

**Jobs** (7 total):
1. `dependency-scan` - Safety check Python dependencies
2. `sast-python` - Bandit + Semgrep analysis
3. `sast-javascript` - ESLint security
4. `secrets-scan` - Gitleaks + credential detection
5. `dependency-check` - npm audit + pip-audit
6. `container-scan` - Trivy Docker image scan
7. `security-summary` - Generate security report

**Duration**: ~2-3 minutes

## 🔒 Security Controls

### Secrets Detection
- **Gitleaks**: Detects API keys, passwords, tokens
- **Pattern Matching**: Hardcoded credentials scan
- **Pre-commit Hooks**: Blocks secrets before commit

### Code Security
- **Bandit**: Python security issues
- **Semgrep**: Pattern-based SAST
- **ESLint Security**: JavaScript vulnerabilities

### Dependency Security
- **Safety**: Python vulnerability database
- **npm audit**: JavaScript vulnerability scan
- **Trivy**: Container image vulnerabilities

### Access Control
- **Branch Protection**: Require status checks + code review
- **Secrets Management**: GitHub Actions secrets only
- **Audit Logs**: All actions logged

## ✅ Status Checks & Requirements

### Blocking Checks (Must Pass)
- ✅ Backend lint
- ✅ Backend tests
- ✅ Backend build
- ✅ Frontend lint
- ✅ Frontend tests
- ✅ Frontend build
- ✅ Security scan

### Warning Checks (Don't Block, But Important)
- ⚠️ E2E tests
- ⚠️ Code coverage (if configured)

### Cannot Merge Without
- ✅ All blocking checks passing
- ✅ At least 1 code review approval
- ✅ Branch up to date with main

## 📊 Metrics & Monitoring

### What Gets Tracked

| Metric | Tool | Purpose |
|--------|------|---------|
| Test Coverage | pytest-cov, Vitest | Code quality |
| Build Time | GitHub Actions | Performance |
| Deployment Status | GitHub | Reliability |
| Security Issues | Bandit, Semgrep | Safety |
| Secrets Detected | Gitleaks | Compliance |
| Dependencies | Safety, npm audit | Vulnerability tracking |

### How to View

1. **CI Status**: GitHub PR checks (green/red)
2. **Detailed Logs**: Click on job → expand logs
3. **Coverage**: Codecov or local reports
4. **Security**: GitHub security tab

## 🚀 Deployment Environments

### Staging
- **URL**: `https://staging.tickerpulse.example.com`
- **Deploy**: Automatic on merge to `main`
- **Fresh data**: Yes (database reset possible)
- **Accessible**: Developers + QA team

### Production
- **URL**: `https://tickerpulse.example.com`
- **Deploy**: Manual approval required
- **Fresh data**: No (data preserved)
- **Accessible**: Public/users
- **Rollback**: Automatic on health check failure

## 🔧 Customization Points

### Add New Test Suite
```yaml
# In .github/workflows/ci.yml
- name: Run custom tests
  run: python -m pytest custom_tests/ -v
```

### Add New Linting Tool
```yaml
# Add to requirements.txt
pylint>=2.17.0

# In CI workflow
- name: Run pylint
  run: pylint backend/ --disable=all --enable=E,F
```

### Add Slack Notifications
```yaml
# Add to any job
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

### Add Code Coverage Threshold
```yaml
- name: Check coverage
  run: pytest backend/tests/ --cov=backend --cov-fail-under=80
```

## 🐛 Troubleshooting Common Issues

### "CI Failed: Tests don't pass"
1. Check GitHub Actions logs
2. Run tests locally: `pytest` or `npm run test:unit`
3. Fix issues and push new commit
4. CI automatically re-runs

### "CI Failed: Lint errors"
1. Auto-fix: `black backend/` and `npm run lint -- --fix`
2. Commit changes
3. Push new commit
4. CI re-runs with fixed code

### "CI Failed: Secrets detected"
1. Remove sensitive data from code
2. Use environment variables or GitHub secrets
3. Check git history to remove from past commits
4. Push clean commit

### "Deployment fails"
1. Check post-deploy health checks
2. Verify environment variables set
3. Check application logs
4. Automatic rollback on failure

### "Tests pass locally but fail in CI"
Common causes:
- Different environment variables
- Timezone differences
- Database state issues
- Race conditions

Solutions:
- Check CI env vars match local setup
- Review test isolation
- Check for flaky tests
- Add better mock setup

## 📈 Best Practices

### For Developers
1. **Run tests locally** before pushing
2. **Install pre-commit hooks** to catch issues early
3. **Check CI logs** if tests fail
4. **Keep commits small** and focused
5. **Update documentation** with code

### For Teams
1. **Protect main branch** - require status checks + review
2. **Monitor CI metrics** - track coverage and build time
3. **Set up alerts** - Slack notifications for failures
4. **Review security reports** - check for vulnerabilities
5. **Schedule maintenance** - dependency updates weekly

### For Operations
1. **Monitor deployments** - track success/failure rates
2. **Review logs** - check for errors and warnings
3. **Maintain secrets** - rotate credentials regularly
4. **Update tools** - keep GitHub Actions versions current
5. **Document processes** - keep deployment runbooks updated

## 📚 Related Documentation

- [WORKFLOW_SETUP.md](./../WORKFLOW_SETUP.md) - Detailed configuration
- [CONTRIBUTING.md](./../CONTRIBUTING.md) - Contributing guidelines
- [CLAUDE.md](../../CLAUDE.md) - Development governance
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Vercel Deployment](https://vercel.com/docs)

## 🆘 Support

**For CI/CD issues:**
1. Check GitHub Actions logs
2. Review WORKFLOW_SETUP.md
3. Check CONTRIBUTING.md for test running
4. Create GitHub issue with error details

**For deployment issues:**
1. Check GitHub Actions deployment logs
2. Verify environment variables
3. Check health check endpoints
4. Review rollback logs

---

**Pipeline Version**: 1.0
**Last Updated**: 2026-03-06
**Maintainer**: DevOps Team
