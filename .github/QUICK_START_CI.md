# Quick Start: GitHub Actions CI/CD

Get the CI/CD pipeline running in 5 minutes.

## ⚡ 5-Minute Setup

### Step 1: Verify Files Are in Place (1 min)
```bash
# Check files exist
ls -la .github/workflows/
ls -la .pre-commit-config.yaml
ls -la .bandit
```

**Expected files**:
- ✅ `.github/workflows/ci.yml`
- ✅ `.github/workflows/deploy.yml`
- ✅ `.github/workflows/security.yml`
- ✅ `.github/WORKFLOW_SETUP.md`
- ✅ `.github/CONTRIBUTING.md`
- ✅ `.github/CICD_OVERVIEW.md`
- ✅ `.pre-commit-config.yaml`
- ✅ `.bandit`

### Step 2: Install Local Pre-Commit Hooks (2 min)
```bash
pip install pre-commit
pre-commit install

# Test it works
pre-commit run --all-files
```

### Step 3: Commit & Push (1 min)
```bash
git add .github/ .pre-commit-config.yaml .bandit requirements.txt CI_CD_IMPLEMENTATION_SUMMARY.md
git commit -m "ci: Setup GitHub Actions CI/CD pipeline with testing, linting, security scanning, and deployment"
git push origin feature-branch
```

### Step 4: Create PR on GitHub (1 min)
- Go to your GitHub repository
- Create a new Pull Request
- Watch CI run automatically ✅

## ✅ What Gets Checked

| Check | What | Status |
|-------|------|--------|
| Lint | Black, isort, flake8, ESLint | Auto-fix available |
| Type | mypy, TypeScript | Must fix manually |
| Tests | pytest, Vitest, Playwright | Must pass |
| Security | Gitleaks, secrets scan | Must pass |
| Build | Python syntax, Next.js | Must pass |

## 🚀 If All Checks Pass ✅

1. Request code review
2. Maintainer approves
3. Merge to main
4. **Staging deployment automatic** ✨
5. (Optional) Deploy to production with approval

## 🐛 If Checks Fail ❌

**For linting issues** (auto-fixable):
```bash
# Python
black backend/
isort backend/

# Frontend
cd frontend
npx prettier --write .
npm run lint -- --fix
```

**For test failures**:
```bash
# Run tests locally to debug
PYTHONPATH=. pytest backend/tests/ -v
cd frontend && npm run test:unit -- --reporter=verbose

# Fix issues, then push
git add .
git commit -m "fix: Address test failures"
git push
```

**For security issues**:
```bash
# Check GitHub Actions logs for details
# Remove secrets from code
# Use environment variables instead
# Push clean commit
```

## 📚 Learn More

- **Full setup**: Read [WORKFLOW_SETUP.md](./WORKFLOW_SETUP.md)
- **Architecture**: Read [CICD_OVERVIEW.md](./CICD_OVERVIEW.md)
- **Development**: Read [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Implementation details**: Read [CI_CD_IMPLEMENTATION_SUMMARY.md](../CI_CD_IMPLEMENTATION_SUMMARY.md)

## 🎯 Key Commands

```bash
# Run tests locally
PYTHONPATH=. pytest backend/tests/ -v
cd frontend && npm run test:unit

# Run linting
black --check backend/
cd frontend && npm run lint

# Format code
black backend/
isort backend/
cd frontend && npx prettier --write .

# Pre-commit (if installed)
pre-commit run --all-files

# Check CI status
gh run list --workflow=ci.yml
gh run view <run-id>
```

## 🔐 Configure Deployment (Optional)

To enable automatic staging & production deployment:

1. **For Vercel** (frontend):
   ```bash
   # Create Vercel project if not exists
   cd frontend
   vercel link
   ```

2. **Add GitHub Secrets** (`Settings` → `Secrets` → `Actions`):
   - `VERCEL_TOKEN` - From vercel.com/account/tokens
   - `VERCEL_ORG_ID` - From Vercel account
   - `VERCEL_PROJECT_ID_STAGING` - From Vercel project
   - `VERCEL_PROJECT_ID_PROD` - From Vercel project

3. **Update workflow**:
   - Edit `.github/workflows/deploy.yml`
   - Replace `https://tickerpulse.example.com/` with your domain

4. **Test it**:
   - Merge PR to main
   - Watch staging deployment ✅

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| `CI failed: pytest error` | Run `PYTHONPATH=. pytest backend/tests/ -v` locally to debug |
| `CI failed: ESLint error` | Run `npm run lint -- --fix` in frontend folder |
| `CI failed: Formatting error` | Run `black backend/` and `npm run prettier --write .` |
| `CI failed: Secrets detected` | Remove API keys from code, use env vars instead |
| `CI takes too long` | This is normal (3-5 min), E2E tests can take longer |

## 📊 What's Next?

✅ **Now that CI is working**:
1. Share CONTRIBUTING.md with your team
2. Configure branch protection on main (requires 1 review + passing checks)
3. (Optional) Set up Slack notifications for CI failures
4. (Optional) Configure deployment destinations

## 🎉 You're All Set!

Your repository now has:
- ✅ Automated testing on every commit
- ✅ Code quality enforcement
- ✅ Security scanning
- ✅ Automatic staging deployment
- ✅ Complete documentation

**Next PR you create will run CI automatically!**

---

Questions? Check the [WORKFLOW_SETUP.md](./WORKFLOW_SETUP.md) documentation.
