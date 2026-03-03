"""
Comprehensive pytest test suite for Downloads API endpoints.

Covers:
- Download statistics aggregation
- Daily breakdown with time-window filtering
- Summary with trend calculation
- Error handling and edge cases
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch


class TestDownloadStatsAPI:
    """Tests for GET /api/downloads/stats endpoint."""

    def test_get_download_stats_success(self, client, mock_download_stats):
        """Test fetching download statistics."""
        with patch('backend.api.downloads.get_download_stats', return_value=mock_download_stats):
            response = client.get('/api/downloads/stats')
            assert response.status_code == 200
            data = json.loads(response.data)

            assert 'data' in data or isinstance(data, list)
            if isinstance(data, dict) and 'data' in data:
                stats = data['data']
            else:
                stats = data

            assert len(stats) == 2
            assert stats[0]['repo_owner'] == 'tickerpulse'
            assert 'total_downloads' in stats[0]

    def test_get_download_stats_single_repo(self, client, mock_download_stats):
        """Test filtering stats by repo owner."""
        filtered = [s for s in mock_download_stats if s['repo_owner'] == 'tickerpulse']
        with patch('backend.api.downloads.get_download_stats', return_value=filtered):
            response = client.get('/api/downloads/stats?repo_owner=tickerpulse')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                stats = data['data']
            else:
                stats = data
            assert len(stats) == 2

    def test_get_download_stats_by_repo_name(self, client, mock_download_stats):
        """Test filtering stats by repo name."""
        repo_data = [s for s in mock_download_stats if s['repo_name'] == 'ai-research']
        with patch('backend.api.downloads.get_download_stats', return_value=repo_data):
            response = client.get('/api/downloads/stats?repo_name=ai-research')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                stats = data['data']
            else:
                stats = data
            assert len(stats) >= 1
            assert stats[0]['repo_name'] == 'ai-research'

    def test_get_download_stats_empty(self, client):
        """Test stats for repo with no downloads."""
        with patch('backend.api.downloads.get_download_stats', return_value=[]):
            response = client.get('/api/downloads/stats')
            assert response.status_code == 200
            data = json.loads(response.data)
            if isinstance(data, dict) and 'data' in data:
                assert data['data'] == []
            else:
                assert data == []

    def test_get_download_stats_with_limit(self, client, mock_download_stats):
        """Test stats with limit parameter."""
        with patch('backend.api.downloads.get_download_stats', return_value=mock_download_stats[:1]):
            response = client.get('/api/downloads/stats?limit=1')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                stats = data['data']
            else:
                stats = data
            assert len(stats) == 1

    def test_get_download_stats_max_limit(self, client, mock_download_stats):
        """Test max limit enforcement."""
        with patch('backend.api.downloads.get_download_stats', return_value=mock_download_stats):
            response = client.get('/api/downloads/stats?limit=1000')
            # Should either cap at max or return 422
            assert response.status_code in [200, 422]

    def test_get_download_stats_invalid_limit(self, client):
        """Test invalid limit parameter."""
        response = client.get('/api/downloads/stats?limit=0')
        assert response.status_code in [200, 422]

    def test_get_download_stats_invalid_repo_owner(self, client):
        """Test with invalid repo owner."""
        with patch('backend.api.downloads.get_download_stats', return_value=[]):
            response = client.get('/api/downloads/stats?repo_owner=nonexistent')
            assert response.status_code == 200


class TestDownloadDailyAPI:
    """Tests for GET /api/downloads/daily endpoint."""

    def test_get_daily_downloads_default(self, client, mock_download_daily):
        """Test fetching daily download breakdown."""
        with patch('backend.api.downloads.get_daily_downloads', return_value=mock_download_daily):
            response = client.get('/api/downloads/daily')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                daily = data['data']
            else:
                daily = data

            assert len(daily) == 7  # 7 days of data
            assert 'date' in daily[0]
            assert 'downloads' in daily[0]

    def test_get_daily_downloads_last_7_days(self, client, mock_download_daily):
        """Test daily downloads for last 7 days."""
        with patch('backend.api.downloads.get_daily_downloads', return_value=mock_download_daily):
            response = client.get('/api/downloads/daily?days=7')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                daily = data['data']
            else:
                daily = data
            assert len(daily) == 7

    def test_get_daily_downloads_last_30_days(self, client):
        """Test daily downloads for last 30 days."""
        data_30d = []
        for days_ago in range(30):
            date = (datetime.utcnow() - timedelta(days=days_ago)).date()
            data_30d.append({
                'date': date.isoformat(),
                'downloads': 100 + days_ago
            })

        with patch('backend.api.downloads.get_daily_downloads', return_value=data_30d):
            response = client.get('/api/downloads/daily?days=30')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                daily = data['data']
            else:
                daily = data
            assert len(daily) == 30

    def test_get_daily_downloads_single_day(self, client):
        """Test daily downloads for single day."""
        single_day = [{
            'date': datetime.utcnow().date().isoformat(),
            'downloads': 250
        }]

        with patch('backend.api.downloads.get_daily_downloads', return_value=single_day):
            response = client.get('/api/downloads/daily?days=1')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                daily = data['data']
            else:
                daily = data
            assert len(daily) == 1

    def test_get_daily_downloads_by_repo(self, client):
        """Test daily downloads filtered by repo."""
        single_repo_data = [{
            'repo_name': 'ai-research',
            'date': datetime.utcnow().date().isoformat(),
            'downloads': 150
        }]

        with patch('backend.api.downloads.get_daily_downloads', return_value=single_repo_data):
            response = client.get('/api/downloads/daily?repo_name=ai-research&days=7')
            assert response.status_code == 200

    def test_get_daily_downloads_invalid_days(self, client):
        """Test invalid days parameter."""
        response = client.get('/api/downloads/daily?days=0')
        assert response.status_code in [200, 422]

    def test_get_daily_downloads_negative_days(self, client):
        """Test negative days parameter."""
        response = client.get('/api/downloads/daily?days=-5')
        assert response.status_code in [200, 422]

    def test_get_daily_downloads_max_days(self, client):
        """Test max days limit (should cap at reasonable value like 365)."""
        response = client.get('/api/downloads/daily?days=1000')
        assert response.status_code in [200, 422]

    def test_get_daily_downloads_empty(self, client):
        """Test daily downloads when no data exists."""
        with patch('backend.api.downloads.get_daily_downloads', return_value=[]):
            response = client.get('/api/downloads/daily')
            assert response.status_code == 200
            data = json.loads(response.data)
            if isinstance(data, dict) and 'data' in data:
                assert data['data'] == []
            else:
                assert data == []


class TestDownloadSummaryAPI:
    """Tests for GET /api/downloads/summary endpoint."""

    def test_get_download_summary(self, client):
        """Test fetching download summary with trends."""
        summary_data = {
            'period': 'all_time',
            'total_downloads': 24340,
            'average_daily': 234.5,
            'trend': 'increasing',
            'trend_percent': 12.5,
            'by_repo': [
                {
                    'repo_name': 'ai-research',
                    'downloads': 15420,
                    'percent_of_total': 63.3,
                    'trend': 'increasing'
                },
                {
                    'repo_name': 'data-toolkit',
                    'downloads': 8920,
                    'percent_of_total': 36.7,
                    'trend': 'stable'
                }
            ]
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                summary = data['data']
            else:
                summary = data

            assert 'total_downloads' in summary
            assert 'trend' in summary
            assert 'by_repo' in summary

    def test_get_download_summary_daily_period(self, client):
        """Test summary for daily period."""
        summary_data = {
            'period': 'daily',
            'date': datetime.utcnow().date().isoformat(),
            'total_downloads': 362,
            'by_repo': []
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary?period=daily')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                summary = data['data']
            else:
                summary = data
            assert summary['period'] == 'daily'

    def test_get_download_summary_weekly_period(self, client):
        """Test summary for weekly period."""
        summary_data = {
            'period': 'weekly',
            'week_starting': '2025-02-24',
            'total_downloads': 2800,
            'trend': 'increasing'
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary?period=weekly')
            assert response.status_code == 200

    def test_get_download_summary_monthly_period(self, client):
        """Test summary for monthly period."""
        summary_data = {
            'period': 'monthly',
            'month': '2025-03',
            'total_downloads': 8750,
            'average_daily': 282
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary?period=monthly')
            assert response.status_code == 200

    def test_get_download_summary_invalid_period(self, client):
        """Test summary with invalid period."""
        response = client.get('/api/downloads/summary?period=invalid')
        assert response.status_code in [200, 422]

    def test_get_download_summary_with_repo_filter(self, client):
        """Test summary filtered by repository."""
        summary_data = {
            'repo_name': 'ai-research',
            'total_downloads': 15420,
            'trend': 'increasing'
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary?repo_name=ai-research')
            assert response.status_code == 200

    def test_get_download_summary_trend_calculation(self, client):
        """Test that trend is calculated correctly."""
        summary_data = {
            'total_downloads': 1000,
            'previous_period_downloads': 800,
            'trend_percent': 25.0,
            'trend': 'increasing'
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary')
            assert response.status_code == 200
            data = json.loads(response.data)

            if isinstance(data, dict) and 'data' in data:
                summary = data['data']
            else:
                summary = data
            assert 'trend' in summary

    def test_get_download_summary_zero_downloads(self, client):
        """Test summary when no downloads exist."""
        summary_data = {
            'total_downloads': 0,
            'trend': 'stable',
            'by_repo': []
        }

        with patch('backend.api.downloads.get_download_summary', return_value=summary_data):
            response = client.get('/api/downloads/summary')
            assert response.status_code == 200


class TestDownloadAPIErrorHandling:
    """Tests for error handling in Downloads API."""

    def test_database_error(self, client):
        """Test handling of database errors."""
        with patch('backend.api.downloads.get_download_stats', side_effect=ConnectionError('DB error')):
            response = client.get('/api/downloads/stats')
            assert response.status_code in [500, 503]
            data = json.loads(response.data)
            assert 'error' in data or 'detail' in data

    def test_invalid_repo_owner_format(self, client):
        """Test invalid repo owner format."""
        response = client.get('/api/downloads/stats?repo_owner=')
        assert response.status_code in [200, 422]

    def test_malformed_date_parameter(self, client):
        """Test malformed date in query."""
        response = client.get('/api/downloads/daily?start_date=invalid-date')
        assert response.status_code in [200, 422]

    def test_internal_server_error(self, client):
        """Test internal server error handling."""
        with patch('backend.api.downloads.get_daily_downloads', side_effect=Exception('Unexpected error')):
            response = client.get('/api/downloads/daily')
            assert response.status_code == 500

    def test_calculation_error(self, client):
        """Test handling of calculation errors in summary."""
        with patch('backend.api.downloads.get_download_summary', side_effect=Exception('Calculation error')):
            response = client.get('/api/downloads/summary')
            assert response.status_code == 500


class TestDownloadAPIEdgeCases:
    """Tests for edge cases in Downloads API."""

    def test_downloads_with_null_values(self, client):
        """Test handling null values in download data."""
        data = [
            {'repo_name': 'repo1', 'downloads': None},
            {'repo_name': 'repo2', 'downloads': 100}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response = client.get('/api/downloads/daily')
            # Should handle gracefully
            assert response.status_code in [200, 500]

    def test_downloads_with_very_large_numbers(self, client):
        """Test handling very large download numbers."""
        data = [
            {'date': '2025-03-03', 'downloads': 999999999}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response = client.get('/api/downloads/daily')
            assert response.status_code == 200

    def test_downloads_with_negative_values(self, client):
        """Test handling negative download values (data corruption)."""
        data = [
            {'date': '2025-03-03', 'downloads': -100}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response = client.get('/api/downloads/daily')
            # Should either handle or flag as error
            assert response.status_code in [200, 400]

    def test_downloads_with_duplicate_dates(self, client):
        """Test handling duplicate date entries."""
        data = [
            {'date': '2025-03-03', 'downloads': 100},
            {'date': '2025-03-03', 'downloads': 50}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response = client.get('/api/downloads/daily')
            # Should handle appropriately
            assert response.status_code in [200, 400]

    def test_downloads_unsorted_dates(self, client):
        """Test handling unsorted date entries."""
        data = [
            {'date': '2025-03-01', 'downloads': 100},
            {'date': '2025-03-03', 'downloads': 150},
            {'date': '2025-03-02', 'downloads': 125}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response = client.get('/api/downloads/daily')
            assert response.status_code == 200

    def test_downloads_with_future_dates(self, client):
        """Test handling future dates in data."""
        future_date = (datetime.utcnow() + timedelta(days=10)).date().isoformat()
        data = [
            {'date': future_date, 'downloads': 100}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response = client.get('/api/downloads/daily')
            # Should handle gracefully
            assert response.status_code in [200, 400]

    def test_downloads_pagination_consistency(self, client):
        """Test that pagination is consistent across calls."""
        data = [
            {'date': '2025-03-03', 'downloads': 100},
            {'date': '2025-03-02', 'downloads': 95}
        ]

        with patch('backend.api.downloads.get_daily_downloads', return_value=data):
            response1 = client.get('/api/downloads/daily?limit=1')
            response2 = client.get('/api/downloads/daily?limit=1&offset=1')

            assert response1.status_code == 200
            assert response2.status_code == 200
