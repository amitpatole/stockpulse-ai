```python
"""
TickerPulse AI v3.0 - Database Backup & Restore Manager
Point-in-time backup creation, restoration, and scheduled retention.
"""

import hashlib
import logging
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any

from backend.config import Config
from backend.database import db_session, get_db_connection

logger = logging.getLogger(__name__)

# Backup directory location
BACKUPS_DIR = Path(Config.BASE_DIR) / '.tickerpulse' / 'backups'

# Rate limit: prevent concurrent backups within 5 minutes
_BACKUP_LOCK = Lock()
_LAST_BACKUP_TIME: dict[str, datetime] = {}
_MIN_BACKUP_INTERVAL_SECONDS = 300  # 5 minutes


# ---------------------------------------------------------------------------
# Directory & Schema Setup
# ---------------------------------------------------------------------------

def ensure_backups_directory() -> None:
    """Create backups directory if it doesn't exist."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Backups directory ready: {BACKUPS_DIR}")


def _ensure_backup_tables() -> None:
    """Create backup metadata tables if they don't exist."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Backups metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                file_size INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                is_manual BOOLEAN NOT NULL DEFAULT 1,
                checksum TEXT
            )
        ''')
        
        # Backup schedule configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enabled BOOLEAN NOT NULL DEFAULT 0,
                schedule_time TEXT,
                retention_days INTEGER DEFAULT 30,
                max_backups INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()


# ---------------------------------------------------------------------------
# Backup Creation & Checksum
# ---------------------------------------------------------------------------

def calculate_checksum(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file.
    
    Parameters
    ----------
    filepath : Path
        Path to the file to checksum.
    
    Returns
    -------
    str
        SHA256 hex digest (64 characters).
    """
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_backup(notes: str = '', is_manual: bool = True) -> dict[str, Any]:
    """Create a point-in-time backup of the database.
    
    Parameters
    ----------
    notes : str, optional
        Human-readable notes about this backup.
    is_manual : bool, default True
        True if user-initiated, False if automated.
    
    Returns
    -------
    dict
        Backup metadata: id, filename, file_size, created_at, notes, is_manual, checksum.
    
    Raises
    ------
    RuntimeError
        If a backup was created within the last 5 minutes (rate limit).
    """
    ensure_backups_directory()
    _ensure_backup_tables()
    
    with _BACKUP_LOCK:
        # Check rate limit
        last_time = _LAST_BACKUP_TIME.get('last_backup')
        if last_time and (datetime.now() - last_time).total_seconds() < _MIN_BACKUP_INTERVAL_SECONDS:
            raise RuntimeError(
                f'Backup rate limit exceeded. Please wait {_MIN_BACKUP_INTERVAL_SECONDS}s '
                'before creating another backup.'
            )
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.db'
        backup_path = BACKUPS_DIR / backup_filename
        
        # Create backup by copying the live database file
        source_db = Path(Config.DB_PATH)
        if not source_db.exists():
            raise RuntimeError(f'Source database not found: {source_db}')
        
        try:
            shutil.copy2(source_db, backup_path)
            logger.info(f'Backup created: {backup_path}')
        except Exception as e:
            logger.error(f'Failed to create backup: {e}')
            raise RuntimeError(f'Backup creation failed: {e}')
        
        # Calculate file size and checksum
        file_size = backup_path.stat().st_size
        checksum = calculate_checksum(backup_path)
        
        # Store metadata in database
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backups (filename, file_size, notes, is_manual, checksum)
                VALUES (?, ?, ?, ?, ?)
            ''', (backup_filename, file_size, notes, is_manual, checksum))
            
            backup_id = cursor.lastrowid
            conn.commit()
        
        # Update rate limit tracker
        _LAST_BACKUP_TIME['last_backup'] = datetime.now()
        
        return {
            'id': backup_id,
            'filename': backup_filename,
            'file_size': file_size,
            'created_at': datetime.now().isoformat(),
            'notes': notes,
            'is_manual': is_manual,
            'checksum': checksum,
        }


# ---------------------------------------------------------------------------
# Backup Listing & Deletion
# ---------------------------------------------------------------------------

def list_backups(
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """List all backups with pagination.
    
    Parameters
    ----------
    limit : int, default 20
        Number of backups to return. Clamped to [1, 100].
    offset : int, default 0
        Number of backups to skip.
    
    Returns
    -------
    dict
        Response with keys:
        - data: List of backup dicts
        - meta: Pagination metadata (total_count, limit, offset, has_next)
    """
    _ensure_backup_tables()
    
    # Clamp limit to [1, 100]
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM backups')
        total_count = cursor.fetchone()[0]
        
        # Get paginated results (newest first)
        cursor.execute('''
            SELECT id, filename, file_size, created_at, notes, is_manual, checksum
            FROM backups
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        backups = [dict(row) for row in rows]
    
    return {
        'data': backups,
        'meta': {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total_count,
        }
    }


def delete_backup(backup_id: int) -> bool:
    """Delete a backup and remove its file.
    
    Parameters
    ----------
    backup_id : int
        The backup record ID.
    
    Returns
    -------
    bool
        True if deleted successfully, False if backup not found.
    """
    _ensure_backup_tables()
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Get backup metadata
        cursor.execute('SELECT filename FROM backups WHERE id = ?', (backup_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        filename = row['filename']
        backup_path = BACKUPS_DIR / filename
        
        try:
            # Delete file if it exists
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f'Deleted backup file: {backup_path}')
        except Exception as e:
            logger.warning(f'Failed to delete backup file: {e}')
        
        # Delete database record
        cursor.execute('DELETE FROM backups WHERE id = ?', (backup_id,))
        conn.commit()
        
        return True


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------

def start_restore(backup_id: int) -> dict[str, Any]:
    """Restore the database from a backup.
    
    Parameters
    ----------
    backup_id : int
        The backup record ID to restore from.
    
    Returns
    -------
    dict
        Restore status with keys: backup_id, restored_at, filename.
    
    Raises
    ------
    RuntimeError
        If backup not found or restore fails.
    """
    _ensure_backup_tables()
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Get backup metadata
        cursor.execute(
            'SELECT id, filename, checksum FROM backups WHERE id = ?',
            (backup_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            raise RuntimeError(f'Backup {backup_id} not found')
        
        filename = row['filename']
        stored_checksum = row['checksum']
        backup_path = BACKUPS_DIR / filename
        
        if not backup_path.exists():
            raise RuntimeError(f'Backup file not found: {backup_path}')
        
        # Verify backup integrity via checksum
        computed_checksum = calculate_checksum(backup_path)
        if computed_checksum != stored_checksum:
            raise RuntimeError(
                f'Backup integrity check failed. Expected {stored_checksum}, '
                f'got {computed_checksum}'
            )
        
        # Close any active connections before swapping
        conn.close()
    
    # Atomic swap: backup current DB, restore from backup
    current_db = Path(Config.DB_PATH)
    current_db_backup = current_db.with_suffix('.db.pre-restore')
    
    try:
        # Back up current state
        if current_db.exists():
            shutil.copy2(current_db, current_db_backup)
        
        # Restore from backup
        shutil.copy2(backup_path, current_db)
        logger.info(f'Restored database from {filename}')
        
        # Clean up temporary backup
        if current_db_backup.exists():
            current_db_backup.unlink()
        
    except Exception as e:
        # Restore from pre-restore backup if copy failed
        if current_db_backup.exists():
            shutil.copy2(current_db_backup, current_db)
            current_db_backup.unlink()
        logger.error(f'Restore failed: {e}')
        raise RuntimeError(f'Restore failed: {e}')
    
    return {
        'backup_id': backup_id,
        'restored_at': datetime.now().isoformat(),
        'filename': filename,
    }


# ---------------------------------------------------------------------------
# Scheduled Backups
# ---------------------------------------------------------------------------

def get_backup_schedule() -> dict[str, Any]:
    """Get the current backup schedule configuration.
    
    Returns
    -------
    dict
        Schedule config with keys: enabled, schedule_time, retention_days, max_backups.
        Returns defaults if no schedule is configured.
    """
    _ensure_backup_tables()
    
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, enabled, schedule_time, retention_days, max_backups
            FROM backup_schedules
            ORDER BY id DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
    
    if row:
        return {
            'id': row['id'],
            'enabled': bool(row['enabled']),
            'schedule_time': row['schedule_time'],
            'retention_days': row['retention_days'],
            'max_backups': row['max_backups'],
        }
    
    # Return defaults
    return {
        'enabled': False,
        'schedule_time': '02:00',
        'retention_days': 30,
        'max_backups': 10,
    }


def set_backup_schedule(
    enabled: bool,
    schedule_time: str,
    retention_days: int,
    max_backups: int,
) -> dict[str, Any]:
    """Update the backup schedule configuration.
    
    Parameters
    ----------
    enabled : bool
        Whether automatic backups are enabled.
    schedule_time : str
        Time to run backups in 24-hour format (HH:MM). Must be valid.
    retention_days : int
        How many days to keep backups. Must be >= 1.
    max_backups : int
        Maximum number of backups to keep. Must be >= 1.
    
    Returns
    -------
    dict
        Updated schedule configuration.
    
    Raises
    ------
    ValueError
        If any parameter is invalid.
    """
    _ensure_backup_tables()
    
    # Validate schedule_time format (HH:MM)
    try:
        parts = schedule_time.split(':')
        if len(parts) != 2:
            raise ValueError()
        hour, minute = int(parts[0]), int(parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError(f'Invalid schedule_time format: {schedule_time}. Use HH:MM.')
    
    # Validate retention_days and max_backups
    if retention_days < 1:
        raise ValueError('retention_days must be >= 1')
    if max_backups < 1:
        raise ValueError('max_backups must be >= 1')
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Insert or replace schedule (keep only latest)
        cursor.execute('''
            DELETE FROM backup_schedules
        ''')
        
        cursor.execute('''
            INSERT INTO backup_schedules (enabled, schedule_time, retention_days, max_backups)
            VALUES (?, ?, ?, ?)
        ''', (enabled, schedule_time, retention_days, max_backups))
        
        conn.commit()
    
    return {
        'enabled': enabled,
        'schedule_time': schedule_time,
        'retention_days': retention_days,
        'max_backups': max_backups,
    }


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def _cleanup_old_backups(retention_days: int = 30, max_backups: int = 10) -> None:
    """Delete old backups based on retention policy.
    
    Parameters
    ----------
    retention_days : int, default 30
        Delete backups older than this many days.
    max_backups : int, default 10
        Keep only this many most recent backups.
    """
    _ensure_backup_tables()
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Find backups to delete (oldest first, but respect max_backups)
        cursor.execute('''
            SELECT id, filename
            FROM backups
            ORDER BY created_at DESC
            LIMIT -1 OFFSET ?
        ''', (max_backups,))
        
        excess_backups = cursor.fetchall()
        
        for row in excess_backups:
            backup_id = row['id']
            filename = row['filename']
            backup_path = BACKUPS_DIR / filename
            
            # Also delete if older than retention_days
            cursor.execute(
                'SELECT created_at FROM backups WHERE id = ?',
                (backup_id,)
            )
            created = cursor.fetchone()['created_at']
            
            try:
                created_dt = datetime.fromisoformat(created)
                if created_dt < cutoff_date or len(excess_backups) > 0:
                    # Delete file
                    if backup_path.exists():
                        backup_path.unlink()
                        logger.info(f'Cleaned up old backup: {filename}')
                    
                    # Delete record
                    cursor.execute('DELETE FROM backups WHERE id = ?', (backup_id,))
            except Exception as e:
                logger.warning(f'Failed to cleanup backup {backup_id}: {e}')
        
        conn.commit()
```