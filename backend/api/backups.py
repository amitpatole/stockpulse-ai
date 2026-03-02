```python
"""
TickerPulse AI v3.0 - Backup & Restore API Routes
Admin endpoints for backup management and scheduling.
"""

from flask import Blueprint, request, jsonify, session
import logging

from backend.core.backup_manager import (
    create_backup,
    list_backups,
    delete_backup,
    start_restore,
    get_restore_status,
    get_backup_schedule,
    set_backup_schedule,
)

logger = logging.getLogger(__name__)

backups_bp = Blueprint('backups', __name__, url_prefix='/api/admin')


def _require_admin():
    """Require admin authentication."""
    # In production, check user role from session
    # For now, allow if user is authenticated
    if 'user_id' not in session:
        return False
    return True


# ---------------------------------------------------------------------------
# Manual Backup Endpoints
# ---------------------------------------------------------------------------

@backups_bp.route('/backups', methods=['POST'])
def create_backup_endpoint():
    """Create a manual backup of the database.
    
    Request JSON:
        {
            "notes": "optional notes"
        }
    """
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        backup = create_backup(notes)
        return jsonify({'data': backup, 'meta': {}}), 201
    
    except RuntimeError as e:
        # Rate limit or insufficient space
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error('Backup failed: %s', str(e))
        return jsonify({'error': 'Backup failed'}), 500


@backups_bp.route('/backups', methods=['GET'])
def list_backups_endpoint():
    """List all backups with pagination (newest first).
    
    Query parameters:
        limit: Maximum items (1-100, default 50)
        offset: Number to skip (default 0)
    """
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        result = list_backups(limit, offset)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error('List backups failed: %s', str(e))
        return jsonify({'error': 'Failed to list backups'}), 500


@backups_bp.route('/backups/<int:backup_id>', methods=['DELETE'])
def delete_backup_endpoint(backup_id: int):
    """Delete a backup file and metadata.
    
    Path parameters:
        backup_id: ID of backup to delete
    """
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        success = delete_backup(backup_id)
        if not success:
            return jsonify({'error': 'Backup not found'}), 404
        
        return '', 204
    
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error('Delete backup failed: %s', str(e))
        return jsonify({'error': 'Delete failed'}), 500


# ---------------------------------------------------------------------------
# Restore Endpoints
# ---------------------------------------------------------------------------

@backups_bp.route('/backups/<int:backup_id>/restore', methods=['POST'])
def restore_backup_endpoint(backup_id: int):
    """Start a restore operation from a backup.
    
    Request JSON:
        {
            "verify_checksum": true
        }
    """
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        verify_checksum = data.get('verify_checksum', True)
        
        result = start_restore(backup_id, verify_checksum)
        return jsonify({'data': result, 'meta': {}}), 202
    
    except RuntimeError as e:
        status_code = 422 if 'checksum' in str(e).lower() else 400
        return jsonify({'error': str(e)}), status_code
    except Exception as e:
        logger.error('Restore failed: %s', str(e))
        return jsonify({'error': 'Restore failed'}), 500


@backups_bp.route('/restores/<restore_id>', methods=['GET'])
def get_restore_status_endpoint(restore_id: str):
    """Get status of a restore operation.
    
    Path parameters:
        restore_id: ID of restore operation
    """
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        status = get_restore_status(restore_id)
        if not status:
            return jsonify({'error': 'Restore not found'}), 404
        
        return jsonify({'data': status, 'meta': {}}), 200
    
    except Exception as e:
        logger.error('Get restore status failed: %s', str(e))
        return jsonify({'error': 'Failed to get status'}), 500


# ---------------------------------------------------------------------------
# Schedule Configuration Endpoints
# ---------------------------------------------------------------------------

@backups_bp.route('/backup-schedule', methods=['GET'])
def get_schedule_endpoint():
    """Get current backup schedule configuration."""
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        config = get_backup_schedule()
        return jsonify({'data': config, 'meta': {}}), 200
    
    except Exception as e:
        logger.error('Get backup schedule failed: %s', str(e))
        return jsonify({'error': 'Failed to get schedule'}), 500


@backups_bp.route('/backup-schedule', methods=['POST'])
def set_schedule_endpoint():
    """Update backup schedule configuration.
    
    Request JSON:
        {
            "enabled": true,
            "schedule_time": "02:00",
            "retention_days": 30,
            "max_backups": 10
        }
    """
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        
        enabled = data.get('enabled', False)
        schedule_time = data.get('schedule_time', '02:00')
        retention_days = int(data.get('retention_days', 30))
        max_backups = int(data.get('max_backups', 10))
        
        config = set_backup_schedule(
            enabled, schedule_time, retention_days, max_backups
        )
        return jsonify({'data': config, 'meta': {}}), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error('Set backup schedule failed: %s', str(e))
        return jsonify({'error': 'Failed to set schedule'}), 500
```