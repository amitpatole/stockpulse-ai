```python
"""
TickerPulse AI - Options Flow Analyzer
Detects anomalous options activity and scores severity.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from backend.database import db_session
from backend.data_providers.options_provider import OptionsDataProvider, OptionContract

logger = logging.getLogger(__name__)


@dataclass
class AnomalyDetectionResult:
    """Result of analyzing a contract for anomalies."""
    contract: OptionContract
    flow_type: str  # 'unusual_volume' | 'large_trade' | 'put_call_imbalance'
    anomaly_score: float  # 0-100
    reason: str


class OptionsAnalyzer:
    """Analyzes options flow data for unusual activity patterns."""

    # Thresholds for anomaly detection
    VOLUME_SPIKE_MULTIPLIER = 3.0  # 3x historical average
    IV_PERCENTILE_THRESHOLD = 75  # IV > 75th percentile is unusual
    LARGE_TRADE_VOLUME = 1000  # Contracts in single day
    PUT_CALL_RATIO_EXTREME = 2.0  # Put/call ratio > 2.0 or < 0.5
    OPEN_INTEREST_SPIKE_MULTIPLIER = 2.5

    def __init__(self, provider: OptionsDataProvider):
        """Initialize the analyzer with a data provider.

        Parameters
        ----------
        provider : OptionsDataProvider
            The provider to fetch options data from.
        """
        self.provider = provider

    def analyze_ticker(self, ticker: str) -> List[AnomalyDetectionResult]:
        """Analyze all options activity for a ticker.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.

        Returns
        -------
        List[AnomalyDetectionResult]
            Anomalies detected, sorted by score (highest first).
        """
        contracts = self.provider.get_contracts(ticker)
        if not contracts:
            logger.warning(f"No contracts found for {ticker}")
            return []

        anomalies: List[AnomalyDetectionResult] = []

        # Check each contract for anomalies
        for contract in contracts:
            result = self._analyze_contract(ticker, contract)
            if result:
                anomalies.append(result)

        # Check put/call ratio anomalies (ticker-wide)
        pc_anomalies = self._check_put_call_imbalance(ticker)
        anomalies.extend(pc_anomalies)

        # Sort by anomaly score (highest severity first)
        anomalies.sort(key=lambda x: x.anomaly_score, reverse=True)

        return anomalies

    def _analyze_contract(
        self, ticker: str, contract: OptionContract
    ) -> Optional[AnomalyDetectionResult]:
        """Analyze a single contract for anomalies.

        Parameters
        ----------
        ticker : str
            Stock ticker.
        contract : OptionContract
            Contract to analyze.

        Returns
        -------
        Optional[AnomalyDetectionResult]
            Anomaly result if detected, None otherwise.
        """
        # Check for unusual volume
        historical_avg = self._get_historical_avg_volume(ticker, contract)
        if historical_avg and contract.volume >= self.VOLUME_SPIKE_MULTIPLIER * historical_avg:
            score = min(100.0, (contract.volume / historical_avg) * 20)
            return AnomalyDetectionResult(
                contract=contract,
                flow_type='unusual_volume',
                anomaly_score=score,
                reason=f"Volume spike: {contract.volume} vs historical avg {historical_avg:.0f}",
            )

        # Check for large single trade
        if contract.volume >= self.LARGE_TRADE_VOLUME:
            score = min(100.0, (contract.volume / self.LARGE_TRADE_VOLUME) * 25)
            return AnomalyDetectionResult(
                contract=contract,
                flow_type='large_trade',
                anomaly_score=score,
                reason=f"Large trade detected: {contract.volume} contracts",
            )

        # Check for high IV percentile
        if contract.iv_percentile >= self.IV_PERCENTILE_THRESHOLD:
            score = (contract.iv_percentile - self.IV_PERCENTILE_THRESHOLD) * 2
            return AnomalyDetectionResult(
                contract=contract,
                flow_type='unusual_volume',
                anomaly_score=min(100.0, score),
                reason=f"High IV percentile: {contract.iv_percentile}",
            )

        return None

    def _check_put_call_imbalance(self, ticker: str) -> List[AnomalyDetectionResult]:
        """Check for put/call ratio anomalies.

        Parameters
        ----------
        ticker : str
            Stock ticker.

        Returns
        -------
        List[AnomalyDetectionResult]
            Anomalies found (may be empty).
        """
        anomalies: List[AnomalyDetectionResult] = []

        try:
            pc_ratio = self.provider.get_put_call_ratio(ticker)
            if not pc_ratio:
                return anomalies

            # Extreme put/call ratios indicate unusual sentiment
            if pc_ratio > self.PUT_CALL_RATIO_EXTREME:
                # Unusual put buying (bearish)
                contracts = self.provider.get_contracts(ticker)
                if contracts:
                    put_contracts = [c for c in contracts if c.option_type == 'put']
                    if put_contracts:
                        top_put = max(put_contracts, key=lambda x: x.volume)
                        score = min(100.0, (pc_ratio - 1.0) * 15)
                        anomalies.append(
                            AnomalyDetectionResult(
                                contract=top_put,
                                flow_type='put_call_imbalance',
                                anomaly_score=score,
                                reason=f"Extreme put/call ratio: {pc_ratio:.2f} (bearish)",
                            )
                        )
            elif pc_ratio < (1.0 / self.PUT_CALL_RATIO_EXTREME):
                # Unusual call buying (bullish)
                contracts = self.provider.get_contracts(ticker)
                if contracts:
                    call_contracts = [c for c in contracts if c.option_type == 'call']
                    if call_contracts:
                        top_call = max(call_contracts, key=lambda x: x.volume)
                        score = min(100.0, (1.0 / pc_ratio) * 15)
                        anomalies.append(
                            AnomalyDetectionResult(
                                contract=top_call,
                                flow_type='put_call_imbalance',
                                anomaly_score=score,
                                reason=f"Extreme put/call ratio: {pc_ratio:.2f} (bullish)",
                            )
                        )
        except Exception as exc:
            logger.error(f"Error checking put/call imbalance for {ticker}: {exc}")

        return anomalies

    def _get_historical_avg_volume(
        self, ticker: str, contract: OptionContract
    ) -> Optional[float]:
        """Get historical average volume for a contract.

        Parameters
        ----------
        ticker : str
            Stock ticker.
        contract : OptionContract
            The contract to get history for.

        Returns
        -------
        Optional[float]
            Historical average volume, or None if not enough data.
        """
        try:
            with db_session() as conn:
                # Get average volume from last 10 days for this contract
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(volume) as avg_vol
                    FROM options_flows
                    WHERE ticker = ? AND contract = ?
                    AND created_at >= datetime('now', '-10 days')
                """, (ticker, contract.contract))
                row = cursor.fetchone()
                
                if row and row['avg_vol']:
                    return float(row['avg_vol'])
                
                # Default to 1000 contracts if no history
                return 1000.0
        except Exception as exc:
            logger.error(f"Failed to get historical volume for {contract.contract}: {exc}")
            return 1000.0
```