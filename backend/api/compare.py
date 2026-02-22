"""
TickerPulse AI v3.0 - Performance Comparison API
GET /api/stocks/compare — returns OHLCV normalized to 100 at period start
for up to 5 tickers, with pre-computed performance deltas.
"""

import math
import re
import logging
import concurrent.futures

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

compare_bp = Blueprint('compare', __name__, url_prefix='/api/stocks')

_TIMEFRAME_MAP = {
    '1D': ('1d', '5m'),
    '1W': ('5d', '15m'),
    '1M': ('1mo', '1d'),
    '3M': ('3mo', '1d'),
    '6M': ('6mo', '1d'),
    '1Y': ('1y', '1d'),
    'All': ('max', '1d'),
}

_TICKER_RE = re.compile(r'^[A-Z0-9.\-^]{1,12}$')

_MAX_TICKERS = 5


def _fetch_series(ticker: str, period: str, interval: str) -> dict:
    """Fetch OHLCV for one ticker and return raw candles (not yet normalized).

    Returns a dict with keys: ticker, name, raw_closes (list of (time, close)),
    error (str or None).
    """
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        hist = tk.history(period=period, interval=interval)

        if hist.empty:
            return {'ticker': ticker, 'name': ticker, 'raw_closes': [], 'error': 'No data found'}

        raw_closes = []
        for ts, row in hist.iterrows():
            try:
                close = float(row['Close'])
                if math.isnan(close):
                    continue
            except (TypeError, ValueError):
                continue
            raw_closes.append((int(ts.timestamp()), close))

        if not raw_closes:
            return {'ticker': ticker, 'name': ticker, 'raw_closes': [], 'error': 'No data found'}

        return {'ticker': ticker, 'name': ticker, 'raw_closes': raw_closes, 'error': None}

    except ImportError:
        logger.error("yfinance is not installed")
        return {'ticker': ticker, 'name': ticker, 'raw_closes': [], 'error': 'Data provider unavailable'}
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", ticker, exc)
        return {'ticker': ticker, 'name': ticker, 'raw_closes': [], 'error': 'No data found'}


@compare_bp.route('/compare', methods=['GET'])
def compare_stocks():
    """Return normalized performance series for up to 5 tickers.

    Query Parameters:
        tickers (str): Required. Comma-separated ticker symbols, max 5. Primary ticker first.
        timeframe (str): Optional. One of 1D, 1W, 1M, 3M, 6M, 1Y. Default 1M.

    Returns:
        JSON with timeframe and series array. Each series has:
            ticker, name, candles ([{time, value}]), delta_pct, error.
        candles[].value = (close / first_close) * 100.
        delta_pct = series final value minus primary series final value.
        Returns 400 for missing/invalid parameters.
    """
    tickers_param = request.args.get('tickers', '').strip()
    if not tickers_param:
        return jsonify({'error': 'tickers parameter is required'}), 400

    tickers = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    if not tickers:
        return jsonify({'error': 'tickers parameter is required'}), 400

    if len(tickers) > _MAX_TICKERS:
        return jsonify({'error': f'Maximum {_MAX_TICKERS} tickers allowed'}), 400

    invalid = [t for t in tickers if not _TICKER_RE.match(t)]
    if invalid:
        return jsonify({'error': f'Invalid ticker symbol(s): {", ".join(invalid)}'}), 400

    timeframe = request.args.get('timeframe', '1M').strip()
    if timeframe not in _TIMEFRAME_MAP:
        return jsonify({
            'error': f'Invalid timeframe. Must be one of: {", ".join(_TIMEFRAME_MAP)}'
        }), 400

    period, interval = _TIMEFRAME_MAP[timeframe]

    # Fetch all tickers in parallel
    results_by_ticker: dict[str, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_TICKERS) as executor:
        future_map = {
            executor.submit(_fetch_series, ticker, period, interval): ticker
            for ticker in tickers
        }
        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
            results_by_ticker[result['ticker']] = result

    # Normalize each series to 100 at its own first data point
    normalized: dict[str, list[dict]] = {}
    final_values: dict[str, float] = {}

    for ticker in tickers:
        result = results_by_ticker.get(ticker)
        if not result or result['error'] or not result['raw_closes']:
            normalized[ticker] = []
            final_values[ticker] = 100.0
            continue

        raw = result['raw_closes']
        first_close = raw[0][1]
        if first_close == 0:
            normalized[ticker] = []
            final_values[ticker] = 100.0
            continue

        candles = [
            {'time': ts, 'value': round((close / first_close) * 100.0, 4)}
            for ts, close in raw
        ]
        normalized[ticker] = candles
        final_values[ticker] = candles[-1]['value'] if candles else 100.0

    primary_ticker = tickers[0]
    primary_final = final_values.get(primary_ticker, 100.0)

    series = []
    for ticker in tickers:
        result = results_by_ticker.get(ticker, {})
        candles = normalized.get(ticker, [])
        error = result.get('error') if not candles else None
        final_val = final_values.get(ticker, 100.0)
        delta_pct = round(final_val - primary_final, 2) if ticker != primary_ticker else 0.0

        series.append({
            'ticker': ticker,
            'name': result.get('name', ticker),
            'candles': candles,
            'delta_pct': delta_pct,
            'error': error,
        })

    return jsonify({'timeframe': timeframe, 'series': series})
