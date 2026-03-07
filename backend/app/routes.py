from typing import Any
from flask import Flask, jsonify, request
import sqlite3
from sqlite3 import Error
from contextlib import asynccontextmanager
from config import DATABASE_PATH

app = Flask(__name__)

@asynccontextmanager
async def get_db_connection():
    conn = await sqlite3.connect(DATABASE_PATH, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        await conn.close()

@app.route('/stock/<stock_symbol>/sentiment', methods=['GET'])
async def get_stock_sentiment(stock_symbol: str) -> Any:
    async with get_db_connection() as conn:
        cursor = await conn.cursor()
        try:
            sentiment_data = await cursor.execute(
                "SELECT * FROM stock_sentiment WHERE stock_symbol = ? ORDER BY timestamp DESC LIMIT 10",
                (stock_symbol,)
            ).fetchall()
            return jsonify([dict(row) for row in sentiment_data])
        except Error as e:
            logging.error(f"Database error: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/stock/<stock_symbol>/trending_mentions', methods=['GET'])
async def get_trending_mentions(stock_symbol: str) -> Any:
    async with get_db_connection() as conn:
        cursor = await conn.cursor()
        try:
            mentions_data = await cursor.execute(
                "SELECT * FROM trending_mentions WHERE stock_symbol = ? ORDER BY timestamp DESC LIMIT 10",
                (stock_symbol,)
            ).fetchall()
            return jsonify([dict(row) for row in mentions_data])
        except Error as e:
            logging.error(f"Database error: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/stock/<stock_symbol>/sentiment_chart', methods=['GET'])
async def get_sentiment_chart(stock_symbol: str) -> Any:
    async with get_db_connection() as conn:
        cursor = await conn.cursor()
        try:
            chart_data = await cursor.execute(
                "SELECT timestamp, sentiment_score FROM stock_sentiment WHERE stock_symbol = ? ORDER BY timestamp ASC",
                (stock_symbol,)
            ).fetchall()
            return jsonify([dict(row) for row in chart_data])
        except Error as e:
            logging.error(f"Database error: {e}")
            return jsonify({"error": str(e)}), 500