"""
StockPulse AI v3.0 - Downloads API Routes
Blueprint for repository download statistics endpoints.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import sqlite3
import logging

from backend.config import Config
from backend.database import db_session

logger = logging.getLogger(__name__)

downloads_bp = Blueprint('downloads', __name__, url_prefix='/api/downloads')


@downloads_bp.route('/stats', methods=['GET'])
def get_download_stats():
    """Get the latest download statistics for the repository.
    
    Query Parameters
    ----------------
    repository : str, optional
        Repository identifier (e.g., 'amitpatole/stockpulse-ai').
        Defaults to 'amitpatole/stockpulse-ai'.
    limit : int, optional
        Number of recent records to return. Default: 30.
    
    Returns
    -------
    json
        {
            'success': bool,
            'repository': str,
            'latest': {
                'total_clones': int,
                'unique_clones': int,
                'recorded_at': str
            },
            'history': [
                {
                    'total_clones': int,
                    'unique_clones': int,
                    'recorded_at': str
                },
                ...
            ]
        }
    """
    repository = request.args.get('repository', 'amitpatole/stockpulse-ai')
    limit = int(request.args.get('limit', 30))
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Get latest stats
            cursor.execute(
                """
                SELECT total_clones, unique_clones, recorded_at
                FROM download_stats
                WHERE repository = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (repository,)
            )
            latest_row = cursor.fetchone()
            
            latest = None
            if latest_row:
                latest = {
                    'total_clones': latest_row['total_clones'],
                    'unique_clones': latest_row['unique_clones'],
                    'recorded_at': latest_row['recorded_at'],
                }
            
            # Get historical stats
            cursor.execute(
                """
                SELECT total_clones, unique_clones, recorded_at
                FROM download_stats
                WHERE repository = ?
                ORDER BY recorded_at DESC
                LIMIT ?
                """,
                (repository, limit)
            )
            history_rows = cursor.fetchall()
            
            history = [
                {
                    'total_clones': row['total_clones'],
                    'unique_clones': row['unique_clones'],
                    'recorded_at': row['recorded_at'],
                }
                for row in history_rows
            ]
            
            return jsonify({
                'success': True,
                'repository': repository,
                'latest': latest,
                'history': history,
            })
    except Exception as e:
        logger.error(f"Error fetching download stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@downloads_bp.route('/daily', methods=['GET'])
def get_daily_download_stats():
    """Get daily breakdown of download statistics.
    
    Query Parameters
    ----------------
    repository : str, optional
        Repository identifier (e.g., 'amitpatole/stockpulse-ai').
        Defaults to 'amitpatole/stockpulse-ai'.
    days : int, optional
        Number of days to return. Default: 14.
    
    Returns
    -------
    json
        {
            'success': bool,
            'repository': str,
            'days': [
                {
                    'date': str,
                    'clones': int,
                    'unique_clones': int,
                    'recorded_at': str
                },
                ...
            ]
        }
    """
    repository = request.args.get('repository', 'amitpatole/stockpulse-ai')
    days = int(request.args.get('days', 14))
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT date, clones, unique_clones, recorded_at
                FROM download_stats_daily
                WHERE repository = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (repository, days)
            )
            rows = cursor.fetchall()
            
            daily_stats = [
                {
                    'date': row['date'],
                    'clones': row['clones'],
                    'unique_clones': row['unique_clones'],
                    'recorded_at': row['recorded_at'],
                }
                for row in rows
            ]
            
            return jsonify({
                'success': True,
                'repository': repository,
                'days': daily_stats,
            })
    except Exception as e:
        logger.error(f"Error fetching daily download stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@downloads_bp.route('/summary', methods=['GET'])
def get_download_summary():
    """Get summary statistics for repository downloads.
    
    Query Parameters
    ----------------
    repository : str, optional
        Repository identifier (e.g., 'amitpatole/stockpulse-ai').
        Defaults to 'amitpatole/stockpulse-ai'.
    
    Returns
    -------
    json
        {
            'success': bool,
            'repository': str,
            'summary': {
                'total_clones_latest': int,
                'unique_clones_latest': int,
                'total_records': int,
                'earliest_record': str,
                'latest_record': str,
                'avg_daily_clones': float,
                'avg_unique_ratio': float
            }
        }
    """
    repository = request.args.get('repository', 'amitpatole/stockpulse-ai')
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Get latest stats
            cursor.execute(
                """
                SELECT total_clones, unique_clones, recorded_at
                FROM download_stats
                WHERE repository = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (repository,)
            )
            latest_row = cursor.fetchone()
            
            # Get aggregate stats
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    MIN(recorded_at) as earliest_record,
                    MAX(recorded_at) as latest_record
                FROM download_stats
                WHERE repository = ?
                """,
                (repository,)
            )
            agg_row = cursor.fetchone()
            
            # Calculate averages from daily data
            cursor.execute(
                """
                SELECT 
                    AVG(clones) as avg_daily_clones,
                    AVG(CAST(unique_clones AS REAL) / NULLIF(clones, 0)) as avg_unique_ratio
                FROM download_stats_daily
                WHERE repository = ? AND clones > 0
                """,
                (repository,)
            )
            avg_row = cursor.fetchone()
            
            summary = {
                'total_clones_latest': latest_row['total_clones'] if latest_row else 0,
                'unique_clones_latest': latest_row['unique_clones'] if latest_row else 0,
                'total_records': agg_row['total_records'] if agg_row else 0,
                'earliest_record': agg_row['earliest_record'] if agg_row else None,
                'latest_record': agg_row['latest_record'] if agg_row else None,
                'avg_daily_clones': round(avg_row['avg_daily_clones'], 2) if avg_row and avg_row['avg_daily_clones'] else 0,
                'avg_unique_ratio': round(avg_row['avg_unique_ratio'] * 100, 1) if avg_row and avg_row['avg_unique_ratio'] else 0,
            }
            
            return jsonify({
                'success': True,
                'repository': repository,
                'summary': summary,
            })
    except Exception as e:
        logger.error(f"Error fetching download summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
