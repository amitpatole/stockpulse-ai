# VO-036: Fix Dependabot: upgrade vulnerable dependencies

## User Story

**As a** developer shipping the Virtual Office platform,
**I want** all flagged Dependabot vulnerabilities resolved by pinning dependencies to patched versions,
**so that** the application is not exposed to known CVEs for DoS attacks, credential leaks, session bypass, SSRF, or ASAR injection.

---

## Acceptance Criteria

**Backend (`backend/requirements.txt`)**
- [ ] `pypdf` pinned to `>=4.0.0` (resolves 10 CVEs: DoS via infinite loop, memory exhaustion, malformed PDF crashes); remove if confirmed unused after audit
- [ ] `requests` pinned to `>=2.32.0` (resolves credential leak via `.netrc` and session `verify=False` bypass)
- [ ] `flask` pinned to `>=3.1.0` (resolves session cookie signing vulnerability)
- [ ] `langchain-core` pinned to latest patched version resolving SSRF via prompt-injectable URLs (verify against PyPI advisory at time of merge)
- [ ] `pip install -r requirements.txt` succeeds with no dependency conflicts
- [ ] Backend starts and all existing API endpoints respond normally after upgrade

**Frontend (`electron/package.json`)**
- [ ] `electron` updated to the latest stable version resolving the ASAR integrity bypass CVE
- [ ] `npm install` succeeds in `electron/`
- [ ] Electron app builds and launches without regression

**Verification**
- [ ] Dependabot alerts for all 16 flagged vulnerabilities show as resolved after merging
- [ ] No new Dependabot alerts introduced by the version bumps
- [ ] Existing test suite passes (backend pytest + any frontend tests)

---

## Priority Reasoning

**High.** These are known CVEs with public exploits, not theoretical risks. The `requests` credential leak and `flask` session issue directly affect production auth integrity. The `pypdf` DoS vectors are exploitable by any user who can upload a PDF. `langchain-core` SSRF is a high-severity server-side risk given the AI pipeline. The Electron ASAR bypass matters for desktop distribution integrity. Version bumps are low-risk mechanical changes — delaying this is unjustifiable.

---

## Estimated Complexity: **2 / 5**

Pure version-bump work. No logic changes, no schema migrations, no new features. Main risk is transitive dependency conflicts (especially with `crewai` pinning its own versions of `langchain-core` and `requests`). Resolve with `pip-compile` or manual conflict resolution if needed. Frontend Electron bump may require minor build config updates if breaking changes exist in the release notes.

---

**Files to touch:** `backend/requirements.txt`, `electron/package.json`
