```python
from typing import Dict, Any
import time
from flask import current_app
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class BackendStatus(Base):
    __tablename__ = 'backend_status'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    status = Column(String, nullable=False)
    latency = Column(Float)
    error_rate = Column(Float)

def get_backend_status() -> Dict[str, Any]:
    try:
        engine = current_app.extensions['sqlalchemy'].db.engine
        Session = sessionmaker(bind=engine)
        session = Session()

        status = session.query(BackendStatus).order_by(BackendStatus.timestamp.desc()).first()

        if status:
            return {
                'status': status.status,
                'timestamp': status.timestamp.isoformat(),
                'latency': status.latency,
                'error_rate': status.error_rate
            }
        else:
            return {'status': 'unknown', 'timestamp': None, 'latency': None, 'error_rate': None}
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error fetching backend status: {e}")
        return {'status': 'unknown', 'timestamp': None, 'latency': None, 'error_rate': None}
    finally:
        session.close()

def get_latest_backend_status() -> Dict[str, Any]:
    try:
        engine = current_app.extensions['sqlalchemy'].db.engine
        Session = sessionmaker(bind=engine, poolclass=NullPool)
        session = Session()

        status = session.query(BackendStatus).order_by(BackendStatus.timestamp.desc()).first()

        if status:
            return {
                'status': status.status,
                'timestamp': status.timestamp.isoformat(),
                'latency': status.latency,
                'error_rate': status.error_rate
            }
        else:
            return {'status': 'unknown', 'timestamp': None, 'latency': None, 'error_rate': None}
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error fetching latest backend status: {e}")
        return {'status': 'unknown', 'timestamp': None, 'latency': None, 'error_rate': None}
    finally:
        session.close()
```