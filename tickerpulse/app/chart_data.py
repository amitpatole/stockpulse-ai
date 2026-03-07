```python
from typing import List, Dict
import datetime
from tickerpulse.api.technical_indicators import async_calculate_indicators

def get_chart_data(symbol: str, start_date: datetime.datetime, end_date: datetime.datetime) -> Dict[str, Any]:
    """
    Get chart data for the given stock symbol and date range, including technical indicators.

    :param symbol: Stock symbol.
    :param start_date: Start date for the data.
    :param end_date: End date for the data.
    :return: Dictionary containing chart data with technical indicators.
    """
    try:
        indicators = async_calculate_indicators(symbol, start_date, end_date)
        return {
            'symbol': symbol,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'chart_data': get_stock_data(symbol, start_date, end_date),
            'indicators': indicators
        }
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        return {}

```