```python
from flask import Blueprint, jsonify
from tickerpulse.api.technical_indicators import async_calculate_indicators

technical_indicators_bp = Blueprint('technical_indicators', __name__)

@technical_indicators_bp.route('/api/v1/indicators/<symbol>', methods=['GET'])
async def get_indicators(symbol: str) -> Any:
    """
    Get technical indicators for the given stock symbol.

    :param symbol: Stock symbol.
    :return: JSON response with calculated indicators.
    """
    try:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
        end_date = datetime.utcnow()
        indicators = await async_calculate_indicators(symbol, start_date, end_date)
        return jsonify(indicators)
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return jsonify({"error": str(e)}), 500

```