# VO-038: Fix Dependabot: upgrade pypdf and other vulnerable dependencies

## User Story

Done. Here's what I wrote and why each decision was made:

**User story framing:** Targeted at the developer/ops persona — this isn't a user-facing feature, it's a supply chain security fix. The "so that" clause names the concrete attack classes, not vague "security improvements."

**Acceptance criteria highlights:**
- Explicitly calls out the audit step for `pypdf` (remove if unused — no point keeping a dependency that's flagged if we don't need it)
- `langchain-core` is flagged to verify at merge time since the patched version is a moving target with the `crewai` ecosystem
- Includes startup smoke test and Dependabot alert resolution as explicit done criteria — too many "dependency update" PRs get merged without confirming the alerts actually close

**Complexity at 2/5:** The real risk here is transitive conflicts with `crewai`, which bundles its own `langchain-core` and `requests` pins. Called that out so whoever picks this up isn't surprised.

**Priority:** High, no hedging. 16 CVEs with public exploits sitting in production is not a "when we get to it" situation.
