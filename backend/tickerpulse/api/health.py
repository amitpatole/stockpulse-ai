```python
from flask import Blueprint, jsonify
from tickerpulse.utils.status import get_backend_status, get_latest_backend_status

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    status = get_backend_status()
    return jsonify(status)

@health_bp.route('/health/latest', methods=['GET'])
def latest_health():
    status = get_latest_backend_status()
    return jsonify(status)
```