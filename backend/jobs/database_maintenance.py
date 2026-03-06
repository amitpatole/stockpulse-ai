"""
Database maintenance job.

Schedule: Daily at 2:00 AM ET (off-hours)
Task: Clean up old data, optimize tables, and maintain database health
Output: Archive old records, rebuild indexes, vacuum database
"""
import logging
import sqlite3
from datetime import datetime, timedelta

from backend.config import Config
from backend.jobs._helpers import (
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'database_maintenance'
JOB_NAME = 'Database Maintenance'


def run_database_maintenance() -> None:
    """Execute database maintenance tasks.

    Steps:
        1. Archive old job_history records (> 90 days).
        2. Archive old agent_runs records (> 90 days).
        3. Delete old news records without sentiment (> 30 days).
        4. Purge old alerts (> 60 days).
        5. Rebuild indexes on frequently queried tables.
        6. Run VACUUM to reclaim disk space.
        7. Update statistics for query planner.
        8. Log summary of maintenance performed.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        stats = {
            'job_history_archived': 0,
            'agent_runs_archived': 0,
            'news_deleted': 0,
            'alerts_deleted': 0,
            'vacuum_completed': False,
            'analyze_completed': False,
        }

        try:
            # ---- 1. Archive old job_history records ----
            stats['job_history_archived'] = _archive_old_records(
                'job_history',
                days=90,
            )
            logger.info(f"Archived {stats['job_history_archived']} old job_history records")

            # ---- 2. Archive old agent_runs records ----
            stats['agent_runs_archived'] = _archive_old_records(
                'agent_runs',
                days=90,
                date_column='completed_at',
            )
            logger.info(f"Archived {stats['agent_runs_archived']} old agent_runs records")

            # ---- 3. Delete old news records without sentiment ----
            stats['news_deleted'] = _delete_old_news(days=30)
            logger.info(f"Deleted {stats['news_deleted']} old news records")

            # ---- 4. Purge old alerts ----
            stats['alerts_deleted'] = _delete_old_alerts(days=60)
            logger.info(f"Deleted {stats['alerts_deleted']} old alert records")

            # ---- 5. Rebuild indexes ----
            _rebuild_indexes()
            logger.info("Rebuilt database indexes")

            # ---- 6. Vacuum database ----
            _vacuum_database()
            stats['vacuum_completed'] = True
            logger.info("Database vacuumed")

            # ---- 7. Update statistics ----
            _analyze_tables()
            stats['analyze_completed'] = True
            logger.info("Database statistics updated")

            ctx['result_summary'] = (
                f"Archived {stats['job_history_archived'] + stats['agent_runs_archived']} records. "
                f"Deleted {stats['news_deleted'] + stats['alerts_deleted']} old entries. "
                f"Vacuum and analyze completed."
            )

        except Exception as exc:
            ctx['status'] = 'error'
            ctx['result_summary'] = f'Maintenance error: {exc}'
            logger.error(f"Database maintenance failed: {exc}", exc_info=True)


def _archive_old_records(
    table: str,
    days: int,
    date_column: str = 'executed_at',
) -> int:
    """Archive (delete) records older than N days.

    Parameters
    ----------
    table : str
        Table name (job_history or agent_runs)
    days : int
        Records older than this many days will be deleted
    date_column : str
        Name of timestamp column to check

    Returns
    -------
    int
        Number of records deleted
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        # Count records to delete
        count_result = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {date_column} < ?",
            (cutoff_iso,),
        ).fetchone()
        count = count_result[0] if count_result else 0

        # Delete records
        if count > 0:
            conn.execute(
                f"DELETE FROM {table} WHERE {date_column} < ?",
                (cutoff_iso,),
            )
            conn.commit()

        conn.close()
        return count

    except Exception as exc:
        logger.error(f"Failed to archive records from {table}: {exc}")
        return 0


def _delete_old_news(days: int) -> int:
    """Delete old news records without sentiment analysis.

    Parameters
    ----------
    days : int
        Delete news older than this many days

    Returns
    -------
    int
        Number of records deleted
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        # Count records to delete
        count_result = conn.execute(
            """SELECT COUNT(*) FROM news
               WHERE (sentiment_score IS NULL OR sentiment_score = 0)
               AND created_at < ?""",
            (cutoff_iso,),
        ).fetchone()
        count = count_result[0] if count_result else 0

        # Delete records
        if count > 0:
            conn.execute(
                """DELETE FROM news
                   WHERE (sentiment_score IS NULL OR sentiment_score = 0)
                   AND created_at < ?""",
                (cutoff_iso,),
            )
            conn.commit()

        conn.close()
        return count

    except Exception as exc:
        logger.error(f"Failed to delete old news records: {exc}")
        return 0


def _delete_old_alerts(days: int) -> int:
    """Delete old alert records.

    Parameters
    ----------
    days : int
        Delete alerts older than this many days

    Returns
    -------
    int
        Number of records deleted
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        # Count records to delete
        count_result = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE created_at < ?",
            (cutoff_iso,),
        ).fetchone()
        count = count_result[0] if count_result else 0

        # Delete records
        if count > 0:
            conn.execute(
                "DELETE FROM alerts WHERE created_at < ?",
                (cutoff_iso,),
            )
            conn.commit()

        conn.close()
        return count

    except Exception as exc:
        logger.error(f"Failed to delete old alerts: {exc}")
        return 0


def _rebuild_indexes() -> None:
    """Rebuild all database indexes.

    Useful after bulk delete operations.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        # List of important indexes
        indexes = [
            'idx_agent_runs_status',
            'idx_agent_runs_agent',
            'idx_agent_runs_started',
            'idx_job_history_job_id',
            'idx_job_history_executed',
            'idx_cost_tracking_date',
            'idx_cost_tracking_agent',
            'idx_ai_ratings_ticker',
            'idx_news_ticker',
            'idx_news_created',
            'idx_alerts_created',
        ]

        for idx in indexes:
            try:
                conn.execute(f"REINDEX {idx}")
            except Exception as exc:
                logger.debug(f"Could not reindex {idx}: {exc}")

        conn.commit()
        conn.close()

    except Exception as exc:
        logger.error(f"Failed to rebuild indexes: {exc}")


def _vacuum_database() -> None:
    """Vacuum database to reclaim disk space.

    This rebuilds the database file, removing dead space from
    deleted records.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database vacuumed successfully")

    except Exception as exc:
        logger.error(f"Failed to vacuum database: {exc}")


def _analyze_tables() -> None:
    """Run ANALYZE to update query planner statistics.

    This helps SQLite choose better query plans.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.execute("ANALYZE")
        conn.commit()
        conn.close()
        logger.info("Database statistics updated")

    except Exception as exc:
        logger.error(f"Failed to analyze database: {exc}")
