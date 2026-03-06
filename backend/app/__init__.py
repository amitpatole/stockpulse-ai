```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from backup_restore import backup_database, restore_database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickerpulse.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Schedule backup
import asyncio
import schedule
import time

async def schedule_backup():
    while True:
        await backup_database()
        await asyncio.sleep(60)  # Sleep for 1 minute

def start_scheduler():
    schedule.every().day.at("02:00").do(schedule_backup)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    start_scheduler()
    app.run()
```