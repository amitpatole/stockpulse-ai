# GitHub Actions CI/CD Pipeline Setup

This document explains the GitHub Actions workflows set up for TickerPulse and how to configure them for your environment.

## 📋 Overview

Three main workflows are configured:

1. **CI Pipeline** (`.github/workflows/ci.yml`)
   - Runs on: All pushes to `main` and `develop`, all pull requests
   - Tests: Backend (pytest), Frontend (vitest), E2E (playwright)
   - Linting: ESLint, Black, isort, flake8
   - Type checking: TypeScript, mypy
   - Security: Gitleaks, hardcoded secret detection

2. **Deploy Pipeline** (`.github/workflows/deploy.yml`)
   - Runs on: Successful CI completion on `main` branch
   - Deploys frontend to Vercel (staging and production)
   - Supports backend deployment to Railway, Render, AWS, etc.
   - Includes health checks and rollback on failure

3. **Security Pipeline** (`.github/workflows/security.yml`)
   - Runs on: Daily schedule + PR/push events
   - Dependency scanning (safety, pip-audit)
   - SAST: Bandit (Python), Semgrep, ESLint security
   - Container scanning (if using Docker)

## 🔧 Configuration Steps

### 1. Basic Setup (No Changes Needed)

The CI pipeline works out-of-the-box for:
- Testing (pytest, vitest, playwright)
- Linting (ESLint, Black, isort)
- Building (npm, Python)
- Security scanning (gitleaks)

### 2. Configure Deployment (Optional)

If you want to deploy your application, follow these steps:

#### For Frontend Deployment to Vercel:

1. Create or link a Vercel project:
   ```bash
   vercel login
   cd frontend
   vercel link
   ```

2. Add secrets to your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):
   ```
   VERCEL_TOKEN          # From vercel.com/account/tokens
   VERCEL_ORG_ID         # From Vercel project settings
   VERCEL_PROJECT_ID_STAGING  # Staging project ID
   VERCEL_PROJECT_ID_PROD     # Production project ID
   ```

3. Update `.github/workflows/deploy.yml`:
   - Replace `https://tickerpulse.example.com/` with your actual domain
   - Update API health check URL if needed

#### For Backend Deployment:

Choose one of these platforms:

**Option A: Railway**
```bash
railway login
railway link
```
Add secrets:
- `RAILWAY_TOKEN` from `railway.app/account/tokens`

Update deploy.yml with:
```bash
railway up --service backend
```

**Option B: Render**
```bash
# Create a render.yaml in root
```
Add secrets:
- `RENDER_API_KEY` from `render.com/account`

**Option C: AWS Lambda**
Add secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Option D: Heroku**
```bash
heroku login
heroku create tickerpulse
```
Add secrets:
- `HEROKU_API_KEY` from `heroku.com/account`

### 3. Configure Environment Variables

Create a `.env.example` file and add to GitHub secrets:

```bash
# .env.example (checked in)
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=<change-in-production>
DATABASE_URL=<your-database-url>
CORS_ORIGINS=https://yourdomain.com

# Sensitive values (as GitHub secrets)
SECRET_KEY → GitHub Secret
API_KEY → GitHub Secret (if applicable)
```

### 4. Set Up Branch Protection Rules

In GitHub repository settings (`Settings` → `Branches` → `main`):

```
✅ Require status checks to pass before merging:
  - backend-lint
  - backend-tests
  - backend-build
  - frontend-lint
  - frontend-tests
  - frontend-build
  - security

✅ Require code reviews before merging (1 approver minimum)
✅ Dismiss stale pull request approvals
✅ Require branches to be up to date before merging
```

## 📊 Workflow Status Badges

Add to your README.md:

```markdown
![CI](https://github.com/your-org/tickerpulse/actions/workflows/ci.yml/badge.svg)
![Deploy](https://github.com/your-org/tickerpulse/actions/workflows/deploy.yml/badge.svg)
![Security](https://github.com/your-org/tickerpulse/actions/workflows/security.yml/badge.svg)
```

## 🚀 Running Workflows Manually

### Trigger specific workflow:

1. Go to GitHub repository
2. Click `Actions` tab
3. Select workflow name
4. Click `Run workflow` button

### Via GitHub CLI:

```bash
# List workflows
gh workflow list

# Run workflow
gh workflow run ci.yml --ref main

# View workflow run
gh run list --workflow=ci.yml
gh run view <run-id>
```

## 📝 Workflow Files Reference

### CI Workflow (`.github/workflows/ci.yml`)

| Job | Purpose | Triggers |
|-----|---------|----------|
| backend-lint | Python formatting & linting | All events |
| backend-tests | Run pytest test suite | After lint succeeds |
| frontend-lint | TypeScript & ESLint checks | All events |
| frontend-tests | Run Vitest unit tests | After lint succeeds |
| frontend-build | Build Next.js application | After tests succeed |
| backend-build | Verify Python syntax & imports | After tests succeed |
| security | Gitleaks & secret detection | All events |
| e2e-tests | Run Playwright E2E tests | PR/main only |
| status-check | Final CI status | After all jobs |

### Deploy Workflow (`.github/workflows/deploy.yml`)

| Job | Purpose | Condition |
|-----|---------|-----------|
| deploy-staging | Deploy to staging | CI passes on main |
| deploy-production | Deploy to production | Requires approval |
| post-deploy-health-check | Verify deployment | After production deploy |
| rollback-on-failure | Rollback on failure | If deployment fails |

### Security Workflow (`.github/workflows/security.yml`)

| Job | Purpose | Schedule |
|-----|---------|----------|
| dependency-scan | Safety check Python deps | PR/push/daily |
| sast-python | Static analysis (Python) | PR/push/daily |
| sast-javascript | Static analysis (JS/TS) | PR/push/daily |
| secrets-scan | Gitleaks detection | PR/push/daily |
| dependency-check | npm audit, pip-audit | PR/push/daily |
| container-scan | Trivy Docker scan | If Dockerfile exists |
| security-summary | Generate report | Always |

## ⚙️ Customization Examples

### Example 1: Run Tests with Coverage Threshold

Edit `backend-tests` job in `ci.yml`:

```yaml
- name: Run pytest with coverage
  run: |
    PYTHONPATH=. pytest backend/tests/ \
      -v \
      --cov=backend \
      --cov-report=xml \
      --cov-fail-under=80  # Fail if coverage < 80%
```

### Example 2: Custom Python Version Matrix

Edit `backend-tests` job:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']

steps:
  - uses: actions/setup-python@v4
    with:
      python-version: ${{ matrix.python-version }}
```

### Example 3: Slack Notification on Failure

Add to any job:

```yaml
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "❌ CI failed for ${{ github.repository }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Build Failed*\nBranch: ${{ github.ref }}\nCommit: ${{ github.sha }}"
            }
          }
        ]
      }
```

### Example 4: Deploy Only on Tag

Edit `deploy.yml`:

```yaml
on:
  push:
    tags:
      - 'v*'  # Deploy on version tags (v1.0.0, etc)
```

## 📚 Troubleshooting

### CI Job Fails: "PYTHONPATH issue"

**Solution**: Ensure `PYTHONPATH=.` is set:

```yaml
run: PYTHONPATH=. pytest backend/tests/
```

### Frontend Build Fails: "npm ERR!"

**Solution**: Clear cache and reinstall:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Playwright E2E Tests Timeout

**Solution**: Increase timeout or retry:

```yaml
- name: Run E2E tests
  run: npm run test:e2e -- --timeout=60000 --retries=2
```

### Deployment Fails: "VERCEL_TOKEN not found"

**Solution**: Add secrets in GitHub:

1. Go to repo `Settings` → `Secrets and variables` → `Actions`
2. Click `New repository secret`
3. Add `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID_PROD`

### Security Scan Too Noisy

**Solution**: Configure bandit/semgrep to ignore certain issues:

Create `.bandit` in root:
```yaml
exclude_dirs: [tests, venv]
skips: [B101]  # Skip assertions check
```

## 🔐 Security Best Practices

1. **Never commit secrets** - Use GitHub secrets only
2. **Use environment variables** - For all configuration
3. **Rotate credentials** - Regularly update tokens
4. **Review secrets access** - Limit who can view secrets
5. **Audit logs** - Check "Security" → "Audit log" in GitHub
6. **Branch protection** - Require status checks + code review

## 📖 Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Development governance
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel Deployment Docs](https://vercel.com/docs)
- [Playwright Testing](https://playwright.dev/)
- [Pytest Documentation](https://docs.pytest.org/)

## 🆘 Getting Help

- Check GitHub Actions logs: Click on failed job → expand logs
- Review error messages for specific issues
- Consult workflow documentation above
- Check platform-specific docs (Vercel, Railway, etc.)

---

**Last Updated**: 2026-03-06
**Maintainer**: DevOps Team
