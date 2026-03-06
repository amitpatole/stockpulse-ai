```python
from flask import Blueprint, jsonify
from flask import current_app as app
from .models import HealthStatus
from datetime import datetime

health_blueprint = Blueprint('health', __name__)

@health_blueprint.route('/health', methods=['GET'])
def get_health_status():
    health_data = HealthStatus.query.order_by(HealthStatus.timestamp.desc()).first()
    if health_data:
        return jsonify({
            'status': health_data.status,
            'latency_ms': health_data.latency_ms,
            'error_rate': health_data.error_rate,
            'timestamp': health_data.timestamp.isoformat()
        })
    return jsonify({'status': 'unknown'}), 404
```