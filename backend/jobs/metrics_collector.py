```python
"""
TickerPulse AI v3.0 - Metrics Collector Job
Background job that periodically collects system metrics and API quotas.
"""

import logging
import threading
from datetime import datetime, timedelta

from backend.health_monitor import collect_metrics_snapshot
from backend.database import get_adapter
from backend.core.quota_manager import get_quota_manager

logger = logging.getLogger(__name__)

# Thread-safe lock for concurrent collection
_collection_lock = threading.Lock()
_last_collection_time = None


def collect_metrics_job() -> None:
    """
    Background job to collect system metrics.

    Collects a snapshot of health metrics and stores them in the database.
    Ensures only one collection job runs at a time using a lock.

    This job is scheduled to run every 60 seconds.
    """
    global _last_collection_time

    # Use lock to ensure only one job runs at a time
    if not _collection_lock.acquire(blocking=False):
        logger.debug("Metrics collection already in progress, skipping this interval")
        return

    try:
        logger.debug("Starting metrics collection")
        collect_metrics_snapshot()
        _last_collection_time = datetime.utcnow()
        logger.debug("Metrics collection completed successfully")
    except Exception as e:
        logger.error("Error during metrics collection: %s", e)
    finally:
        _collection_lock.release()


def cleanup_old_metrics(days_to_keep: int = 30) -> None:
    """
    Clean up metrics older than the specified number of days.

    This job should be scheduled to run once per day.

    Parameters
    ----------
    days_to_keep : int
        Number of days of metrics to retain (default: 30)
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)

        adapter = get_adapter()
        sql = 'DELETE FROM metrics WHERE timestamp < ?'

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, sql, (cutoff_time.isoformat() + 'Z',))
            conn.commit()
            deleted_rows = cursor.rowcount if cursor else 0

        logger.info("Cleanup completed: deleted %d old metrics", deleted_rows)
    except Exception as e:
        logger.error("Error during metrics cleanup: %s", e)


def cleanup_old_quota_history(days_to_keep: int = 30) -> None:
    """
    Clean up quota history older than the specified number of days.

    Parameters
    ----------
    days_to_keep : int
        Number of days of quota history to retain (default: 30)
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)

        adapter = get_adapter()
        sql = 'DELETE FROM quota_history WHERE recorded_at < ?'

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, sql, (cutoff_time.isoformat() + 'Z',))
            conn.commit()
            deleted_rows = cursor.rowcount if cursor else 0

        logger.info("Quota history cleanup completed: deleted %d old records", deleted_rows)
    except Exception as e:
        logger.error("Error during quota history cleanup: %s", e)


def collect_api_quotas_job() -> None:
    """
    Background job to collect and update API quota metrics.

    Periodically retrieves quota information from data providers
    and updates the api_quotas table. This job is scheduled to run
    every 5 minutes to keep quota information current.
    """
    try:
        logger.debug("Starting API quotas collection")
        quota_manager = get_quota_manager()

        # Import provider registry
        from backend.data_providers import create_registry

        registry = create_registry()

        # Collect quotas from all registered providers
        for provider in registry.list_providers():
            if not provider['is_available']:
                continue

            provider_name = provider['name']
            provider_obj = registry.get_provider(provider_name)

            try:
                # Call report_usage if provider implements it
                if hasattr(provider_obj, 'report_usage'):
                    quotas = provider_obj.report_usage()
                    if quotas:
                        for quota_type, limit_value, used, reset_at in quotas:
                            quota_manager.record_usage(
                                provider_name=provider_name,
                                quota_type=quota_type,
                                limit_value=limit_value,
                                used=used,
                                reset_at=reset_at,
                            )
            except Exception as e:
                logger.warning(
                    f"Failed to collect quotas for {provider_name}: {e}"
                )

        logger.debug("API quotas collection completed")
    except Exception as e:
        logger.error("Error during API quotas collection: %s", e)


def register_metrics_jobs(scheduler_manager) -> None:
    """
    Register metrics collection jobs with the scheduler.

    Parameters
    ----------
    scheduler_manager : SchedulerManager
        The application's scheduler manager instance
    """
    try:
        # Register the metrics collection job (runs every 60 seconds)
        scheduler_manager.add_job(
            'collect_metrics',
            'interval',
            seconds=60,
            job_func=collect_metrics_job,
            replace_existing=True,
        )

        # Register the API quotas collection job (runs every 5 minutes)
        scheduler_manager.add_job(
            'collect_api_quotas',
            'interval',
            seconds=300,
            job_func=collect_api_quotas_job,
            replace_existing=True,
        )

        # Register the cleanup job (runs daily at 2 AM)
        scheduler_manager.add_job(
            'cleanup_old_metrics',
            'cron',
            hour=2,
            minute=0,
            job_func=lambda: cleanup_old_metrics(days_to_keep=30),
            replace_existing=True,
        )

        # Register the quota history cleanup job (runs daily at 2:30 AM)
        scheduler_manager.add_job(
            'cleanup_quota_history',
            'cron',
            hour=2,
            minute=30,
            job_func=lambda: cleanup_old_quota_history(days_to_keep=30),
            replace_existing=True,
        )

        logger.info("Registered metrics collection, API quotas, and cleanup jobs")
    except Exception as e:
        logger.error("Error registering metrics jobs: %s", e)
```