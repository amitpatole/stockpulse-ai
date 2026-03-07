```python
from flask import Blueprint, jsonify
from app.models import Cryptocurrency
from app.services import get_cryptocurrency_data

cryptocurrencies_bp = Blueprint('cryptocurrencies', __name__)

@cryptocurrencies_bp.route('/api/v1/cryptocurrencies', methods=['GET'])
def get_cryptocurrencies():
    cryptocurrencies = Cryptocurrency.query.all()
    return jsonify([cryptocurrency.to_dict() for cryptocurrency in cryptocurrencies])

@cryptocurrencies_bp.route('/api/v1/cryptocurrency/<string:symbol>', methods=['GET'])
def get_cryptocurrency(symbol):
    cryptocurrency = Cryptocurrency.query.filter_by(symbol=symbol).first_or_404()
    return jsonify(cryptocurrency.to_dict())
```