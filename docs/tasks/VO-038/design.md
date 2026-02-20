# VO-038: Fix Dependabot: upgrade pypdf and other vulnerable dependencies

## Technical Design

Done. Here's the spec I wrote and the key decisions:

**`pypdf` audit-first approach**: It's not in either requirements file, so whoever picks this up should grep for direct imports before adding the constraint. If it's purely transitive via `yfinance` or `crewai`, an explicit `pypdf>=4.0.0` floor pin is the right fix — it forces pip's resolver to use a patched version without us claiming ownership of the dep.

**`langchain-core` needs explicit pinning**: Because `crewai` owns it transitively, bumping `crewai` alone isn't guaranteed to pull a patched `langchain-core` fast enough. Adding it as an explicit lower-bound in `backend/requirements.txt` overrides the transitive resolution. The "verify at merge time" note is intentional — the SSRF patch landed in a moving release window and the exact version should be confirmed against the CVE advisory, not hardcoded today.

**Two separate `requirements.txt` files**: Root `requirements.txt` and `backend/requirements.txt` both pin `flask==3.0.0` and `requests==2.31.0`. Both need the bump. Easy to miss the root one.

**Electron bump is a devDependency**: The ASAR bypass only affects the packaged installer build, not the running frontend JS. The risk surface is narrow, but the fix (^34.0.0) is straightforward.

**No test strategy theater**: The testing section is concrete commands, not "write unit tests." These CVE fixes don't need new test coverage — they need version verification and a conflict-free pip resolve.
