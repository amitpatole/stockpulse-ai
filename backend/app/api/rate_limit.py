```python
from flask import Blueprint, jsonify
from app.models import RateLimit, Provider

rate_limit_blueprint = Blueprint('rate_limit', __name__)

@rate_limit_blueprint.route('/rate_limit', methods=['GET'])
def get_rate_limit():
    rate_limits = RateLimit.query.all()
    return jsonify([rl.to_dict() for rl in rate_limits])

@rate_limit_blueprint.route('/rate_limit/<int:provider_id>', methods=['GET'])
def get_rate_limit_by_provider(provider_id):
    rate_limit = RateLimit.query.filter_by(provider_id=provider_id).first_or_404()
    return jsonify(rate_limit.to_dict())
```