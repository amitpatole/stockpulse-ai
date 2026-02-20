# VO-036: Infra: LXC exception — provisioning (VO-002)

## User Story

## User Story: VO-002 — LXC Provisioning Lock Timeout

---

**As a** DevOps engineer,
**I want** the container provisioning system to detect and resolve stale LXC lock files automatically,
**so that** container creation failures due to lock timeouts are self-healing and don't require manual intervention.

---

### Acceptance Criteria

- [ ] Before provisioning CT 300 (or any VMID), the system checks for the existence of `/run/lock/lxc/pve-config-<VMID>.lock`
- [ ] If a stale lock is detected (no active process holding it), the system removes it automatically and logs the action
- [ ] If a valid lock is held by an active process, provisioning is queued or aborted with a clear error — never silently fails
- [ ] Retry logic includes a pre-flight lock check before each attempt (not just on failure)
- [ ] Lock resolution attempts are bounded (max 3 retries, with backoff) to avoid infinite loops
- [ ] All lock events (detected, cleared, blocked) are emitted to the incident log with timestamp and VMID
- [ ] If the Proxmox LXC daemon is unresponsive, the system escalates to a PagerDuty/alerting channel rather than silently destroying the container

---

### Priority Reasoning

**High.** This is a provisioning blocker — every failed container creation wastes infrastructure resources, generates noise in incident logs, and delays feature work (in this case, VO-002 was blocked entirely). Stale lock files are a predictable, recurring failure mode in Proxmox environments. This is low-hanging fruit with high reliability ROI.

---

### Estimated Complexity: **2 / 5**

Lock detection and cleanup is well-understood. The main work is integrating the pre-flight check into the provisioning pipeline and wiring up alerting for the daemon-unresponsive edge case. No architectural changes needed.

---

**Owner:** DevOps / Infra team
**Linked incident:** VO-002
**Retry recommended:** Yes — after lock check logic is in place.
