# VO-036: Infra: LXC exception — provisioning (VO-002)

## Technical Design

Here's the design spec written to `docs/tasks/VO-002/design.md`:

---

**Approach:** A new `LxcLockGuard` class in `scripts/infra/lxc_provisioner.py` — entirely outside the application codebase. It performs a pre-flight lock check before every provisioning attempt by reading the lock file's PID and probing `/proc/<pid>`. Stale locks (no matching `/proc` entry) are cleared automatically. Valid locks escalate immediately. A bounded retry loop (max 3, exponential backoff) wraps the Proxmox API call, and the daemon-unresponsive path escalates to PagerDuty.

**Files to create** (all net-new, no existing code touched):

| File | Purpose |
|---|---|
| `scripts/infra/lxc_provisioner.py` | `LxcLockGuard` + `provision_container()` |
| `scripts/infra/incident_log.py` | Structured JSONL event emitter |
| `scripts/infra/alerting.py` | PagerDuty Events API v2 wrapper |
| `scripts/infra/__init__.py` | Package marker |
| `backend/tests/infra/test_lxc_provisioner.py` | Full pytest suite, all I/O mocked |

**Data model:** None. Lock state is filesystem-ephemeral. Events append to existing `logs/backend.log` (standard Python `logging`) plus a new `logs/infra-incidents.jsonl` for structured querying.

**API / Frontend:** No changes. The provisioner is a CI/CD-invoked script, not an HTTP endpoint.

**Testing:** 7 focused pytest cases covering happy path, stale clear, live lock blocking, retry with backoff, 3-strike escalation, bounds enforcement, and audit trail emission — all with mocked Proxmox API, `os.remove`, `os.path.exists`, and `time.sleep`. Zero real I/O in tests.
