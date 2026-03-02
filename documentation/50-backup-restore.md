```markdown
# Feature: Database Backup & Restore

## Overview
One-click backup and restore functionality for the SQLite database, with scheduled automatic backups. Allows users to create point-in-time snapshots of their TickerPulse database and restore from them, with configurable retention policies and scheduling.

## Data Model

### Database Tables

#### `backups`
Stores metadata about each backup file.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique backup identifier |
| filename | TEXT | UNIQUE NOT NULL | Backup file name (e.g., `stock_news.backup.20260302_170530.db`) |
| file_size | INTEGER | NOT NULL | Size in bytes |
| created_at | TIMESTAMP | NOT NULL DEFAULT CURRENT_TIMESTAMP | When backup was created |
| notes | TEXT | | Optional user notes |
| is_manual | BOOLEAN | NOT NULL DEFAULT 1 | 1=manual, 0=scheduled |
| checksum | TEXT | | SHA256 hash for integrity verification |

#### `backup_schedules`
Configuration for automatic backups.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Configuration ID |
| enabled | BOOLEAN | NOT NULL DEFAULT 0 | Whether automatic backups are enabled |
| schedule_time | TEXT | | Time of day in HH:MM format (e.g., "02:00") |
| retention_days | INTEGER | DEFAULT 30 | Keep backups for N days |
| max_backups | INTEGER | DEFAULT 10 | Maximum number of automatic backups to keep |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When schedule was created |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last modification time |

### Sample Data

```sql
INSERT INTO backups (filename, file_size, created_at, notes, is_manual, checksum)
VALUES ('stock_news.backup.20260302_170530.db', 15728640, '2026-03-02 17:05:30', 'Pre-update backup', 1, 'abc123def456...');

INSERT INTO backup_schedules (enabled, schedule_time, retention_days, max_backups)
VALUES (1, '02:00', 30, 10);
```

## API Endpoints

### Create Manual Backup
**POST /api/admin/backups**

Creates an immediate backup of the database.

**Request:**
```json
{
  "notes": "Optional backup notes"
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": 1,
    "filename": "stock_news.backup.20260302_170530.db",
    "file_size": 15728640,
    "created_at": "2026-03-02T17:05:30Z",
    "notes": "Optional backup notes",
    "is_manual": true,
    "checksum": "abc123def456..."
  },
  "meta": {}
}
```

**Error Cases:**
- 400: Disk space insufficient
- 500: Database backup failed

### List Backups
**GET /api/admin/backups?limit=50&offset=0**

Lists all backups with pagination (newest first).

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "filename": "stock_news.backup.20260302_170530.db",
      "file_size": 15728640,
      "created_at": "2026-03-02T17:05:30Z",
      "notes": "Manual backup",
      "is_manual": true,
      "checksum": "abc123def456..."
    }
  ],
  "meta": {
    "total_count": 1,
    "limit": 50,
    "offset": 0
  }
}
```

### Restore from Backup
**POST /api/admin/backups/{backup_id}/restore**

Restores database from specified backup. Current database is backed up first.

**Request:**
```json
{
  "verify_checksum": true
}
```

**Response (202 Accepted):**
```json
{
  "data": {
    "restore_id": "restore_20260302_170545",
    "status": "in_progress",
    "backup_id": 1,
    "backup_filename": "stock_news.backup.20260302_170530.db"
  },
  "meta": {}
}
```

**Error Cases:**
- 404: Backup not found
- 400: Current database cannot be backed up
- 422: Checksum verification failed (corrupt backup)

### Get Restore Status
**GET /api/admin/restores/{restore_id}**

Polls the status of a restore operation.

**Response (200 OK):**
```json
{
  "data": {
    "restore_id": "restore_20260302_170545",
    "status": "completed",
    "backup_id": 1,
    "started_at": "2026-03-02T17:05:45Z",
    "completed_at": "2026-03-02T17:05:55Z",
    "pre_restore_backup_id": 2
  },
  "meta": {}
}
```

### Delete Backup
**DELETE /api/admin/backups/{backup_id}**

Removes a backup file and its metadata record.

**Response (204 No Content)**

**Error Cases:**
- 404: Backup not found
- 400: Cannot delete; restore in progress

### Get Backup Schedule Configuration
**GET /api/admin/backup-schedule**

Retrieves current automatic backup schedule settings.

**Response (200 OK):**
```json
{
  "data": {
    "enabled": true,
    "schedule_time": "02:00",
    "retention_days": 30,
    "max_backups": 10,
    "next_scheduled_run": "2026-03-03T02:00:00Z"
  },
  "meta": {}
}
```

### Update Backup Schedule Configuration
**POST /api/admin/backup-schedule**

Updates automatic backup schedule settings.

**Request:**
```json
{
  "enabled": true,
  "schedule_time": "02:00",
  "retention_days": 30,
  "max_backups": 10
}
```

**Response (200 OK):**
```json
{
  "data": {
    "enabled": true,
    "schedule_time": "02:00",
    "retention_days": 30,
    "max_backups": 10,
    "next_scheduled_run": "2026-03-03T02:00:00Z"
  },
  "meta": {}
}
```

**Validation:**
- `schedule_time`: Must be valid HH:MM in 24-hour format
- `retention_days`: Integer >= 1
- `max_backups`: Integer >= 1

## Dashboard/UI Elements

### Admin Backup Manager Page

**Path:** `/admin/backups` or `/settings/backups` tab

**Sections:**

1. **Automatic Backup Settings**
   - Toggle: "Enable Scheduled Backups"
   - Input: "Backup Time" (HH:MM selector)
   - Input: "Retention Period" (days)
   - Input: "Maximum Backups" (count)
   - Button: "Save Schedule"
   - Display: "Next scheduled run: [date/time]"

2. **Manual Backup**
   - Input: "Optional notes" (text field)
   - Button: "Create Backup Now" (primary, disabled during backup)
   - Progress: Spinner while creating backup
   - Success: Toast notification "Backup created successfully"

3. **Backups List**
   - Table columns:
     - Backup Date (formatted: "Mar 2, 2026 5:05 PM")
     - File Size (formatted: "15 MB")
     - Type (Manual/Automatic)
     - Notes (truncated)
     - Actions: Restore, Download, Delete
   - Pagination: 50 backups per page
   - Sorting: By date (newest first)
   - Empty state: "No backups yet"

4. **Restore Confirmation Dialog**
   - Warning: "Restoring will replace current database"
   - Message: Show which backup will be restored
   - Note: "Current database will be backed up first as: [filename]"
   - Checkbox: "Verify backup integrity before restoring"
   - Buttons: Cancel, Restore (danger variant)
   - Status modal during restore: Show progress

## Business Rules

- **Backup Creation**: Disallows starting new backup if one is in progress
- **Automatic Backups**: Run once per day at configured time; skip if manual backup already created that day
- **Retention**: Delete backups older than retention_days; keep maximum max_backups regardless of age
- **Restore Safety**: Always creates pre-restore backup before replacing current database
- **Concurrent Operations**: No concurrent backups/restores; queue or reject if in-progress
- **File Storage**: Backups stored in `{BASE_DIR}/backups/` directory
- **Disk Space**: Check available disk space before backup; fail gracefully if insufficient
- **Integrity**: Calculate SHA256 checksum on backup; verify on restore
- **Admin Only**: All backup/restore operations require admin authentication
- **Pagination**: Default 50 items/page, max 100 items/page

## Edge Cases

- **Empty Database**: Backup succeeds; file size reflects empty database
- **Large Database**: Progress indication during backup/restore; timeout after 5 minutes
- **Insufficient Disk Space**: Return 400 error with available space in message
- **Corrupted Backup**: Detect via checksum mismatch; prevent restore; suggest manual recovery
- **Concurrent Restore Requests**: Queue or reject duplicate restore requests for same backup
- **Delete During Restore**: Prevent deletion of backup being restored
- **Network Interruption**: Restore operation is atomic (all-or-nothing); no partial states
- **Backup File Permissions**: Ensure backups are readable/writable by app process
- **Orphaned Backups**: Periodically clean up backup metadata for deleted files

## Security

- **Access Control**: All endpoints require admin role (Flask-Login authentication)
- **Path Traversal**: Prevent directory traversal in backup file selection (validate against whitelist)
- **SQL Injection**: No SQL injection risk (using parameterized queries with sqlite3)
- **Backup Encryption**: Backups stored as plaintext SQLite (no encryption required; same as source)
- **Audit Logging**: Log all backup/restore operations with timestamps and user IDs
- **Rate Limiting**: Limit manual backups to 1 per minute per user
- **Checksum Verification**: SHA256 hash prevents accidental corruption detection

## Testing

### Unit Tests

File: `backend/tests/test_backup_manager.py`

**Test Cases:**
1. `test_create_backup_success` - Full backup creation flow
2. `test_create_backup_insufficient_disk_space` - Graceful failure
3. `test_backup_checksum_calculation` - SHA256 verification
4. `test_list_backups_pagination` - Offset/limit handling
5. `test_delete_backup_success` - File + metadata deletion
6. `test_delete_backup_not_found` - Returns 404
7. `test_restore_from_backup` - Full restore flow with pre-backup
8. `test_restore_checksum_mismatch` - Prevents restore of corrupt backup
9. `test_concurrent_backup_prevention` - Rejects second backup during first
10. `test_auto_backup_schedule_trigger` - Scheduled task execution
11. `test_retention_cleanup` - Removes old backups based on policy

### E2E Tests

File: `frontend/src/components/__tests__/BackupManager.test.tsx`

**Test Cases:**
1. Render backup manager page
2. Create manual backup with notes
3. List and paginate backups
4. Restore from backup with confirmation
5. Delete backup with confirmation
6. Update automatic backup schedule
7. View next scheduled run time
8. Handle backup errors with toast

## Changes & Deprecations

### Version 3.3.0
- Initial release
- One-click backup/restore
- Scheduled automatic backups
- Backup list with pagination
- Restore checksum verification
```