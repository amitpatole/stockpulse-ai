"""
Scheduler REST API routes.

Provides endpoints for listing, inspecting, pausing, resuming, triggering,
and rescheduling jobs, as well as viewing job execution history.

Blueprint prefix: /api/scheduler
"""
import logging
from flask import Blueprint, jsonify, request

from backend.jobs._helpers import get_job_history

logger = logging.getLogger(__name__)

scheduler_bp = Blueprint('scheduler_routes', __name__, url_prefix='/api/scheduler')


def _get_scheduler_manager():
    """Lazily import the module-level SchedulerManager singleton."""
    from backend.scheduler import scheduler_manager
    return scheduler_manager


# -----------------------------------------------------------------------
# Jobs listing
# -----------------------------------------------------------------------

@scheduler_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all registered jobs with their current status.

    Returns:
        JSON object with ``jobs`` array and ``total`` count.
    """
    sm = _get_scheduler_manager()
    jobs = sm.get_all_jobs()
    return jsonify({'jobs': jobs, 'total': len(jobs)})


@scheduler_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get detailed information about a specific job.

    Path Parameters:
        job_id (str): The unique job identifier.

    Returns:
        JSON object with job details.

    Errors:
        404: Job not found.
    """
    sm = _get_scheduler_manager()
    job = sm.get_job(job_id)
    if not job:
        return jsonify({'error': f'Job not found: {job_id}'}), 404

    # Attach recent execution history
    job['recent_history'] = get_job_history(job_id=job_id, limit=10)
    return jsonify(job)


# -----------------------------------------------------------------------
# Job control
# -----------------------------------------------------------------------

@scheduler_bp.route('/jobs/<job_id>/pause', methods=['POST'])
def pause_job(job_id):
    """Pause a scheduled job.

    Path Parameters:
        job_id (str): The job to pause.

    Returns:
        JSON object with ``success`` boolean and optional ``error``.
    """
    sm = _get_scheduler_manager()
    success = sm.pause_job(job_id)
    if success:
        return jsonify({'success': True, 'job_id': job_id, 'status': 'paused'})
    return jsonify({'success': False, 'error': f'Failed to pause job: {job_id}'}), 400


@scheduler_bp.route('/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """Resume a paused job.

    Path Parameters:
        job_id (str): The job to resume.

    Returns:
        JSON object with ``success`` boolean and optional ``error``.
    """
    sm = _get_scheduler_manager()
    success = sm.resume_job(job_id)
    if success:
        return jsonify({'success': True, 'job_id': job_id, 'status': 'resumed'})
    return jsonify({'success': False, 'error': f'Failed to resume job: {job_id}'}), 400


@scheduler_bp.route('/jobs/<job_id>/trigger', methods=['POST'])
def trigger_job(job_id):
    """Trigger immediate execution of a job.

    Path Parameters:
        job_id (str): The job to trigger.

    Returns:
        JSON object with ``success`` boolean.
    """
    sm = _get_scheduler_manager()
    success = sm.trigger_job(job_id)
    if success:
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Job {job_id} triggered for immediate execution.',
        })
    return jsonify({'success': False, 'error': f'Failed to trigger job: {job_id}'}), 400


@scheduler_bp.route('/jobs/<job_id>/schedule', methods=['PUT'])
def update_schedule(job_id):
    """Update a job's schedule.

    Path Parameters:
        job_id (str): The job to reschedule.

    Request Body (JSON):
        trigger (str): Trigger type (``'cron'`` or ``'interval'``).
        Additional keys are forwarded as trigger arguments.
        For cron: hour, minute, day_of_week, etc.
        For interval: minutes, hours, seconds, etc.

    Example bodies::

        {"trigger": "cron", "hour": 9, "minute": 0, "day_of_week": "mon-fri"}
        {"trigger": "interval", "minutes": 30}

    Returns:
        JSON object with ``success`` boolean.
    """
    data = request.get_json(silent=True)
    if not data or 'trigger' not in data:
        return jsonify({
            'success': False,
            'error': 'Request body must include "trigger" (cron or interval).',
        }), 400

    trigger = data.pop('trigger')
    valid_triggers = ('cron', 'interval', 'date')
    if trigger not in valid_triggers:
        return jsonify({
            'success': False,
            'error': f'Invalid trigger type: {trigger}. Must be one of: {", ".join(valid_triggers)}',
        }), 400

    sm = _get_scheduler_manager()
    success = sm.update_job_schedule(job_id, trigger, **data)
    if success:
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Schedule updated to trigger={trigger} with args={data}.',
        })
    return jsonify({'success': False, 'error': f'Failed to update schedule for: {job_id}'}), 400


# -----------------------------------------------------------------------
# Job history
# -----------------------------------------------------------------------

@scheduler_bp.route('/history', methods=['GET'])
def job_execution_history():
    """Get job execution history.

    Query Parameters:
        job_id (str, optional): Filter by job ID.
        limit (int, optional): Max records to return (default 50, max 200).

    Returns:
        JSON object with ``history`` array and ``total`` count.
    """
    job_id = request.args.get('job_id', None)
    limit = min(int(request.args.get('limit', 50)), 200)

    history = get_job_history(job_id=job_id, limit=limit)
    return jsonify({
        'history': history,
        'total': len(history),
        'filters': {
            'job_id': job_id,
            'limit': limit,
        },
    })
