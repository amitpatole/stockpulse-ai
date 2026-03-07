```python
from flask import Blueprint, jsonify
from ticker_pulse.models.crypto import CryptoCurrency

cryptocurrencies_api = Blueprint('cryptocurrencies_api', __name__)

@cryptocurrencies_api.route('/v1/cryptocurrencies', methods=['GET'])
def get_cryptocurrencies():
    cryptocurrencies = CryptoCurrency.query.all()
    return jsonify([crypto.to_dict() for crypto in cryptocurrencies])

@cryptocurrencies_api.route('/v1/cryptocurrencies/<int:id>', methods=['GET'])
def get_crypto_by_id(id):
    crypto = CryptoCurrency.query.get(id)
    if not crypto:
        return jsonify({'error': 'Crypto not found'}), 404
    return jsonify(crypto.to_dict())
```