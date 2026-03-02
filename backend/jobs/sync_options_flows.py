"""
TickerPulse AI v3.0 - Options Flow Sync Job
Background job to periodically sync options flow data and generate alerts.
"""

import logging
from datetime import datetime

from backend.core.stock_manager import get_active_stocks
from backend.core.options_flow_manager import OptionsFlowManager
from backend.data_providers.options_provider import OptionsDataProvider

logger = logging.getLogger(__name__)


class OptionsFlowSyncJob:
    """Scheduled job to sync options flows and detect anomalies."""

    def __init__(self):
        """Initialize the job."""
        self.manager = OptionsFlowManager()
        self.provider = OptionsDataProvider()

    def execute(self) -> Dict:
        """Execute the sync job.

        Returns
        -------
        Dict
            Job result with flows_detected, alerts_created, errors
        """
        result = {
            "started_at": datetime.utcnow().isoformat(),
            "flows_detected": 0,
            "alerts_created": 0,
            "errors": [],
        }

        try:
            # Get list of active stocks
            stocks = get_active_stocks()
            logger.info(f"Starting options flow sync for {len(stocks)} stocks")

            for ticker in stocks:
                try:
                    # Get configuration for this stock
                    config = self.manager.get_config(ticker)

                    if not config.get("enabled"):
                        continue

                    # Fetch flows from provider
                    flows = self.provider.get_flows(ticker)
                    if not flows:
                        continue

                    # Process each flow
                    for flow in flows:
                        # Check if flow should trigger an alert
                        if flow.unusual_ratio >= config.get(
                            "volume_spike_threshold", 2.0
                        ):
                            # Create flow record
                            flow_id = self.manager.create_flow(
                                ticker=flow.ticker,
                                flow_type=flow.flow_type,
                                option_type=flow.option_type,
                                strike_price=flow.strike_price,
                                expiry_date=flow.expiry_date,
                                volume=flow.volume,
                                open_interest=flow.open_interest,
                                unusual_ratio=flow.unusual_ratio,
                                price_action=(
                                    "bullish"
                                    if flow.option_type == "call"
                                    else "bearish"
                                ),
                            )

                            if flow_id:
                                result["flows_detected"] += 1

                                # Calculate severity and create alert
                                severity = self.manager.calculate_severity(
                                    flow.unusual_ratio
                                )
                                message = (
                                    f"Unusual {flow.option_type} volume on "
                                    f"{ticker} ${flow.strike_price} "
                                    f"({flow.unusual_ratio:.1f}x average)"
                                )

                                alert_id = self.manager.create_alert(
                                    ticker=ticker,
                                    flow_id=flow_id,
                                    alert_type="volume_spike",
                                    severity=severity,
                                    message=message,
                                )

                                if alert_id:
                                    result["alerts_created"] += 1

                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                    result["errors"].append(
                        {
                            "ticker": ticker,
                            "message": str(e),
                        }
                    )

        except Exception as e:
            logger.error(f"Options flow sync job failed: {e}")
            result["errors"].append(
                {
                    "job": "sync",
                    "message": str(e),
                }
            )

        result["completed_at"] = datetime.utcnow().isoformat()
        logger.info(
            f"Options flow sync completed: {result['flows_detected']} flows, "
            f"{result['alerts_created']} alerts"
        )

        return result


# Job entry point (called by scheduler)
def sync_options_flows() -> Dict:
    """Execute options flow sync job."""
    job = OptionsFlowSyncJob()
    return job.execute()