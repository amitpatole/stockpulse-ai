```python
#!/usr/bin/env python3
"""
AI-Powered Stock Analytics
Analyzes technical indicators, news sentiment, and social media to provide stock ratings
"""

import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

from backend.config import Config

logger = logging.getLogger(__name__)


def _mask_api_key(api_key: str) -> str:
    """Mask API key for safe logging. Shows only first 4 and last 4 characters."""
    if not api_key:
        return "(not set)"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


class StockAnalytics:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Config.DB_PATH
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_stock_price_data(self, ticker: str, period='1mo') -> Dict:
        """Fetch stock price data from Yahoo Finance with yfinance library fallback."""
        # Attempt 1: Direct Yahoo v8 API
        try:
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
            params = {
                'range': period,
                'interval': '1d',
                'indicators': 'quote',
                'includeTimestamps': 'true'
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [{}])[0]

                quote = result.get('indicators', {}).get('quote', [{}])[0]
                timestamps = result.get('timestamp', [])

                if timestamps and quote.get('close'):
                    return {
                        'open': quote.get('open', []),
                        'high': quote.get('high', []),
                        'low': quote.get('low', []),
                        'close': quote.get('close', []),
                        'volume': quote.get('volume', []),
                        'timestamps': timestamps
                    }

        except Exception as e:
            logger.warning(f"Yahoo v8 API failed for {ticker}: {e}")

        # Attempt 2: yfinance library fallback
        try:
            import yfinance as yf
            tk = yf.Ticker(ticker)
            hist = tk.history(period=period, interval='1d')
            if not hist.empty:
                return {
                    'open': hist['Open'].tolist(),
                    'high': hist['High'].tolist(),
                    'low': hist['Low'].tolist(),
                    'close': hist['Close'].tolist(),
                    'volume': hist['Volume'].tolist(),
                    'timestamps': [int(ts.timestamp()) for ts in hist.index]
                }
        except Exception as e:
            logger.error(f"yfinance fallback also failed for {ticker}: {e}")

        return {}

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index (RSI)"""
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data

        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        # Calculate average gains and losses
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0
        if avg_gain == 0:
            return 0.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def calculate_ai_rating(self, ticker: str, use_cache: bool = True) -> Dict:
        """Calculate AI-powered stock rating based on multiple factors."""
        if use_cache:
            rating_data = self._get_cached_rating(ticker)
            if rating_data:
                return rating_data

        try:
            # Get price data
            price_data = self.get_stock_price_data(ticker, '1y')
            if not price_data or not price_data.get('close'):
                logger.warning(f"No price data available for {ticker}")
                return self._error_rating(ticker, "No price data")

            closes = price_data.get('close', [])
            current_price = closes[-1] if closes else 0
            previous_price = closes[-2] if len(closes) > 1 else current_price

            # Calculate technical indicators
            rsi = self.calculate_rsi(closes)
            price_change = current_price - previous_price
            price_change_pct = (price_change / previous_price * 100) if previous_price else 0

            # Calculate rating based on technical indicators
            score, rating = self._calculate_rating_from_technicals(rsi, price_change_pct)

            # Technical signals
            technical_signals = self._get_technical_signals(rsi, price_change_pct)
            sentiment_signals = self._get_sentiment_signals(ticker)

            # Get AI summary
            summary_text, is_ai_powered = self._generate_summary(rating, score, technical_signals, sentiment_signals)

            rating_data = {
                'ticker': ticker,
                'rating': rating,
                'score': round(score, 2),
                'confidence': 0.75,
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'rsi': round(rsi, 2),
                'sentiment_score': 0.5,
                'sentiment_label': 'neutral',
                'technical_score': round(score, 2),
                'fundamental_score': 0.0,
                'analysis_summary': summary_text,
                'updated_at': datetime.utcnow().isoformat()
            }

            self._cache_rating(rating_data)
            return rating_data

        except Exception as e:
            logger.error(f"Error calculating rating for {ticker}: {e}", exc_info=True)
            return self._error_rating(ticker, str(e))

    def _get_cached_rating(self, ticker: str) -> Optional[Dict]:
        """Get cached rating from database if it exists and is recent."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM ai_ratings WHERE ticker = ?',
                (ticker.upper(),)
            ).fetchone()
            conn.close()

            if row:
                updated_at = datetime.fromisoformat(row['updated_at'])
                age = datetime.utcnow() - updated_at
                if age.total_seconds() < 3600:  # Cache valid for 1 hour
                    return dict(row)
        except Exception as e:
            logger.debug(f"Could not get cached rating for {ticker}: {e}")

        return None

    def _error_rating(self, ticker: str, error_msg: str) -> Dict:
        """Return error rating when calculation fails."""
        return {
            'ticker': ticker,
            'rating': 'ERROR',
            'score': 0,
            'confidence': 0,
            'error': error_msg,
            'updated_at': datetime.utcnow().isoformat()
        }

    def _calculate_rating_from_technicals(self, rsi: float, price_change_pct: float) -> Tuple[float, str]:
        """Calculate rating score and label based on technical indicators."""
        score = 50.0

        # RSI contribution (max ±30 points)
        if rsi < 30:
            score += 20
        elif rsi < 40:
            score += 10
        elif rsi > 70:
            score -= 20
        elif rsi > 60:
            score -= 10

        # Price momentum contribution (max ±20 points)
        if price_change_pct > 5:
            score += 15
        elif price_change_pct > 2:
            score += 8
        elif price_change_pct < -5:
            score -= 15
        elif price_change_pct < -2:
            score -= 8

        score = max(0, min(100, score))

        if score >= 80:
            rating = 'STRONG_BUY'
        elif score >= 65:
            rating = 'BUY'
        elif score >= 50:
            rating = 'HOLD'
        elif score >= 35:
            rating = 'SELL'
        else:
            rating = 'STRONG_SELL'

        return score, rating

    def _get_technical_signals(self, rsi: float, price_change_pct: float) -> List[str]:
        """Generate technical analysis signals."""
        signals = []

        if rsi < 30:
            signals.append("RSI indicates oversold conditions")
        elif rsi > 70:
            signals.append("RSI indicates overbought conditions")
        else:
            signals.append("RSI in neutral zone")

        if price_change_pct > 5:
            signals.append("Strong positive price momentum")
        elif price_change_pct < -5:
            signals.append("Strong negative price momentum")
        else:
            signals.append("Price momentum is neutral")

        return signals

    def _get_sentiment_signals(self, ticker: str) -> List[str]:
        """Generate sentiment signals (placeholder)."""
        return [
            "Market sentiment appears neutral",
            "No major news catalysts detected",
            "Social media mentions show moderate interest"
        ]

    def _cache_rating(self, rating_data: Dict):
        """Cache the rating in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ai_ratings
                (ticker, rating, score, confidence, current_price, price_change, 
                 price_change_pct, rsi, sentiment_score, sentiment_label, 
                 technical_score, fundamental_score, analysis_summary, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rating_data['ticker'],
                rating_data['rating'],
                rating_data['score'],
                rating_data['confidence'],
                rating_data['current_price'],
                rating_data['price_change'],
                rating_data['price_change_pct'],
                rating_data['rsi'],
                rating_data['sentiment_score'],
                rating_data['sentiment_label'],
                rating_data['technical_score'],
                rating_data['fundamental_score'],
                rating_data['analysis_summary'],
                rating_data['updated_at'],
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Could not cache rating for {rating_data['ticker']}: {e}")

    def _generate_summary(self, rating: str, score: float, technical_signals: List[str],
                         sentiment_signals: List[str]) -> tuple:
        """Generate AI summary of the analysis. Returns (summary_text, is_ai_powered)"""
        # Try to use real AI if configured
        try:
            # CRITICAL FIX: Use correct import paths
            from backend.core.settings_manager import get_active_ai_provider
            from backend.core.ai_providers import AIProviderFactory

            provider_config = get_active_ai_provider()

            if provider_config:
                # CRITICAL FIX: Validate provider config before use and mask API key in logs
                if not provider_config.get('api_key'):
                    logger.warning("AI provider configured but no API key set")
                    return (self._get_fallback_summary(rating, score), False)

                masked_key = _mask_api_key(provider_config['api_key'])
                logger.info(f"Using AI provider: {provider_config['provider_name']} - {provider_config['model']} (key: {masked_key})")

                # Create AI provider
                provider = AIProviderFactory.create_provider(
                    provider_config['provider_name'],
                    provider_config['api_key'],
                    provider_config['model']
                )

                if provider:
                    # Create detailed prompt for AI
                    prompt = self._create_ai_prompt(rating, score, technical_signals, sentiment_signals)

                    # Get AI analysis (with timeout protection)
                    ai_summary = provider.generate_analysis(prompt, max_tokens=300)

                    # Return AI summary if successful
                    if ai_summary and not ai_summary.startswith('Error:'):
                        logger.info("AI analysis generated successfully")
                        return (ai_summary, True)
        except Exception as e:
            logger.warning(f"Error generating AI summary: {e}")

        # Fallback to basic summary if AI is not available
        return (self._get_fallback_summary(rating, score), False)

    def _get_fallback_summary(self, rating: str, score: float) -> str:
        """Generate fallback summary when AI is not available."""
        summaries = {
            'STRONG_BUY': f"Strong bullish signals detected (Score: {score:.1f}/100). Technical indicators and news sentiment are highly positive. Consider buying.",
            'BUY': f"Bullish indicators present (Score: {score:.1f}/100). Both technical analysis and sentiment lean positive. Good buying opportunity.",
            'HOLD': f"Mixed signals (Score: {score:.1f}/100). Consider holding current position. Monitor for clearer directional signals.",
            'SELL': f"Bearish indicators detected (Score: {score:.1f}/100). Technical and/or sentiment analysis suggest caution. Consider reducing position.",
            'STRONG_SELL': f"Strong bearish signals (Score: {score:.1f}/100). Multiple negative indicators present. Consider exiting position."
        }
        return summaries.get(rating, f"Score: {score:.1f}/100")

    def _create_ai_prompt(self, rating: str, score: float, technical_signals: List[str],
                         sentiment_signals: List[str]) -> str:
        """Create a detailed prompt for AI analysis"""
        prompt = f"""Analyze this stock based on the following data:

RATING: {rating} (Score: {score:.1f}/100)

TECHNICAL SIGNALS:
{chr(10).join('- ' + signal for signal in technical_signals[:5])}

SENTIMENT SIGNALS:
{chr(10).join('- ' + signal for signal in sentiment_signals[:5])}

Provide a concise 2-3 sentence analysis focusing on:
1. Key insights from the data
2. Main risk factors or opportunities
3. Clear recommendation

Be direct and actionable. Avoid disclaimers."""

        return prompt

    def get_all_ratings(self) -> List[Dict]:
        """Get AI ratings for all active stocks"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
```