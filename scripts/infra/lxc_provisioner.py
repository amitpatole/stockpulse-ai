"""
LXC container provisioner with pre-flight lock guard (VO-036 / VO-002).

Resolves the Proxmox lock-timeout failure mode by:
  1. Detecting stale /run/lock/lxc/pve-config-<VMID>.lock files before
     each provisioning attempt and removing them automatically.
  2. Blocking immediately when the lock is held by a live process.
  3. Wrapping the Proxmox API call in a bounded retry loop (max 3,
     exponential backoff: 2 s, 4 s) and escalating to PagerDuty on
     exhaustion.
"""

import logging
import os
import time

from scripts.infra.alerting import PagerDutyAlerter
from scripts.infra.incident_log import IncidentLog

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_LOCK_DIR = "/run/lock/lxc"


class LxcLockGuard:
    """Pre-flight checker that clears stale LXC lock files or raises on live locks."""

    def __init__(self, vmid: int, lock_dir: str = _LOCK_DIR) -> None:
        self.vmid = vmid
        self.lock_dir = lock_dir
        self.lock_path = f"{lock_dir}/pve-config-{vmid}.lock"

    def ensure_clear(self) -> None:
        """Ensure the lock file is absent or stale (and remove it).

        Raises:
            RuntimeError: if the lock is held by an active process.
        """
        if not os.path.exists(self.lock_path):
            return

        # Attempt to read the PID stored in the lock file.
        try:
            with open(self.lock_path) as fh:
                pid_str = fh.read().strip()
            pid = int(pid_str)
        except (OSError, ValueError):
            # Unreadable or non-integer content → treat as stale.
            logger.warning(
                "Stale LXC lock at %s (unreadable PID); removing.", self.lock_path
            )
            os.remove(self.lock_path)
            return

        proc_path = f"/proc/{pid}"
        if os.path.exists(proc_path):
            raise RuntimeError(
                f"LXC lock held by live process PID {pid} at {self.lock_path}"
            )

        # No /proc entry → process is gone; lock is stale.
        logger.warning(
            "Stale LXC lock at %s (PID %d not in /proc); removing.", self.lock_path, pid
        )
        os.remove(self.lock_path)


def provision_container(
    proxmox_client,
    *,
    vmid: int,
    config: dict,
    pagerduty_key: str | None = None,
    lock_dir: str = _LOCK_DIR,
) -> dict:
    """Provision an LXC container via the Proxmox API with lock guard and retry.

    Args:
        proxmox_client: Proxmox API client with a ``create_container(vmid, config)``
            method.
        vmid: Container VMID (e.g. 300).
        config: Container configuration dict passed verbatim to the API.
        pagerduty_key: PagerDuty integration routing key.  When provided and all
            retries are exhausted, a critical alert is triggered.
        lock_dir: Directory that holds LXC lock files.

    Returns:
        The dict returned by ``proxmox_client.create_container()``.

    Raises:
        RuntimeError: propagated from the last failed API call, or immediately
            if a live lock is detected.
    """
    log = IncidentLog()
    guard = LxcLockGuard(vmid=vmid, lock_dir=lock_dir)

    last_exc: RuntimeError | None = None

    for attempt in range(_MAX_RETRIES):
        # Pre-flight lock check — raises immediately for live locks.
        guard.ensure_clear()

        try:
            result = proxmox_client.create_container(vmid, config)
            log.emit({"event": "container_provisioned", "vmid": vmid, "attempt": attempt})
            return result
        except RuntimeError as exc:
            last_exc = exc
            log.emit(
                {
                    "event": "provisioning_attempt_failed",
                    "vmid": vmid,
                    "attempt": attempt,
                    "error": str(exc),
                }
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(2 ** (attempt + 1))

    # All retries exhausted.
    log.emit(
        {
            "event": "provisioning_failed_all_retries",
            "vmid": vmid,
            "max_retries": _MAX_RETRIES,
            "error": str(last_exc),
        }
    )

    if pagerduty_key:
        alerter = PagerDutyAlerter(routing_key=pagerduty_key)
        alerter.trigger(
            summary=f"CT {vmid} provisioning failed after {_MAX_RETRIES} attempts",
            severity="critical",
        )

    raise last_exc  # type: ignore[misc]
