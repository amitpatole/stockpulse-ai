```python
from typing import Any, Dict, List
import sqlite3
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///heatmap.db?mode=memory&cache=shared'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)

class Sector(db.Model):
    __tablename__ = 'sectors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    sector_id = db.Column(db.Integer, db.ForeignKey('sectors.id'), nullable=False)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

async def create_async_engine_and_sessionmaker():
    engine = create_async_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    sessionmaker_ = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return engine, sessionmaker_

async def get_sectors(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(select(Sector))
    return [dict(row._mapping) async for row in result]

async def get_stocks_by_sector(session: AsyncSession, sector_id: int) -> List[Dict[str, Any]]:
    result = await session.execute(select(Stock).where(Stock.sector_id == sector_id))
    return [dict(row._mapping) async for row in result]

@app.route('/heatmap', methods=['GET'])
async def heatmap():
    engine, sessionmaker_ = await create_async_engine_and_sessionmaker()
    async with sessionmaker_() as session:
        sectors = await get_sectors(session)
        sector_data = []
        for sector in sectors:
            sector_id = sector['id']
            stocks = await get_stocks_by_sector(session, sector_id)
            sector['stocks'] = stocks
            sector_data.append(sector)
    return jsonify(sector_data)

@app.route('/heatmap/<int:sector_id>', methods=['GET'])
async def heatmap_drill_down(sector_id: int):
    engine, sessionmaker_ = await create_async_engine_and_sessionmaker()
    async with sessionmaker_() as session:
        result = await session.execute(select(Sector).where(Sector.id == sector_id))
        sector = result.fetchone()
        if sector is None:
            return jsonify({'error': 'Sector not found'}), 404
        stocks = await get_stocks_by_sector(session, sector_id)
        return jsonify({'sector': sector._mapping, 'stocks': stocks})

if __name__ == '__main__':
    app.run(debug=True)
```