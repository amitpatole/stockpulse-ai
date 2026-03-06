from typing import Any, Dict, List
import sqlite3
from sqlite3 import Row
from flask import Flask, request, jsonify
from contextlib import asynccontextmanager

app = Flask(__name__)

# Configuration
DATABASE_PATH = "tickerpulse.db"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

async def init_db() -> None:
    async with get_db_connection() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT FALSE
            );
            """
        )

async def get_notifications(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    async with get_db_connection() as conn:
        query = """
        SELECT id, title, message, read
        FROM notifications
        WHERE 1=1
        """
        params = []
        if filters.get("read") is not None:
            query += " AND read = ?"
            params.append(filters["read"])
        if filters.get("unread") is not None:
            query += " AND read = ?"
            params.append(not filters["unread"])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def mark_notification_as_read(notification_id: int) -> None:
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE notifications SET read = ? WHERE id = ?",
            (True, notification_id)
        )

@app.route('/notifications', methods=['GET'])
async def get_all_notifications() -> Dict[str, Any]:
    filters = request.args.to_dict()
    notifications = await get_notifications(filters)
    return {"notifications": notifications}

@app.route('/notifications/<int:notification_id>/read', methods=['PUT'])
async def mark_notification_read(notification_id: int) -> Dict[str, Any]:
    await mark_notification_as_read(notification_id)
    return {"message": "Notification marked as read"}

if __name__ == '__main__':
    init_db()
    app.run(debug=True)