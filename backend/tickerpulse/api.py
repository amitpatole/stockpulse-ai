```python
from typing import Any
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlite3 import Row
from contextlib import asynccontextmanager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickerpulse.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)

class LayoutConfig(db.Model):
    __tablename__ = 'layout_configs'
    id = db.Column(db.Integer, primary_key=True)
    user_agent = db.Column(db.String, unique=True, nullable=False)
    layout = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<LayoutConfig(user_agent={self.user_agent}, layout={self.layout})>"

@asynccontextmanager
async def get_db():
    """Async context manager for database operations."""
    db.session.expire_on_commit = False
    yield db.session
    await db.session.commit()

@app.route('/mobile_layout', methods=['GET'])
async def get_mobile_layout():
    """Endpoint to get mobile layout configuration."""
    user_agent = request.headers.get('User-Agent')
    if not user_agent:
        return jsonify({"error": "User-Agent header missing"}), 400

    async with get_db() as session:
        layout_config = await session.get(LayoutConfig, user_agent)
        if layout_config is None:
            # Default layout for unknown user agents
            layout_config = LayoutConfig(user_agent=user_agent, layout="mobile-responsive")
            await session.add(layout_config)
            await session.commit()

        return jsonify({"layout": layout_config.layout})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
```

--- FILE: backend/tickerpulse/models.py ---
```python
from typing import Any
from flask_sqlalchemy import SQLAlchemy
from sqlite3 import Row
from flask import Flask

db = SQLAlchemy()

class LayoutConfig(db.Model):
    __tablename__ = 'layout_configs'
    id = db.Column(db.Integer, primary_key=True)
    user_agent = db.Column(db.String, unique=True, nullable=False)
    layout = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<LayoutConfig(user_agent={self.user_agent}, layout={self.layout})>"

def init_app(app: Flask) -> None:
    db.init_app(app)
```