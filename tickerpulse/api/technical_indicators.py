```python
from typing import List, Dict
import sqlite3
from datetime import datetime
from talib import abstract
from flask import current_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_indicators(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate technical indicators for the given stock data.

    :param data: List of dictionaries with OHLCV data.
    :return: Dictionary containing calculated indicators.
    """
    rsi = abstract.RSI(data, timeperiod=14)
    macd, macd_signal, macd_hist = abstract.MACD(data, fastperiod=12, slowperiod=26, signalperiod=9)
    sma = abstract.SMA(data, timeperiod=50)
    ema = abstract.EMA(data, timeperiod=200)
    bollinger_bands = abstract.BBANDS(data, timeperiod=20)

    return {
        'RSI': rsi,
        'MACD': macd,
        'MACD_Signal': macd_signal,
        'MACD_Hist': macd_hist,
        'SMA': sma,
        'EMA': ema,
        'Bollinger_Bands': bollinger_bands
    }

def get_stock_data(symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Fetch stock data from the database for the given symbol and date range.

    :param symbol: Stock symbol.
    :param start_date: Start date for the data.
    :param end_date: End date for the data.
    :return: List of dictionaries containing OHLCV data.
    """
    conn = sqlite3.connect(current_app.config['DATABASE_PATH'], uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM stock_data WHERE symbol=? AND date BETWEEN ? AND ?", (symbol, start_date, end_date))
        rows = cursor.fetchall()
        if not rows:
            return []
        return [dict(row) for row in rows]
    finally:
        conn.close()

async def async_get_stock_data(symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Asynchronously fetch stock data from the database for the given symbol and date range.

    :param symbol: Stock symbol.
    :param start_date: Start date for the data.
    :param end_date: End date for the data.
    :return: List of dictionaries containing OHLCV data.
    """
    with current_app.app_context():
        return await current_app.asyncio.run_coroutine(async_get_stock_data, symbol, start_date, end_date)

async def async_calculate_indicators(symbol: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Asynchronously calculate technical indicators for the given stock data.

    :param symbol: Stock symbol.
    :param start_date: Start date for the data.
    :param end_date: End date for the data.
    :return: Dictionary containing calculated indicators.
    """
    stock_data = await async_get_stock_data(symbol, start_date, end_date)
    if not stock_data:
        return {}
    return calculate_indicators(stock_data)

```