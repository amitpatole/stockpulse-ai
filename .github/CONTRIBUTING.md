# Contributing to TickerPulse

Thank you for contributing to TickerPulse! This guide explains how to develop features, run tests locally, and submit pull requests.

## 🚀 Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/tickerpulse.git
   cd tickerpulse
   ```

2. **Set up development environment**
   ```bash
   # Python
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Node.js
   cd frontend
   npm install
   ```

3. **Install pre-commit hooks** (strongly recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Create feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

## 📝 Development Workflow

### 1. Documentation First

Before writing code, read the relevant documentation:

- **New Feature?** → Create/read `documentation/NN-feature-name.md`
- **API Changes?** → Update `documentation/09-api-guidelines.md`
- **Database?** → Check `documentation/08-database-schema.md`
- **Security?** → Review `documentation/10-security.md`

See [CLAUDE.md](../../CLAUDE.md) for all feature documentation.

### 2. Write Code

Follow the conventions:

**Python (Backend)**
```python
# Use type hints
def get_stocks(limit: int = 20, offset: int = 0) -> list[Stock]:
    """Fetch stocks with pagination.

    Args:
        limit: Maximum number of stocks to return (max 100)
        offset: Number of stocks to skip

    Returns:
        List of Stock objects
    """
    pass

# Use async/await for I/O operations
async def fetch_from_api(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
```

**TypeScript (Frontend)**
```typescript
// Use strict TypeScript
interface Stock {
  ticker: string;
  name: string;
  price: number;
}

export const StockCard: React.FC<{ stock: Stock }> = ({ stock }) => {
  return <div>{stock.name}</div>;
};

// No `any` types
const data: Record<string, unknown> = {};  // ✅ Good
const data: any = {};  // ❌ Bad
```

### 3. Write Tests

**Unit Tests (Backend)**
```python
# backend/tests/test_stocks.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_db():
    with patch('backend.database.get_connection') as mock:
        yield mock

def test_get_stocks_pagination(mock_db):
    """Test that pagination limits results."""
    # Arrange
    mock_db.execute.return_value = [
        {'ticker': 'AAPL', 'name': 'Apple'},
        {'ticker': 'MSFT', 'name': 'Microsoft'},
    ]

    # Act
    result = get_stocks(limit=2, offset=0)

    # Assert
    assert len(result) == 2
    mock_db.execute.assert_called_once()
```

**Unit Tests (Frontend)**
```typescript
// frontend/src/components/__tests__/StockCard.test.tsx
import { render, screen } from '@testing-library/react';
import { StockCard } from '../StockCard';

test('displays stock name and price', () => {
  const stock = { ticker: 'AAPL', name: 'Apple', price: 150 };
  render(<StockCard stock={stock} />);

  expect(screen.getByText('Apple')).toBeInTheDocument();
  expect(screen.getByText('150')).toBeInTheDocument();
});
```

**E2E Tests (Playwright)**
```typescript
// e2e/stocks.spec.ts
import { test, expect } from '@playwright/test';

test('user can add and view stock', async ({ page }) => {
  await page.goto('/dashboard');

  // Add stock
  await page.click('button[aria-label="Add Stock"]');
  await page.fill('input[placeholder="Stock ticker"]', 'AAPL');
  await page.click('button:has-text("Add")');

  // Verify added
  await expect(page.locator('text=Apple')).toBeVisible();
});
```

### 4. Run Tests Locally

**Backend Tests**
```bash
# All tests
PYTHONPATH=. pytest backend/tests/ -v

# Specific test file
PYTHONPATH=. pytest backend/tests/test_stocks.py -v

# Single test
PYTHONPATH=. pytest backend/tests/test_stocks.py::test_get_stocks_pagination -v

# With coverage
PYTHONPATH=. pytest backend/tests/ --cov=backend --cov-report=html
```

**Frontend Tests**
```bash
cd frontend

# All unit tests
npm run test:unit

# Watch mode
npm run test:unit -- --watch

# With coverage
npm run test:unit -- --coverage
```

**E2E Tests**
```bash
cd frontend

# All E2E tests (requires running backend)
npm run test:e2e

# Specific test file
npm run test:e2e -- e2e/stocks.spec.ts

# Interactive mode (Playwright Inspector)
npm run test:e2e -- --debug
```

### 5. Lint and Format

**Format code locally**
```bash
# Python
black backend/
isort backend/

# JavaScript/TypeScript
cd frontend
npx prettier --write .
```

**Check linting without fixing**
```bash
# Python
flake8 backend/
black --check backend/

# JavaScript
cd frontend
npm run lint
npx prettier --check .
```

### 6. Commit Changes

Write good commit messages:

```bash
# ❌ Bad
git commit -m "fix stuff"
git commit -m "update"

# ✅ Good
git commit -m "feat: Add pagination to stocks API"
git commit -m "fix: Handle null values in price calculations"
git commit -m "test: Add unit tests for stock validation"
git commit -m "docs: Update API documentation for new endpoints"
```

**Commit message format**: `{type}: {description}`

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvement
- `chore:` - Build, dependencies, etc.

### 7. Push and Create Pull Request

```bash
git push origin feat/your-feature-name
```

Then:
1. Go to GitHub and open a pull request
2. Fill in the PR template (title, description, checklist)
3. Link related issues: `Closes #123`
4. Wait for CI to pass (all checks green ✅)

## 🧪 CI/CD Pipeline

Your code is automatically tested by GitHub Actions:

### CI Runs On:
- Every push to `main` or `develop`
- Every pull request to `main` or `develop`

### What CI Tests:

| Check | What It Does | Status |
|-------|------------|--------|
| Backend Lint | Black, isort, flake8 | ⚠️ Warning (doesn't block) |
| Backend Tests | pytest suite | 🛑 Blocking |
| Backend Build | Python syntax check | 🛑 Blocking |
| Frontend Lint | ESLint, Prettier | ⚠️ Warning (doesn't block) |
| Frontend Tests | Vitest suite | 🛑 Blocking |
| Frontend Build | Next.js build | 🛑 Blocking |
| Security | Gitleaks, secret detection | 🛑 Blocking |
| E2E Tests | Playwright (PRs & main only) | ⚠️ Warning (doesn't block) |

**Blocking checks must pass** before you can merge. You can see the status on your PR.

### Fixing CI Failures

**Test Failure?**
```bash
# Run tests locally to debug
PYTHONPATH=. pytest backend/tests/test_file.py::test_name -v -s
cd frontend && npm run test:unit -- --reporter=verbose
```

**Lint Failure?**
```bash
# Auto-fix formatting
black backend/
isort backend/
cd frontend && npx prettier --write .
```

**Build Failure?**
```bash
# Check for syntax errors
python -m py_compile backend/file.py
cd frontend && npm run build
```

## 📋 Pull Request Checklist

Before submitting your PR, verify:

- [ ] **Documentation Updated**
  - [ ] Feature documented in `documentation/`
  - [ ] README updated if needed
  - [ ] API docs updated if applicable

- [ ] **Code Quality**
  - [ ] Code follows style guide (lint passes locally)
  - [ ] No hardcoded secrets or API keys
  - [ ] No console.log in production code
  - [ ] TypeScript/Python types all correct
  - [ ] Comments explain *why*, not *what*

- [ ] **Testing**
  - [ ] Unit tests written and passing
  - [ ] Tests run locally: `pytest` and `npm run test:unit`
  - [ ] E2E tests written if user-facing
  - [ ] Edge cases covered

- [ ] **Git Hygiene**
  - [ ] Branch name follows pattern: `feat/`, `fix/`, `docs/`
  - [ ] Commits are atomic and descriptive
  - [ ] No merge commits (rebase if needed)
  - [ ] No large files (>10MB) committed

## 🔍 Code Review

During code review, we check:

1. **Does it match the documentation?** (spec compliance)
2. **Is it tested?** (unit + E2E coverage)
3. **Is it secure?** (no injection, proper validation)
4. **Is it performant?** (no N+1 queries, proper caching)
5. **Is it maintainable?** (clear code, good names, documented)

## 🚀 After Merge

Once your PR is merged to `main`:

1. **CI runs** - All tests, lint, security checks
2. **Staging deploys** - Your changes go live on staging environment
3. **Production ready** - After human approval, deploys to production
4. **Cleanup** - Your branch is deleted

## 📚 Additional Resources

- [CLAUDE.md](../../CLAUDE.md) - Development governance & conventions
- [.github/WORKFLOW_SETUP.md](./../WORKFLOW_SETUP.md) - CI/CD detailed configuration
- [Playwright Docs](https://playwright.dev/)
- [Pytest Docs](https://docs.pytest.org/)
- [Next.js Docs](https://nextjs.org/docs)

## 💬 Questions?

- Check [CLAUDE.md](../../CLAUDE.md) FAQ section
- Review existing pull requests for examples
- Ask in GitHub Issues
- Check CI logs for specific errors

## ⚠️ Important Rules

1. **Never push to main directly** - Use pull requests only
2. **Never commit secrets** - Pre-commit hooks will block them
3. **All tests must pass** - CI requirements are enforced
4. **Code reviews are mandatory** - Requires at least 1 approval
5. **Document before code** - Update docs as you code

---

**Thank you for contributing!** 🎉

Every PR helps make TickerPulse better for everyone. We appreciate your time and effort!
