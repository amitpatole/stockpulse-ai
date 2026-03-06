```python
from flask import Blueprint, request, jsonify
from backend.models import Dashboard, db
from backend.schemas import DashboardSchema

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/config', methods=['GET'])
def get_dashboard_config():
    user_id = request.args.get('user_id')
    dashboard = Dashboard.query.filter_by(user_id=user_id).first()
    if dashboard:
        return DashboardSchema().dump(dashboard)
    return jsonify({'error': 'Dashboard not found'}), 404

@dashboard_bp.route('/dashboard/config', methods=['POST'])
def update_dashboard_config():
    data = request.json
    user_id = data.get('user_id')
    widgets = data.get('widgets')
    dashboard = Dashboard.query.filter_by(user_id=user_id).first()
    if dashboard:
        dashboard.widgets = widgets
        db.session.commit()
        return DashboardSchema().dump(dashboard)
    new_dashboard = Dashboard(user_id=user_id, widgets=widgets)
    db.session.add(new_dashboard)
    db.session.commit()
    return DashboardSchema().dump(new_dashboard), 201
```