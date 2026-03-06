# CI/CD Quick Start Guide

## What is CI/CD?

**Continuous Integration (CI)**: Automated testing and validation on every commit
**Continuous Deployment (CD)**: Automated deployment to staging/production when tests pass

TickerPulse uses GitHub Actions to run tests before code merges.

---

## Local Development Workflow

### Before Committing Code

```bash
# Format Python code
black backend/
isort backend/

# Format TypeScript/JavaScript
cd frontend && npm run format && cd ..

# Type check
cd frontend && npx tsc --noEmit && cd ..

# Run tests locally
PYTHONPATH=. pytest backend/tests/ -v
cd frontend && npm run test:unit -- --run && cd ..
```

### Or Run All Checks At Once

```bash
# Backend
black backend/ && \
isort backend/ && \
PYTHONPATH=. pytest backend/tests/ -v && \
echo "✅ Backend checks passed"

# Frontend
cd frontend && \
npm run format && \
npm run lint && \
npm run test:unit -- --run && \
echo "✅ Frontend checks passed"
```

---

## Understanding CI Failures

When a GitHub Actions workflow fails, check:

1. **Which job failed?** (Lint, Test, Build?)
2. **View the logs** on GitHub Actions tab
3. **Reproduce locally** with the same commands
4. **Fix the issue** and push again

### Common Failures

| Failure | Cause | Fix |
|---------|-------|-----|
| `Black formatting check failed` | Code formatting doesn't match Black style | `black backend/` |
| `isort check failed` | Imports not sorted correctly | `isort backend/` |
| `mypy type check failed` | Type annotation mismatch | Add missing types |
| `pytest failed` | Test assertion failed | Fix test or implementation |
| `ESLint failed` | JavaScript/TypeScript lint error | Fix linting issue or ignore if false positive |
| `Prettier check failed` | Code formatting doesn't match | `cd frontend && npm run format` |
| `tsc failed` | TypeScript compilation error | Fix TypeScript errors |
| `Coverage threshold failed` | Code coverage below 70% | Add tests for uncovered lines |

---

## Running CI Locally with `act`

### Install `act`

```bash
# macOS
brew install act

# Linux (ubuntu)
sudo apt install act

# Windows (with WSL)
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash
```

### Run Specific Jobs

```bash
# Run all CI jobs
act

# Run specific job
act -j lint-backend
act -j test-backend
act -j test-frontend

# Run with custom event
act -e "push"  # Simulate push event

# List all jobs
act -l
```

### Troubleshooting `act`

```bash
# If Docker not found
act --docker-host unix:///var/run/docker.sock

# If containers fail
act --rm  # Clean up old containers

# Verbose output
act -v

# Run single step
act -j test-backend -s "Run pytest with coverage"
```

---

## GitHub Actions Secrets

### Viewing Secrets

Go to **Settings > Secrets and variables > Actions**

Required secrets for deployment:
- `VERCEL_TOKEN` - Vercel deployment token
- `VERCEL_ORG_ID` - Your Vercel organization
- `VERCEL_PROJECT_ID_STAGING` - Staging project ID
- `VERCEL_PROJECT_ID_PROD` - Production project ID

### Adding a New Secret

1. Go to **Settings > Secrets and variables > Actions**
2. Click **New repository secret**
3. Enter `Name` and `Value`
4. Click **Add secret**

### Using Secrets in Workflows

```yaml
- name: Deploy
  run: ./deploy.sh
  env:
    VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

---

## Monitoring Workflows

### View Running Workflows

```bash
# GitHub CLI (if installed)
gh run list

# View specific workflow
gh run view <run-id>

# Watch logs
gh run watch <run-id>
```

### Get Notified of Failures

1. Click **⭐ Star** this repository (notifications enabled by default)
2. Go to **Settings > Notifications**
3. Enable "Branch pushed" + "Pull request reviews" notifications
4. Failures will show in your GitHub notifications

---

## Skipping CI for Quick Fixes

### Skip All Checks (NOT RECOMMENDED)

Add `[skip ci]` to commit message:

```bash
git commit -m "docs: Update README [skip ci]"
git push
```

**Use only for:**
- Documentation-only changes
- README updates
- Comments in code

**Never skip for:**
- Code changes
- Test changes
- Configuration changes

---

## PR Review Checklist

Before approving a PR, verify:

- [ ] All CI checks are passing (green checkmark)
- [ ] Code coverage >= 70% (backend)
- [ ] No merge conflicts
- [ ] No hardcoded secrets (gitleaks passed)
- [ ] Linting passed (Black, isort, ESLint)
- [ ] Tests passed (backend + frontend)
- [ ] E2E tests passed
- [ ] No new console.log statements

---

## Next Steps

- Read **docs/CI_CD_PIPELINE.md** for detailed architecture
- Check **.github/workflows/ci.yml** for exact steps
- Review **docs/testing.md** for testing best practices
- Ask in #engineering-help if you get stuck

---

## Useful Commands

```bash
# View GitHub Actions status (requires gh CLI)
gh run list --limit 5

# Install GitHub CLI on macOS
brew install gh

# Authenticate
gh auth login

# View workflow for a specific commit
gh run view -n 1

# Check branch protection rules
gh repo view --json branchProtectionRules
```

---

**Last Updated**: 2026-03-06
