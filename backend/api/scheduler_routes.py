```python
"""
Scheduler REST API routes.

Provides endpoints for listing, inspecting, pausing, resuming, triggering,
and rescheduling jobs, as well as viewing job execution history.

Blueprint prefix: /api/scheduler
"""
import logging
from flask import Blueprint, jsonify, request

from backend.jobs._helpers import get_job_history
from backend.api.validators.scheduler_validators import validate_job_id, validate_trigger_args
from backend.core.error_handlers import handle_api_errors, ValidationError, NotFoundError

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
@handle_api_errors
def list_jobs():
    """List all registered jobs with their current status.
    ---
    tags:
      - Scheduler
    summary: List all scheduled jobs
    responses:
      200:
        description: All registered jobs with status and schedule metadata.
        schema:
          type: object
          properties:
            jobs:
              type: array
              items:
                $ref: '#/definitions/SchedulerJob'
            total:
              type: integer
              example: 6
    """
    sm = _get_scheduler_manager()
    jobs = sm.get_all_jobs()
    tz = sm.get_scheduler_timezone()
    for job in jobs:
        job['timezone'] = tz
    return jsonify({'jobs': jobs, 'total': len(jobs)})


@scheduler_bp.route('/jobs/<job_id>', methods=['GET'])
@handle_api_errors
def get_job(job_id):
    """Get detailed information about a specific scheduled job.
    ---
    tags:
      - Scheduler
    summary: Get job details
    parameters:
      - name: job_id
        in: path
        type: string
        required: true
        description: Unique job identifier.
        example: news_monitor
    responses:
      200:
        description: Job details including recent execution history.
        schema:
          $ref: '#/definitions/SchedulerJob'
      400:
        description: Invalid job_id format.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Job not found.
        schema:
          $ref: '#/definitions/Error'
    """
    ok, err = validate_job_id(job_id)
    if not ok:
        raise ValidationError(err)

    sm = _get_scheduler_manager()
    job = sm.get_job(job_id)
    if not job:
        raise NotFoundError(f'Job not found: {job_id}')

    # Attach recent execution history and scheduler timezone
    job['recent_history'] = get_job_history(job_id=job_id, limit=10)
    job['timezone'] = sm.get_scheduler_timezone()
    return jsonify(job)


# -----------------------------------------------------------------------
# Job control
# -----------------------------------------------------------------------

@scheduler_bp.route('/jobs/<job_id>/pause', methods=['POST'])
@handle_api_errors
def pause_job(job_id):
    """Pause a scheduled job.
    ---
    tags:
      - Scheduler
    summary: Pause a scheduled job
    parameters:
      - name: job_id
        in: path
        type: string
        required: true
        description: Job identifier to pause.
        example: news_monitor
    responses:
      200:
        description: Job paused successfully.
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: Invalid job_id or pause failed.
        schema:
          $ref: '#/definitions/Error'
    """
    ok, err = validate_job_id(job_id)
    if not ok:
        raise ValidationError(err)

    sm = _get_scheduler_manager()
    success = sm.pause_job(job_id)
    if success:
        return jsonify({'success': True, 'job_id': job_id, 'status': 'paused'})
    raise ValidationError(f'Failed to pause job: {job_id}')


@scheduler_bp.route('/jobs/<job_id>/resume', methods=['POST'])
@handle_api_errors
def resume_job(job_id):
    """Resume a paused scheduled job.
    ---
    tags:
      - Scheduler
    summary: Resume a paused job
    parameters:
      - name: job_id
        in: path
        type: string
        required: true
        description: Job identifier to resume.
        example: news_monitor
    responses:
      200:
        description: Job resumed successfully.
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: Invalid job_id or resume failed.
        schema:
          $ref: '#/definitions/Error'
    """
    ok, err = validate_job_id(job_id)
    if not ok:
        raise ValidationError(err)

    sm = _get_scheduler_manager()
    success = sm.resume_job(job_id)
    if success:
        return jsonify({'success': True, 'job_id': job_id, 'status': 'resumed'})
    raise ValidationError(f'Failed to resume job: {job_id}')


@scheduler_bp.route('/jobs/<job_id>/trigger', methods=['POST'])
@handle_api_errors
def trigger_job(job_id):
    """Trigger immediate execution of a scheduled job.
    ---
    tags:
      - Scheduler
    summary: Trigger a job immediately
    parameters:
      - name: job_id
        in: path
        type: string
        required: true
        description: Job identifier to trigger.
        example: news_monitor
    responses:
      200:
        description: Job triggered for immediate execution.
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: Invalid job_id or trigger failed.
        schema:
          $ref: '#/definitions/Error'
    """
    ok, err = validate_job_id(job_id)
    if not ok:
        raise ValidationError(err)

    sm = _get_scheduler_manager()
    success = sm.trigger_job(job_id)
    if success:
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Job {job_id} triggered for immediate execution.',
        })
    raise ValidationError(f'Failed to trigger job: {job_id}')


@scheduler_bp.route('/jobs/<job_id>/schedule', methods=['PUT'])
@handle_api_errors
def update_schedule(job_id):
    """Update a job's schedule trigger.
    ---
    tags:
      - Scheduler
    summary: Reschedule a job
    consumes:
      - application/json
    parameters:
      - name: job_id
        in: path
        type: string
        required: true
        description: Job identifier to reschedule.
        example: news_monitor
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - trigger
          properties:
            trigger:
              type: string
              enum: [cron, interval, date]
            hour:
              type: integer
            minute:
              type: integer
            day_of_week:
              type: string
            minutes:
              type: integer
    responses:
      200:
        description: Schedule updated successfully.
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: Invalid job_id, missing trigger, or invalid trigger arguments.
        schema:
          $ref: '#/definitions/Error'
    """
    ok, err = validate_job_id(job_id)
    if not ok:
        raise ValidationError(err)

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict) or 'trigger' not in data:
        raise ValidationError('Request body must include "trigger" (cron or interval).')

    trigger = data.pop('trigger')
    valid_triggers = ('cron', 'interval', 'date')
    if trigger not in valid_triggers:
        raise ValidationError(
            f'Invalid trigger type: {trigger}. Must be one of: {", ".join(valid_triggers)}'
        )

    ok, err = validate_trigger_args(trigger, data)
    if not ok:
        raise ValidationError(err)

    sm = _get_scheduler_manager()
    success = sm.update_job_schedule(job_id, trigger, **data)
    if success:
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Schedule updated to trigger={trigger} with args={data}.',
        })
    raise ValidationError(f'Failed to update schedule for: {job_id}')


# -----------------------------------------------------------------------
# Job history
# -----------------------------------------------------------------------

@scheduler_bp.route('/history', methods=['GET'])
@handle_api_errors
def job_execution_history():
    """Get job execution history.
    ---
    tags:
      - Scheduler
    summary: Get job execution history
    description: >
      Returns past job execution records, optionally filtered by job ID.
      Results are ordered by most recent execution first.
    parameters:
      - in: query
        name: job_id
        type: string
        required: false
      - in: query
        name: limit
        type: integer
        required: false
        default: 50
    responses:
      200:
        description: Execution history with applied filter metadata.
      400:
        description: Invalid limit parameter.
        schema:
          $ref: '#/definitions/Error'
    """
    job_id = request.args.get('job_id', None)
    raw_limit = request.args.get('limit', 50)
    try:
        limit = min(int(raw_limit), 200)
    except (ValueError, TypeError):
        raise ValidationError('Invalid limit: must be an integer.')

    history = get_job_history(job_id=job_id, limit=limit)
    return jsonify({
        'history': history,
        'total': len(history),
        'filters': {
            'job_id': job_id,
            'limit': limit,
        },
    })
```