```python
"""
TickerPulse AI v3.0 - Database Backup & Restore Manager
Handles backup creation, restoration, and automatic scheduling.
"""

import os
import shutil
import hashlib
import logging
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from backend.config import Config
from backend.database import db_session, get_db_connection

logger = logging.getLogger(__name__)

# Configuration
BACKUPS_DIR = Config.BASE_DIR / 'backups'
BACKUP_TIMEOUT_SECONDS = 300  # 5 minutes


def ensure_backups_directory() -> Path:
    """Create backups directory if it doesn't exist."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUPS_DIR


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_disk_free_space(path: Path) -> int:
    """Get free disk space in bytes at given path."""
    stat = os.statvfs(str(path))
    return stat.f_bavail * stat.f_frsize


def _get_backup_status(backup_id: int) -> Optional[Dict[str, Any]]:
    """Fetch backup record from database."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM backups WHERE id = ?',
            (backup_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


# ---------------------------------------------------------------------------
# Core backup operations
# ---------------------------------------------------------------------------

def create_backup(notes: str = '') -> Dict[str, Any]:
    """Create a backup of the current database.
    
    Parameters
    ----------
    notes : str
        Optional user notes for the backup.
    
    Returns
    -------
    dict
        Backup metadata: {id, filename, file_size, created_at, notes, checksum}
    
    Raises
    ------
    RuntimeError
        If backup fails (insufficient space, I/O error, etc.)
    """
    ensure_backups_directory()
    
    # Check for concurrent backup
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM backups WHERE created_at >= datetime("now", "-5 minutes") AND is_manual = 1')
        recent = cursor.fetchone()[0]
        if recent > 0:
            # Enforce rate limit (1 backup per minute)
            raise RuntimeError('Backup in progress or rate limit exceeded; try again in 60 seconds')
    
    # Check disk space (require at least 2x database size)
    db_size = Path(Config.DB_PATH).stat().st_size
    free_space = get_disk_free_space(BACKUPS_DIR)
    if free_space < db_size * 2:
        raise RuntimeError(
            f'Insufficient disk space: {free_space / (1024**3):.1f} GB free, '
            f'{db_size * 2 / (1024**3):.1f} GB required'
        )
    
    # Create backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'stock_news.backup.{timestamp}.db'
    backup_path = BACKUPS_DIR / backup_filename
    
    try:
        # Copy database file
        shutil.copy2(Config.DB_PATH, str(backup_path))
        
        # Calculate checksum
        checksum = calculate_checksum(backup_path)
        
        # Get file size
        file_size = backup_path.stat().st_size
        
        # Record in database
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO backups 
                   (filename, file_size, created_at, notes, is_manual, checksum)
                   VALUES (?, ?, datetime("now"), ?, 1, ?)''',
                (backup_filename, file_size, notes, checksum)
            )
            backup_id = cursor.lastrowid
            conn.commit()
        
        logger.info('Created backup %d: %s (%.1f MB)', 
                   backup_id, backup_filename, file_size / (1024**2))
        
        return {
            'id': backup_id,
            'filename': backup_filename,
            'file_size': file_size,
            'created_at': datetime.now().isoformat() + 'Z',
            'notes': notes,
            'is_manual': True,
            'checksum': checksum
        }
    except Exception as e:
        # Clean up partial backup
        if backup_path.exists():
            backup_path.unlink()
        logger.error('Backup failed: %s', str(e))
        raise RuntimeError(f'Backup failed: {str(e)}')


def list_backups(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List all backups with pagination (newest first).
    
    Parameters
    ----------
    limit : int
        Maximum number of backups to return (1-100).
    offset : int
        Number of backups to skip.
    
    Returns
    -------
    dict
        {data: [backups], meta: {total_count, limit, offset}}
    """
    limit = min(max(limit, 1), 100)  # Clamp to [1, 100]
    offset = max(offset, 0)
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM backups')
        total_count = cursor.fetchone()[0]
        
        # Get backups (newest first)
        cursor.execute(
            '''SELECT id, filename, file_size, created_at, notes, is_manual, checksum
               FROM backups
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?''',
            (limit, offset)
        )
        
        backups = [dict(row) for row in cursor.fetchall()]
    
    return {
        'data': backups,
        'meta': {
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    }


def delete_backup(backup_id: int) -> bool:
    """Delete a backup file and its metadata.
    
    Parameters
    ----------
    backup_id : int
        ID of backup to delete.
    
    Returns
    -------
    bool
        True if deleted, False if not found.
    
    Raises
    ------
    RuntimeError
        If restore is in progress for this backup.
    """
    backup = _get_backup_status(backup_id)
    if not backup:
        return False
    
    backup_path = BACKUPS_DIR / backup['filename']
    
    try:
        # Delete file
        if backup_path.exists():
            backup_path.unlink()
        
        # Delete metadata
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM backups WHERE id = ?', (backup_id,))
            conn.commit()
        
        logger.info('Deleted backup %d: %s', backup_id, backup['filename'])
        return True
    except Exception as e:
        logger.error('Failed to delete backup %d: %s', backup_id, str(e))
        raise RuntimeError(f'Delete failed: {str(e)}')


# ---------------------------------------------------------------------------
# Restore operations
# ---------------------------------------------------------------------------

_restore_in_progress: Dict[int, Dict[str, Any]] = {}
_restore_lock = threading.Lock()


def start_restore(backup_id: int, verify_checksum: bool = True) -> Dict[str, Any]:
    """Start a restore operation (background).
    
    First creates a backup of the current database before restoring.
    
    Parameters
    ----------
    backup_id : int
        ID of backup to restore from.
    verify_checksum : bool
        Whether to verify checksum before restoring.
    
    Returns
    -------
    dict
        Restore status: {restore_id, status, backup_id, backup_filename}
    
    Raises
    ------
    RuntimeError
        If backup not found, checksum mismatch, or restore fails.
    """
    backup = _get_backup_status(backup_id)
    if not backup:
        raise RuntimeError(f'Backup {backup_id} not found')
    
    backup_path = BACKUPS_DIR / backup['filename']
    if not backup_path.exists():
        raise RuntimeError(f'Backup file not found: {backup["filename"]}')
    
    # Verify checksum if requested
    if verify_checksum:
        actual_checksum = calculate_checksum(backup_path)
        if actual_checksum != backup['checksum']:
            raise RuntimeError(
                'Checksum mismatch: backup may be corrupted. '
                'Contact support for manual recovery.'
            )
    
    # Create pre-restore backup
    try:
        pre_restore = create_backup(f'Pre-restore backup before restoring backup #{backup_id}')
        pre_restore_backup_id = pre_restore['id']
    except Exception as e:
        raise RuntimeError(f'Could not create pre-restore backup: {str(e)}')
    
    # Start restore in background thread
    restore_id = f'restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    with _restore_lock:
        _restore_in_progress[backup_id] = {
            'restore_id': restore_id,
            'status': 'in_progress',
            'backup_id': backup_id,
            'backup_filename': backup['filename'],
            'started_at': datetime.now().isoformat() + 'Z',
            'pre_restore_backup_id': pre_restore_backup_id
        }
    
    def _do_restore():
        try:
            # Copy backup over current database
            shutil.copy2(str(backup_path), Config.DB_PATH)
            
            with _restore_lock:
                if backup_id in _restore_in_progress:
                    _restore_in_progress[backup_id]['status'] = 'completed'
                    _restore_in_progress[backup_id]['completed_at'] = (
                        datetime.now().isoformat() + 'Z'
                    )
            
            logger.info('Restore completed for backup %d', backup_id)
        except Exception as e:
            with _restore_lock:
                if backup_id in _restore_in_progress:
                    _restore_in_progress[backup_id]['status'] = 'failed'
                    _restore_in_progress[backup_id]['error'] = str(e)
            logger.error('Restore failed for backup %d: %s', backup_id, str(e))
    
    thread = threading.Thread(target=_do_restore, daemon=True)
    thread.start()
    
    return {
        'restore_id': restore_id,
        'status': 'in_progress',
        'backup_id': backup_id,
        'backup_filename': backup['filename']
    }


def get_restore_status(restore_id: str) -> Optional[Dict[str, Any]]:
    """Get status of an ongoing or completed restore."""
    with _restore_lock:
        for backup_id, status in _restore_in_progress.items():
            if status['restore_id'] == restore_id:
                return status.copy()
    return None


# ---------------------------------------------------------------------------
# Automatic backup scheduling
# ---------------------------------------------------------------------------

def get_backup_schedule() -> Dict[str, Any]:
    """Get current backup schedule configuration."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT enabled, schedule_time, retention_days, max_backups
               FROM backup_schedules LIMIT 1'''
        )
        row = cursor.fetchone()
    
    if not row:
        # Return defaults
        return {
            'enabled': False,
            'schedule_time': '02:00',
            'retention_days': 30,
            'max_backups': 10,
            'next_scheduled_run': None
        }
    
    config = dict(row)
    
    # Calculate next scheduled run
    if config['enabled'] and config['schedule_time']:
        next_run = _calculate_next_run(config['schedule_time'])
        config['next_scheduled_run'] = next_run.isoformat() + 'Z'
    else:
        config['next_scheduled_run'] = None
    
    return config


def set_backup_schedule(enabled: bool, schedule_time: str, 
                       retention_days: int, max_backups: int) -> Dict[str, Any]:
    """Update backup schedule configuration.
    
    Parameters
    ----------
    enabled : bool
        Whether to enable automatic backups.
    schedule_time : str
        Time in HH:MM format (24-hour).
    retention_days : int
        Keep backups for this many days.
    max_backups : int
        Maximum number of backups to keep.
    
    Returns
    -------
    dict
        Updated configuration with next_scheduled_run.
    
    Raises
    ------
    ValueError
        If schedule_time format is invalid.
    """
    # Validate schedule_time
    try:
        datetime.strptime(schedule_time, '%H:%M')
    except ValueError:
        raise ValueError(f'Invalid schedule_time format: {schedule_time}. Use HH:MM')
    
    if retention_days < 1:
        raise ValueError('retention_days must be >= 1')
    if max_backups < 1:
        raise ValueError('max_backups must be >= 1')
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Check if schedule exists
        cursor.execute('SELECT COUNT(*) FROM backup_schedules')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert
            cursor.execute(
                '''INSERT INTO backup_schedules
                   (enabled, schedule_time, retention_days, max_backups)
                   VALUES (?, ?, ?, ?)''',
                (enabled, schedule_time, retention_days, max_backups)
            )
        else:
            # Update
            cursor.execute(
                '''UPDATE backup_schedules
                   SET enabled = ?, schedule_time = ?, retention_days = ?, max_backups = ?,
                       updated_at = datetime("now")
                   WHERE id = 1''',
                (enabled, schedule_time, retention_days, max_backups)
            )
        
        conn.commit()
    
    return get_backup_schedule()


def _calculate_next_run(schedule_time: str) -> datetime:
    """Calculate next scheduled run time based on HH:MM."""
    hour, minute = map(int, schedule_time.split(':'))
    
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If time has already passed today, schedule for tomorrow
    if next_run <= now:
        next_run += timedelta(days=1)
    
    return next_run


def run_scheduled_backup() -> Optional[Dict[str, Any]]:
    """Run automatic backup if scheduled and enabled.
    
    Called by APScheduler task. Enforces retention policy.
    
    Returns
    -------
    dict or None
        Backup metadata if created, None if not needed.
    """
    config = get_backup_schedule()
    if not config['enabled']:
        return None
    
    try:
        backup = create_backup('Automatic scheduled backup')
        
        # Enforce retention policy
        _cleanup_old_backups(
            retention_days=config['retention_days'],
            max_backups=config['max_backups']
        )
        
        logger.info('Scheduled backup completed successfully')
        return backup
    except Exception as e:
        logger.error('Scheduled backup failed: %s', str(e))
        return None


def _cleanup_old_backups(retention_days: int, max_backups: int) -> None:
    """Delete backups older than retention_days or beyond max_backups limit."""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Delete by retention_days
        cursor.execute(
            'SELECT id, filename FROM backups WHERE created_at < ? ORDER BY created_at ASC',
            (cutoff_date.isoformat(),)
        )
        old_backups = cursor.fetchall()
        
        for backup_id, filename in old_backups:
            try:
                backup_path = BACKUPS_DIR / filename
                if backup_path.exists():
                    backup_path.unlink()
                cursor.execute('DELETE FROM backups WHERE id = ?', (backup_id,))
                logger.info('Cleaned up old backup: %s', filename)
            except Exception as e:
                logger.warning('Failed to clean up backup %s: %s', filename, str(e))
        
        # Delete beyond max_backups
        cursor.execute(
            '''SELECT id, filename FROM backups
               ORDER BY created_at DESC
               LIMIT -1 OFFSET ?''',
            (max_backups,)
        )
        excess_backups = cursor.fetchall()
        
        for backup_id, filename in excess_backups:
            try:
                backup_path = BACKUPS_DIR / filename
                if backup_path.exists():
                    backup_path.unlink()
                cursor.execute('DELETE FROM backups WHERE id = ?', (backup_id,))
                logger.info('Deleted excess backup: %s', filename)
            except Exception as e:
                logger.warning('Failed to delete excess backup %s: %s', filename, str(e))
        
        conn.commit()
```