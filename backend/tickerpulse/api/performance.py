```python
from typing import Any, Dict
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Row
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)

# Load configuration from environment variables
DB_URL = os.getenv('DB_URL', 'sqlite:///tickerpulse.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Async SQLAlchemy setup
@asynccontextmanager
async def get_async_session():
    engine = create_async_engine(DB_URL, echo=True, connect_args={"check_same_thread": False})
    async_session = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    async with async_session() as session:
        yield session

class PerformanceMetric(db.Model):
    __tablename__ = 'performance_metrics'
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String, nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

@app.route('/api/performance', methods=['GET'])
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Fetches performance metrics from the database.

    Returns:
        Dict[str, Any]: A dictionary containing performance metrics.
    """
    try:
        async with get_async_session() as session:
            metrics = await session.query(PerformanceMetric).order_by(PerformanceMetric.timestamp.desc()).limit(10).all()
            return [metric.__dict__ for metric in metrics]
    except Exception as e:
        logging.error(f"Error fetching performance metrics: {e}")
        return {"error": str(e)}, 500

@app.route('/api/performance/monitor', methods=['POST'])
async def monitor_performance() -> Dict[str, Any]:
    """
    Monitors and records performance metrics.

    Args:
        metric_name (str): The name of the metric.
        metric_value (float): The value of the metric.

    Returns:
        Dict[str, Any]: A success message or error details.
    """
    try:
        metric_name = request.form.get('metric_name')
        metric_value = float(request.form.get('metric_value'))
        timestamp = request.form.get('timestamp')

        if not metric_name or not metric_value or not timestamp:
            return {"error": "Missing required fields"}, 400

        metric = PerformanceMetric(metric_name=metric_name, metric_value=metric_value, timestamp=timestamp)
        async with get_async_session() as session:
            session.add(metric)
            await session.commit()
        return {"message": "Performance metric recorded successfully"}
    except Exception as e:
        logging.error(f"Error monitoring performance: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
```