# Branch Protection Configuration

This document describes the GitHub branch protection settings needed to enforce CI/CD requirements.

## Required Settings

### Main Branch Protection

Go to **Settings > Branches > Branch protection rules > main**

#### Status Checks to Require

✅ **Required** (CI cannot be bypassed):
```
- Backend Lint & Type Check
- Frontend Lint & Type Check
- Backend Tests
- Frontend Unit Tests
- Backend Build
- Frontend Build
```

Optional (recommended):
```
- E2E Tests (only runs on PRs, non-blocking for direct pushes)
- Secrets Scanning (informational only)
- Security Scanning (informational only)
```

#### Require Approval Before Merging
- ✅ **Require pull request reviews before merging**
  - Required number of reviewers: **1**
  - Require review from code owners: **✅ (if CODEOWNERS exists)**
  - Dismiss stale reviews on new push: **❌ (keep reviews fresh)**
  - Require approval of most recent reviews only: **✅**

#### Additional Rules
- ✅ **Require branches to be up to date before merging**
  - Forces all PRs to merge with latest main
  - Prevents "stale branch" deploys

- ✅ **Require status checks to pass before merging**
  - CI must complete successfully
  - No "merge anyway" option

- ✅ **Require conversation resolution before merging**
  - All review comments must be addressed

- ❌ **Restrict who can push to matching branches**
  - Leave unchecked (let admins push if needed)

- ❌ **Require signed commits**
  - Optional if your org uses GPG signing

---

## Setup Instructions

### Using GitHub UI

1. Navigate to **Settings > Branches**
2. Click **Add rule** (or edit existing)
3. For **Branch name pattern**: `main`
4. Check the following:
   - ✅ Require pull request reviews before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require conversation resolution before merging
   - ✅ Require code reviews before merging (1 reviewer)
5. Add the required checks:
   - `Backend Lint & Type Check`
   - `Frontend Lint & Type Check`
   - `Backend Tests`
   - `Frontend Unit Tests`
   - `Backend Build`
   - `Frontend Build`
6. Click **Create** or **Save changes**

### Using GitHub CLI

```bash
# Install GitHub CLI
brew install gh
gh auth login

# Add branch protection
gh repo edit --enable-branch-protection-required-checks=main

# View current rules
gh repo view --json branchProtectionRules

# Add individual status check
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks \
  --input - << 'EOF'
{
  "strict": true,
  "contexts": [
    "Backend Lint & Type Check",
    "Frontend Lint & Type Check",
    "Backend Tests",
    "Frontend Unit Tests",
    "Backend Build",
    "Frontend Build"
  ]
}
EOF
```

---

## Typical Workflow

### What happens when you create a PR

1. ✅ **Branch is created** from main
   - CI automatically starts

2. ✅ **CI runs in parallel**
   - Lint checks (2-3 min)
   - Type checks (1-2 min)
   - Unit tests (5-8 min)
   - Total: ~8-10 minutes

3. ✅ **PR requires approval**
   - At least 1 team member must review
   - CI must pass
   - Branch must be up-to-date with main

4. ✅ **Merge button available only if**
   - All CI checks pass ✅
   - At least 1 approval ✅
   - Branch is up-to-date ✅
   - No unresolved conversations ✅

5. ✅ **Auto-deploy to staging**
   - After merge to main
   - Deploy workflow runs
   - Notifies team

### What you CANNOT do

❌ Cannot merge if CI is failing
❌ Cannot merge without approval
❌ Cannot merge stale branches
❌ Cannot bypass status checks
❌ Cannot merge with unresolved comments

---

## Troubleshooting

### "Required status check did not complete"

**Problem**: CI job exists in workflow but isn't showing as status check

**Solution**:
```bash
# Verify the job name matches exactly
# In ci.yml:
#   - name: Backend Lint & Type Check  ← This is the status check name

# View current status checks
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks
```

### "Cannot merge - branch is out of date"

**Fix**: Click "Update branch" button on PR
```bash
# Or locally
git fetch origin
git rebase origin/main
git push --force-with-lease
```

### "Waiting for status checks"

**Wait for CI to complete**:
- Check **Actions** tab
- Click workflow run
- Wait for all jobs to finish (green checkmarks)

### "Allowed all secrets check"

If you accidentally pushed secrets:
1. Rotate the secret immediately
2. Remove from git history (use `git filter-branch` or BFG)
3. Force push (requires admin)

---

## Develop Branch (Optional)

If you have a `develop` branch for staging:

### Settings for Develop

Go to **Settings > Branches > Add rule**

**Branch name pattern**: `develop`

**Different from main**:
- ✅ Status checks required (same as main)
- ✅ Pull request review: **0 reviewers** (less strict)
- ✅ Branches must be up to date: **❌ (optional for develop)**
- ❌ Do NOT dismiss stale reviews (develop moves faster)

This allows:
- Faster CI iteration
- Staging deployments
- Still prevents obvious errors

---

## Emergency Override (Use Sparingly)

### If CI is Broken (False Positive)

Only repo admins can:

1. Click **Dismiss review** on PR
2. Click **Bypass status checks** (if temporarily disabled)
3. Click **Merge anyway**

**After override**:
- Immediately investigate why CI failed
- Fix the root cause
- Re-enable protections
- Document the incident

---

## CODEOWNERS Integration

Create `.github/CODEOWNERS` to require specific team reviews:

```
# Require backend team to review Python changes
backend/ @team/backend-team

# Require frontend team to review UI changes
frontend/src/ @team/frontend-team

# Require devops to review CI/CD changes
.github/workflows/ @devops-team

# Require both security teams to review auth/security
backend/core/security.py @security-team
```

Then enable in branch protection:
- ✅ **Require review from code owners**

---

## Best Practices

### For Small Teams (< 5 engineers)
- 1 review required
- Status checks required
- Dismiss stale reviews disabled

### For Medium Teams (5-20 engineers)
- 2 reviews required (1 code, 1 QA)
- Status checks required
- Code owners specified
- Branch must be up to date

### For Large Teams (> 20 engineers)
- 2-3 reviews required
- Full status check matrix
- Enforce signed commits
- Require protected branch policy

---

## Automation Rules

After you set up branch protection, GitHub will:

| Action | Result |
|--------|--------|
| Push to main directly | ❌ Blocked |
| Force push to main | ❌ Blocked |
| Merge PR without review | ❌ Blocked |
| Merge PR with failing tests | ❌ Blocked |
| Merge stale PR | ❌ Blocked |
| Merge with approved review | ✅ Allowed |
| Auto-delete head branch | ✅ Auto-deletes (optional) |

---

## Monitoring Compliance

### Weekly Checklist

- [ ] All PRs have at least 1 review
- [ ] No force pushes to main
- [ ] All merges have passing CI
- [ ] No emergency overrides
- [ ] Failed CI runs investigated

### GitHub Insights

View merged PRs stats:
```bash
gh pr list --state merged --limit 50
gh api repos/{owner}/{repo}/pulls \
  --method GET \
  --input - -q '.[] | {number, title, merged_at}'
```

---

## Related Documentation

- **CI/CD Pipeline**: `docs/CI_CD_PIPELINE.md`
- **Quick Start**: `docs/QUICK_START_CI.md`
- **Testing Guide**: `documentation/24-testing.md`
- **Git Operations**: `documentation/21-git-operations.md`

---

**Last Updated**: 2026-03-06
**Maintained By**: DevOps Team
