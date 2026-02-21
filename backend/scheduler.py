"""
APScheduler configuration and management for TickerPulse AI.
Sets up job store (SQLite), job defaults, and exposes helpers.
"""
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from backend.config import Config

# Timezone alias map -- pytz on some systems does not ship the short
# ``US/Eastern`` aliases.  Map them to their canonical IANA names.
_TZ_ALIASES = {
    'US/Eastern': 'America/New_York',
    'US/Central': 'America/Chicago',
    'US/Mountain': 'America/Denver',
    'US/Pacific': 'America/Los_Angeles',
}


def _tz(name: str):
    """Return a pytz timezone, resolving common aliases."""
    try:
        return pytz.timezone(name)
    except pytz.exceptions.UnknownTimeZoneError:
        canonical = _TZ_ALIASES.get(name)
        if canonical:
            return pytz.timezone(canonical)
        raise

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manages all scheduled jobs for TickerPulse AI."""

    def __init__(self, app=None):
        self.scheduler = None
        self.app = app
        self._job_registry: Dict[str, Dict[str, Any]] = {}  # name -> job metadata

    def init_app(self, app):
        """Initialize scheduler with Flask app."""
        self.app = app

        # Configure APScheduler
        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{Config.DB_PATH}')
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }
        job_defaults = {
            'coalesce': True,  # If job missed multiple times, only run once
            'max_instances': 1,
            'misfire_grace_time': 300,  # 5 min grace period
        }

        timezone = _tz(Config.MARKET_TIMEZONE)

        # Use app's scheduler if available (Flask-APScheduler), else create new
        if hasattr(app, 'scheduler') and app.scheduler:
            self.scheduler = app.scheduler.scheduler  # Get underlying APScheduler
        else:
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=timezone,
            )

    def register_job(self, job_id: str, func, trigger: str, name: str,
                     description: str, **trigger_args):
        """Register a scheduled job.

        Parameters
        ----------
        job_id : str
            Unique identifier for the job (e.g. ``morning_briefing``).
        func : callable
            The function to execute.
        trigger : str
            APScheduler trigger type: ``'cron'``, ``'interval'``, or ``'date'``.
        name : str
            Human-readable name shown in the UI.
        description : str
            Longer description of what the job does.
        **trigger_args
            Keyword arguments forwarded to the APScheduler trigger
            (e.g. ``hour=8, minute=30, day_of_week='mon-fri'``).
        """
        self._job_registry[job_id] = {
            'name': name,
            'description': description,
            'func': func,
            'trigger': trigger,
            'trigger_args': trigger_args,
            'enabled': True,
        }

    def start_all_jobs(self):
        """Add all registered jobs to scheduler and start."""
        for job_id, meta in self._job_registry.items():
            if meta['enabled']:
                try:
                    self.scheduler.add_job(
                        meta['func'],
                        meta['trigger'],
                        id=job_id,
                        name=meta['name'],
                        replace_existing=True,
                        **meta['trigger_args'],
                    )
                    logger.info("Scheduled job: %s (%s)", job_id, meta['name'])
                except Exception as exc:
                    logger.error("Failed to schedule job %s: %s", job_id, exc)

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started with %d active jobs",
                        len(self.scheduler.get_jobs()))

    def get_all_jobs(self) -> List[Dict]:
        """List all jobs with their status."""
        jobs = []
        for job_id, meta in self._job_registry.items():
            sched_job = self.scheduler.get_job(job_id) if self.scheduler else None
            jobs.append({
                'id': job_id,
                'name': meta['name'],
                'description': meta['description'],
                'enabled': meta['enabled'],
                'next_run': str(sched_job.next_run_time) if sched_job and sched_job.next_run_time else None,
                'trigger': str(sched_job.trigger) if sched_job else meta['trigger'],
            })
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get details for a single job by ID."""
        meta = self._job_registry.get(job_id)
        if not meta:
            return None
        sched_job = self.scheduler.get_job(job_id) if self.scheduler else None
        return {
            'id': job_id,
            'name': meta['name'],
            'description': meta['description'],
            'enabled': meta['enabled'],
            'next_run': str(sched_job.next_run_time) if sched_job and sched_job.next_run_time else None,
            'trigger': str(sched_job.trigger) if sched_job else meta['trigger'],
        }

    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        if job_id not in self._job_registry:
            logger.warning("Cannot pause unknown job: %s", job_id)
            return False
        try:
            if self.scheduler:
                sched_job = self.scheduler.get_job(job_id)
                if sched_job:
                    self.scheduler.pause_job(job_id)
            self._job_registry[job_id]['enabled'] = False
            logger.info("Paused job: %s", job_id)
            return True
        except Exception as exc:
            logger.error("Failed to pause job %s: %s", job_id, exc)
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        if job_id not in self._job_registry:
            logger.warning("Cannot resume unknown job: %s", job_id)
            return False
        try:
            if self.scheduler:
                sched_job = self.scheduler.get_job(job_id)
                if sched_job:
                    self.scheduler.resume_job(job_id)
                else:
                    # Job was removed from scheduler while paused -- re-add it
                    meta = self._job_registry[job_id]
                    self.scheduler.add_job(
                        meta['func'],
                        meta['trigger'],
                        id=job_id,
                        name=meta['name'],
                        replace_existing=True,
                        **meta['trigger_args'],
                    )
            self._job_registry[job_id]['enabled'] = True
            logger.info("Resumed job: %s", job_id)
            return True
        except Exception as exc:
            logger.error("Failed to resume job %s: %s", job_id, exc)
            return False

    def trigger_job(self, job_id: str) -> bool:
        """Trigger immediate execution of a job."""
        if job_id not in self._job_registry:
            logger.warning("Cannot trigger unknown job: %s", job_id)
            return False
        try:
            meta = self._job_registry[job_id]
            # Add a one-shot job that runs immediately
            if self.scheduler:
                self.scheduler.add_job(
                    meta['func'],
                    'date',
                    id=f'{job_id}_manual_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                    name=f'{meta["name"]} (manual)',
                    run_date=datetime.now(_tz(Config.MARKET_TIMEZONE)),
                    replace_existing=False,
                )
            logger.info("Triggered immediate run of job: %s", job_id)
            return True
        except Exception as exc:
            logger.error("Failed to trigger job %s: %s", job_id, exc)
            return False

    def update_job_schedule(self, job_id: str, trigger: str, **trigger_args) -> bool:
        """Update a job's schedule.

        Parameters
        ----------
        job_id : str
            The job to reschedule.
        trigger : str
            New trigger type (``'cron'``, ``'interval'``).
        **trigger_args
            New trigger keyword arguments.
        """
        if job_id not in self._job_registry:
            logger.warning("Cannot update unknown job: %s", job_id)
            return False
        try:
            # Update the registry
            self._job_registry[job_id]['trigger'] = trigger
            self._job_registry[job_id]['trigger_args'] = trigger_args

            # Reschedule in APScheduler
            if self.scheduler:
                sched_job = self.scheduler.get_job(job_id)
                if sched_job:
                    self.scheduler.reschedule_job(job_id, trigger=trigger, **trigger_args)
                else:
                    # Re-add if not currently in scheduler
                    meta = self._job_registry[job_id]
                    self.scheduler.add_job(
                        meta['func'],
                        trigger,
                        id=job_id,
                        name=meta['name'],
                        replace_existing=True,
                        **trigger_args,
                    )
            logger.info("Updated schedule for job %s: trigger=%s, args=%s",
                        job_id, trigger, trigger_args)
            return True
        except Exception as exc:
            logger.error("Failed to update job %s schedule: %s", job_id, exc)
            return False

    def is_market_hours(self, market: str = 'US') -> bool:
        """Check if currently within market hours.

        Parameters
        ----------
        market : str
            ``'US'`` or ``'India'``.

        Returns
        -------
        bool
            True if the current time is within market trading hours for the
            given market and it is a weekday.
        """
        if market.upper() == 'INDIA':
            tz = _tz(Config.INDIA_MARKET_TIMEZONE)
            open_str = Config.INDIA_MARKET_OPEN   # '09:15'
            close_str = Config.INDIA_MARKET_CLOSE  # '15:30'
        else:
            tz = _tz(Config.MARKET_TIMEZONE)
            open_str = Config.US_MARKET_OPEN   # '09:30'
            close_str = Config.US_MARKET_CLOSE  # '16:00'

        now = datetime.now(tz)

        # Markets are closed on weekends (Monday=0, Sunday=6)
        if now.weekday() >= 5:
            return False

        open_h, open_m = map(int, open_str.split(':'))
        close_h, close_m = map(int, close_str.split(':'))

        market_open = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        market_close = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)

        return market_open <= now <= market_close


# Module-level singleton -- populated by backend.jobs.register_all_jobs()
scheduler_manager = SchedulerManager()
