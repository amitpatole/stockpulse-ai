```python
from typing import Any, Optional
import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from contextlib import asynccontextmanager
from config import BACKUP_PATH, BACKUP_SCHEDULE

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect('tickerpulse.db', uri=True, isolation_level=None, factory=sqlite3.Row)
    try:
        yield conn
    finally:
        conn.close()

async def backup_database() -> str:
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = os.path.join(BACKUP_PATH, f'tickerpulse_{timestamp}.db')
    logging.info(f"Starting backup to {backup_file}")
    
    async with get_db_connection() as conn:
        with conn.backup_to(backup_file) as backup:
            backup.execute_sql("PRAGMA journal_mode=WAL")
            backup.execute_sql("PRAGMA foreign_keys=ON")
            await backup.step()

    logging.info(f"Backup completed to {backup_file}")
    return backup_file

async def restore_database(backup_file: str) -> bool:
    logging.info(f"Starting restore from {backup_file}")
    
    async with get_db_connection() as conn:
        with conn.backup_from(backup_file) as restore:
            restore.execute_sql("PRAGMA journal_mode=WAL")
            restore.execute_sql("PRAGMA foreign_keys=ON")
            await restore.step()

    logging.info(f"Restore completed from {backup_file}")
    return True

@app.route('/backup', methods=['POST'])
async def backup() -> Any:
    try:
        await backup_database()
        return jsonify({"status": "success", "message": "Backup completed successfully."}), 200
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/restore', methods=['POST'])
async def restore() -> Any:
    try:
        backup_file = request.form.get('file')
        if not backup_file:
            return jsonify({"status": "error", "message": "No backup file provided."}), 400
        
        await restore_database(backup_file)
        return jsonify({"status": "success", "message": "Restore completed successfully."}), 200
    except Exception as e:
        logging.error(f"Restore failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run()
```