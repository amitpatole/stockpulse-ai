"""
PagerDuty Events API v2 wrapper for infra alerting (VO-036).

Usage:
    alerter = PagerDutyAlerter(routing_key="<your-integration-key>")
    alerter.trigger(
        summary="CT 300 provisioning failed after 3 attempts",
        severity="critical",
    )
"""

import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_PAGERDUTY_EVENTS_URL = "https://events.pagerduty.com/v2/enqueue"


class PagerDutyAlerter:
    """Thin wrapper around PagerDuty Events API v2 trigger action."""

    def __init__(self, routing_key: str) -> None:
        self._routing_key = routing_key

    def trigger(
        self,
        *,
        summary: str,
        severity: str = "critical",
        source: str = "lxc-provisioner",
        **details,
    ) -> None:
        """Send a trigger event to PagerDuty."""
        payload = {
            "routing_key": self._routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": source,
                **details,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            _PAGERDUTY_EVENTS_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info("PagerDuty accepted alert: %s", resp.read())
        except urllib.error.URLError as exc:
            logger.error("PagerDuty alert delivery failed: %s", exc)
