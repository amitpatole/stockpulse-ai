# Feature: Economic Calendar

## Overview
The Economic Calendar feature provides users with a curated feed of important economic events that impact market movements. Users can track upcoming economic releases (GDP, employment data, inflation, interest rate decisions), see historical releases with their actual impact on markets, and filter by country or economic category. Impact ratings help prioritize which events matter most for trading decisions.

## Data Model

### Database Tables

#### `economic_events`
Core table tracking economic releases:
- `id` (INTEGER PRIMARY KEY): Event identifier
- `event_name` (TEXT NOT NULL): Name of the economic indicator (e.g., "Non-Farm Payroll", "CPI")
- `country` (TEXT NOT NULL): Country code (e.g., "US", "EU", "UK")
- `category` (TEXT NOT NULL): Economic category (employment, inflation, gdp, interest_rates, housing, consumer)
- `scheduled_datetime` (DATETIME NOT NULL): Scheduled release time (UTC)
- `actual_datetime` (DATETIME): When the event actually occurred (if released)
- `impact_level` (TEXT NOT NULL): Severity rating ("low", "medium", "high")
- `forecast_value` (TEXT): Expected value for the release
- `actual_value` (TEXT): Actual reported value
- `previous_value` (TEXT): Previously reported value for this indicator
- `source` (TEXT): Data provider (e.g., "fred", "investing.com", "tradingeconomics")
- `external_id` (TEXT UNIQUE): Provider's unique identifier
- `is_released` (BOOLEAN DEFAULT 0): Whether the actual value has been published
- `created_at` (DATETIME DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (DATETIME DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `(country, category)` - for filtering events
- `(scheduled_datetime)` - for chronological queries
- `(is_released)` - to find upcoming vs. released events
- `(external_id)` - for deduplication

#### `economic_event_impacts`
Historical impact analysis:
- `id` (INTEGER PRIMARY KEY): Record identifier
- `event_id` (INTEGER NOT NULL FOREIGN KEY → economic_events.id ON DELETE CASCADE)
- `market_volatility_change` (REAL): Change in volatility (%) on release day
- `sp500_price_impact` (REAL): S&P 500 movement (%) following event
- `vix_change` (REAL): VIX change (%) following event
- `fx_impact_magnitude` (REAL): Average currency pair movement (pips)
- `impact_score` (REAL): Normalized score 0-100 indicating historical market impact
- `analysis_timestamp` (DATETIME DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `(event_id)` - for impact lookup
- `(impact_score)` - for sorting by significance

#### `economic_calendar_preferences`
User subscription preferences:
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER NOT NULL FOREIGN KEY → users.id ON DELETE CASCADE)
- `country_list` (TEXT): JSON array of countries to track (e.g., '["US", "EU"]')
- `category_list` (TEXT): JSON array of categories (e.g., '["employment", "inflation"]')
- `min_impact_level` (TEXT): Minimum impact to show ("low", "medium", "high")
- `alert_enabled` (BOOLEAN DEFAULT 1): Receive alerts for upcoming events
- `alert_hours_before` (INTEGER DEFAULT 24): Alert N hours before release
- `created_at` (DATETIME DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (DATETIME DEFAULT CURRENT_TIMESTAMP)

**Unique Constraint:** `(user_id)` - one preference set per user

### Sample Data
```json
{
  "event": {
    "id": 1,
    "event_name": "Non-Farm Payroll",
    "country": "US",
    "category": "employment",
    "scheduled_datetime": "2026-03-06T13:30:00Z",
    "impact_level": "high",
    "forecast_value": "250k",
    "actual_value": "275k",
    "previous_value": "272k",
    "source": "fred",
    "is_released": true
  },
  "impact": {
    "event_id": 1,
    "market_volatility_change": 8.5,
    "sp500_price_impact": 1.2,
    "vix_change": 15.3,
    "impact_score": 78.5
  }
}
```

## API Endpoints

### GET /api/economic-calendar/upcoming
Fetch upcoming economic events with optional filtering.

**Query Parameters:**
- `country` (string, optional): Filter by country code (e.g., "US")
- `category` (string, optional): Filter by category
- `min_impact` (string, optional): Minimum impact level ("low", "medium", "high")
- `days_ahead` (integer, optional, default=30): Look ahead N days from today
- `limit` (integer, optional, default=50): Max events to return [1-100]
- `offset` (integer, optional, default=0): Pagination offset

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "event_name": "Non-Farm Payroll",
      "country": "US",
      "category": "employment",
      "scheduled_datetime": "2026-03-06T13:30:00Z",
      "impact_level": "high",
      "forecast_value": "250k",
      "previous_value": "272k",
      "is_released": false,
      "source": "fred"
    }
  ],
  "meta": {
    "total_count": 150,
    "limit": 50,
    "offset": 0,
    "has_next": true,
    "countries": ["US", "EU", "UK"],
    "categories": ["employment", "inflation", "gdp"]
  },
  "errors": null
}
```

**Error Cases:**
- 400: Invalid country code, category, min_impact value, or limit > 100
- 401: Unauthorized (no authentication token)

### GET /api/economic-calendar/history
Fetch historical economic events with impact analysis.

**Query Parameters:**
- `country` (string, optional): Filter by country
- `category` (string, optional): Filter by category
- `days_back` (integer, optional, default=90): Look back N days
- `min_impact_score` (integer, optional, default=0): Filter by impact [0-100]
- `limit` (integer, optional, default=50): Max results [1-100]
- `offset` (integer, optional, default=0): Pagination offset

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "event_name": "Non-Farm Payroll",
      "country": "US",
      "category": "employment",
      "actual_datetime": "2026-02-06T13:30:00Z",
      "actual_value": "275k",
      "previous_value": "272k",
      "impact": {
        "impact_score": 78.5,
        "market_volatility_change": 8.5,
        "sp500_price_impact": 1.2,
        "vix_change": 15.3
      }
    }
  ],
  "meta": {
    "total_count": 250,
    "limit": 50,
    "offset": 0,
    "has_next": true,
    "avg_impact_score": 62.3
  },
  "errors": null
}
```

### GET /api/economic-calendar/{event_id}
Fetch detailed information about a specific economic event.

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "event_name": "Non-Farm Payroll",
    "country": "US",
    "category": "employment",
    "scheduled_datetime": "2026-03-06T13:30:00Z",
    "actual_datetime": "2026-03-06T13:30:00Z",
    "impact_level": "high",
    "forecast_value": "250k",
    "actual_value": "275k",
    "previous_value": "272k",
    "source": "fred",
    "is_released": true,
    "impact": {
      "impact_score": 78.5,
      "market_volatility_change": 8.5,
      "sp500_price_impact": 1.2,
      "vix_change": 15.3
    },
    "related_events": [
      {"id": 5, "event_name": "Unemployment Rate", "country": "US", "scheduled_datetime": "2026-03-06T13:30:00Z"}
    ]
  },
  "meta": null,
  "errors": null
}
```

**Error Cases:**
- 404: Event not found

### POST /api/economic-calendar/preferences
Save user's calendar preferences and alert settings.

**Request Body:**
```json
{
  "country_list": ["US", "EU"],
  "category_list": ["employment", "inflation"],
  "min_impact_level": "medium",
  "alert_enabled": true,
  "alert_hours_before": 24
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "user_id": 123,
    "country_list": ["US", "EU"],
    "category_list": ["employment", "inflation"],
    "min_impact_level": "medium",
    "alert_enabled": true,
    "alert_hours_before": 24
  },
  "meta": null,
  "errors": null
}
```

**Error Cases:**
- 400: Invalid country_list, category_list, min_impact_level, or alert_hours_before
- 401: Unauthorized
- 409: Invalid combination (empty lists or invalid values)

### GET /api/economic-calendar/preferences
Fetch user's current calendar preferences.

**Response (200 OK):** Same as POST response above
**Error Cases:**
- 401: Unauthorized
- 404: No preferences found (return defaults)

### GET /api/economic-calendar/impact-analysis
Analyze impact of events on specific tickers or markets.

**Query Parameters:**
- `event_ids` (string, required): Comma-separated event IDs
- `tickers` (string, optional): Comma-separated ticker symbols to analyze impact on

**Response (200 OK):**
```json
{
  "data": {
    "events_analyzed": 5,
    "avg_impact_score": 72.3,
    "affected_tickers": {
      "SPY": {
        "avg_price_impact": 0.85,
        "total_volatility_increase": 6.2,
        "events_impacted": 5
      },
      "GLD": {
        "avg_price_impact": -0.32,
        "total_volatility_increase": 4.1,
        "events_impacted": 3
      }
    }
  },
  "meta": null,
  "errors": null
}
```

## Dashboard/UI Elements

### Pages
- `/dashboard/economic-calendar` - Main calendar view
- `/dashboard/economic-calendar/history` - Historical events
- `/dashboard/economic-calendar/settings` - User preferences

### Components
- **EconomicCalendarWidget** - Dashboard widget showing next 5 upcoming events
- **CalendarView** - Full calendar of upcoming events
- **EventCard** - Individual event with details and impact rating
- **ImpactBadge** - Visual indicator for impact level (low=green, medium=yellow, high=red)
- **HistoricalChart** - Line chart showing historical event impact over time
- **EventFilter** - Dropdown/chip selector for country and category filtering
- **PreferencesForm** - Settings for alert configuration and event subscriptions

### Dashboard Widget (Calendar Tab)
- Shows next 5 high-impact events
- One-click access to full calendar
- Color-coded by impact level
- Time remaining countdown

## Business Rules
- **Impact Levels:** Events are rated as low/medium/high based on historical market volatility
- **Upcoming vs. Released:** Events are filtered by `is_released` flag; released events move to history
- **Data Freshness:** Calendar data is refreshed daily from external sources; events older than 6 months are archived
- **Duplicates:** External IDs prevent duplicate imports from different providers
- **User Preferences:** Each user can customize which countries/categories they monitor
- **Impact Calculation:** Historical impact scores are normalized 0-100 based on volatility_change, price_impact, and VIX correlation
- **Timezone Handling:** All event times stored in UTC; displayed in user's local timezone
- **Cascading Deletes:** Deleting an economic event cascades to delete its impact records and user preferences related to it
- **Rate Limiting:** External API calls to fetch calendar data limited to 1 request per hour per source

## Edge Cases
- **No events available:** Return empty array with metadata showing no upcoming events
- **Events with missing values:** forecast_value and actual_value can be null for some events
- **Concurrent updates:** Multiple sources updating same event - use ON CONFLICT REPLACE to ensure consistency
- **Historical impact not yet calculated:** Events released but not yet analyzed return empty impact object
- **Timezone edge cases:** Events scheduled at market open/close may affect neighboring days' analysis
- **User has no preferences set:** Return sensible defaults (all countries, all categories, min_impact="low")

## Security
- **Authentication:** All endpoints require valid API token (same as other TickerPulse endpoints)
- **Data Validation:** All inputs validated against allowed values (country codes, impact levels, category names)
- **Rate Limiting:** Per-user limit of 100 requests/hour to calendar endpoints
- **SQL Injection Prevention:** All database queries use parameterized statements
- **No Sensitive Data:** Events contain only public economic data; no user PII mixed in response

## Testing

### Unit Tests
- **EventManager.fetch_upcoming():** Returns only unreleased events, respects filters, validates parameters
- **EventManager.fetch_history():** Returns released events, impact scores calculated correctly
- **ImpactAnalyzer.calculate_impact_score():** Score normalized 0-100, accounts for volatility/price/vix
- **PreferencesManager:** Create/update/fetch preferences, handle defaults, validate inputs

### E2E Tests
- **User views upcoming events:** Calendar loads, events displayed, filterable
- **User subscribes to event alerts:** Preferences saved, correct events shown after filtering
- **User analyzes historical impact:** History page loads, chart displays impact trends
- **Real-time event release:** Released events move from upcoming to history automatically

## Changes & Deprecations
- **v1.0 (2026-03-02):** Initial implementation with upcoming events, historical analysis, and user preferences

---

--- FILE: backend/migrations/0044_economic_calendar.py ---
"""
Migration 0044: Add Economic Calendar tables (economic_events, economic_event_impacts, economic_calendar_preferences)
Created: 2026-03-02
"""

def up(conn):
    """Create economic calendar tables."""
    cursor = conn.cursor()
    
    # economic_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS economic_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            country TEXT NOT NULL,
            category TEXT NOT NULL,
            scheduled_datetime DATETIME NOT NULL,
            actual_datetime DATETIME,
            impact_level TEXT NOT NULL CHECK(impact_level IN ('low', 'medium', 'high')),
            forecast_value TEXT,
            actual_value TEXT,
            previous_value TEXT,
            source TEXT,
            external_id TEXT UNIQUE,
            is_released INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_events_country_category ON economic_events(country, category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_events_scheduled ON economic_events(scheduled_datetime)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_events_released ON economic_events(is_released)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_events_external_id ON economic_events(external_id)")
    
    # economic_event_impacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS economic_event_impacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            market_volatility_change REAL,
            sp500_price_impact REAL,
            vix_change REAL,
            fx_impact_magnitude REAL,
            impact_score REAL,
            analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES economic_events(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_impacts_event_id ON economic_event_impacts(event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_impacts_score ON economic_event_impacts(impact_score)")
    
    # economic_calendar_preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS economic_calendar_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            country_list TEXT,
            category_list TEXT,
            min_impact_level TEXT DEFAULT 'low',
            alert_enabled INTEGER DEFAULT 1,
            alert_hours_before INTEGER DEFAULT 24,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_econ_prefs_user_id ON economic_calendar_preferences(user_id)")
    
    conn.commit()


def down(conn):
    """Drop economic calendar tables (rollback)."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS economic_calendar_preferences")
    cursor.execute("DROP TABLE IF EXISTS economic_event_impacts")
    cursor.execute("DROP TABLE IF EXISTS economic_events")
    conn.commit()
---

--- FILE: backend/managers/economic_calendar_manager.py ---
"""
TickerPulse AI - Economic Calendar Manager
Handles fetching, storing, and analyzing economic events.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from backend.database import db_session

logger = logging.getLogger(__name__)


@dataclass
class EconomicEvent:
    """Economic event data."""
    id: Optional[int]
    event_name: str
    country: str
    category: str
    scheduled_datetime: str
    impact_level: str
    forecast_value: Optional[str] = None
    actual_value: Optional[str] = None
    previous_value: Optional[str] = None
    source: Optional[str] = None
    actual_datetime: Optional[str] = None
    is_released: bool = False
    external_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event_name': self.event_name,
            'country': self.country,
            'category': self.category,
            'scheduled_datetime': self.scheduled_datetime,
            'actual_datetime': self.actual_datetime,
            'impact_level': self.impact_level,
            'forecast_value': self.forecast_value,
            'actual_value': self.actual_value,
            'previous_value': self.previous_value,
            'source': self.source,
            'is_released': self.is_released,
            'external_id': self.external_id,
        }


@dataclass
class EventImpact:
    """Historical event impact data."""
    event_id: int
    impact_score: Optional[float] = None
    market_volatility_change: Optional[float] = None
    sp500_price_impact: Optional[float] = None
    vix_change: Optional[float] = None
    fx_impact_magnitude: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'impact_score': self.impact_score,
            'market_volatility_change': self.market_volatility_change,
            'sp500_price_impact': self.sp500_price_impact,
            'vix_change': self.vix_change,
            'fx_impact_magnitude': self.fx_impact_magnitude,
        }


class EconomicCalendarManager:
    """Manages economic event data and impact analysis."""
    
    VALID_IMPACT_LEVELS = {'low', 'medium', 'high'}
    VALID_CATEGORIES = {'employment', 'inflation', 'gdp', 'interest_rates', 'housing', 'consumer'}
    DEFAULT_LOOK_AHEAD_DAYS = 30
    DEFAULT_LOOK_BACK_DAYS = 90
    
    @staticmethod
    def fetch_upcoming_events(
        country: Optional[str] = None,
        category: Optional[str] = None,
        min_impact: Optional[str] = None,
        days_ahead: int = DEFAULT_LOOK_AHEAD_DAYS,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[EconomicEvent], int]:
        """
        Fetch upcoming (unreleased) economic events.
        
        Returns:
            Tuple of (events list, total_count)
        
        Raises:
            ValueError: On invalid parameters
        """
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if days_ahead < 1:
            raise ValueError("days_ahead must be >= 1")
        if min_impact and min_impact not in EconomicCalendarManager.VALID_IMPACT_LEVELS:
            raise ValueError(f"min_impact must be one of {EconomicCalendarManager.VALID_IMPACT_LEVELS}")
        if country and not isinstance(country, str) or (country and len(country) > 5):
            raise ValueError("country must be a valid code (max 5 chars)")
        if category and category not in EconomicCalendarManager.VALID_CATEGORIES:
            raise ValueError(f"category must be one of {EconomicCalendarManager.VALID_CATEGORIES}")
        
        future_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM economic_events WHERE is_released = 0 AND scheduled_datetime <= ?"
            params = [future_date]
            
            if country:
                query += " AND country = ?"
                params.append(country)
            if category:
                query += " AND category = ?"
                params.append(category)
            if min_impact:
                # Map impact level to priority: low < medium < high
                impact_order = {'low': 0, 'medium': 1, 'high': 2}
                min_priority = impact_order[min_impact]
                impact_levels = [k for k, v in impact_order.items() if v >= min_priority]
                placeholders = ','.join(['?' for _ in impact_levels])
                query += f" AND impact_level IN ({placeholders})"
                params.extend(impact_levels)
            
            # Get total count
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated results
            query += " ORDER BY scheduled_datetime ASC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
        
        events = [_row_to_event(row) for row in rows]
        return events, total_count
    
    @staticmethod
    def fetch_history(
        country: Optional[str] = None,
        category: Optional[str] = None,
        days_back: int = DEFAULT_LOOK_BACK_DAYS,
        min_impact_score: float = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int, float]:
        """
        Fetch historical (released) economic events with impact data.
        
        Returns:
            Tuple of (events list with impacts, total_count, average_impact_score)
        
        Raises:
            ValueError: On invalid parameters
        """
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if days_back < 1:
            raise ValueError("days_back must be >= 1")
        if not 0 <= min_impact_score <= 100:
            raise ValueError("min_impact_score must be between 0 and 100")
        
        past_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Build query with impact data
            query = """
                SELECT 
                    e.*,
                    COALESCE(ei.impact_score, 0) as impact_score,
                    ei.market_volatility_change,
                    ei.sp500_price_impact,
                    ei.vix_change,
                    ei.fx_impact_magnitude
                FROM economic_events e
                LEFT JOIN economic_event_impacts ei ON e.id = ei.event_id
                WHERE e.is_released = 1 AND e.actual_datetime >= ?
            """
            params = [past_date]
            
            if country:
                query += " AND e.country = ?"
                params.append(country)
            if category:
                query += " AND e.category = ?"
                params.append(category)
            
            query += " AND COALESCE(ei.impact_score, 0) >= ?"
            params.append(min_impact_score)
            
            # Get total count
            count_query = query.replace("SELECT", "SELECT COUNT(*)")
            count_query = count_query.split("FROM")[0] + "FROM " + count_query.split("FROM")[1]
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get average impact
            avg_query = "SELECT AVG(COALESCE(ei.impact_score, 0)) FROM economic_events e LEFT JOIN economic_event_impacts ei ON e.id = ei.event_id WHERE e.is_released = 1"
            cursor.execute(avg_query)
            avg_score = cursor.fetchone()[0] or 0.0
            
            # Get paginated results
            query += " ORDER BY e.actual_datetime DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
        
        events = []
        for row in rows:
            event = _row_to_event(row)
            impact = EventImpact(
                event_id=event.id,
                impact_score=row['impact_score'],
                market_volatility_change=row['market_volatility_change'],
                sp500_price_impact=row['sp500_price_impact'],
                vix_change=row['vix_change'],
                fx_impact_magnitude=row['fx_impact_magnitude'],
            )
            events.append({
                'event': event.to_dict(),
                'impact': impact.to_dict(),
            })
        
        return events, total_count, avg_score
    
    @staticmethod
    def get_event_detail(event_id: int) -> Dict[str, Any]:
        """Fetch detailed event information with impact and related events."""
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Get event with impact
            cursor.execute("""
                SELECT 
                    e.*,
                    COALESCE(ei.impact_score, 0) as impact_score,
                    ei.market_volatility_change,
                    ei.sp500_price_impact,
                    ei.vix_change,
                    ei.fx_impact_magnitude
                FROM economic_events e
                LEFT JOIN economic_event_impacts ei ON e.id = ei.event_id
                WHERE e.id = ?
            """, (event_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            event = _row_to_event(row)
            impact = EventImpact(
                event_id=event.id,
                impact_score=row['impact_score'],
                market_volatility_change=row['market_volatility_change'],
                sp500_price_impact=row['sp500_price_impact'],
                vix_change=row['vix_change'],
                fx_impact_magnitude=row['fx_impact_magnitude'],
            )
            
            # Get related events (same country and category, within 7 days)
            cursor.execute("""
                SELECT * FROM economic_events 
                WHERE country = ? AND category = ? AND id != ?
                AND ABS(julianday(scheduled_datetime) - julianday(?)) <= 7
                ORDER BY scheduled_datetime ASC
                LIMIT 5
            """, (event.country, event.category, event_id, event.scheduled_datetime))
            
            related = [_row_to_event(r) for r in cursor.fetchall()]
            
            return {
                'event': event.to_dict(),
                'impact': impact.to_dict() if impact.impact_score else None,
                'related_events': [e.to_dict() for e in related],
            }
    
    @staticmethod
    def upsert_event(event: EconomicEvent) -> int:
        """Insert or update an economic event. Returns event ID."""
        with db_session() as conn:
            cursor = conn.cursor()
            
            if event.external_id:
                # Try to find existing event
                cursor.execute("SELECT id FROM economic_events WHERE external_id = ?", (event.external_id,))
                existing = cursor.fetchone()
                
                if existing:
                    event_id = existing[0]
                    cursor.execute("""
                        UPDATE economic_events SET
                            event_name=?, country=?, category=?, scheduled_datetime=?,
                            actual_datetime=?, impact_level=?, forecast_value=?,
                            actual_value=?, previous_value=?, source=?, is_released=?,
                            updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, (
                        event.event_name, event.country, event.category, event.scheduled_datetime,
                        event.actual_datetime, event.impact_level, event.forecast_value,
                        event.actual_value, event.previous_value, event.source, 
                        int(event.is_released), event_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO economic_events
                        (event_name, country, category, scheduled_datetime, actual_datetime,
                         impact_level, forecast_value, actual_value, previous_value,
                         source, external_id, is_released)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_name, event.country, event.category, event.scheduled_datetime,
                        event.actual_datetime, event.impact_level, event.forecast_value,
                        event.actual_value, event.previous_value, event.source,
                        event.external_id, int(event.is_released)
                    ))
                    event_id = cursor.lastrowid
            else:
                # No external_id, just insert
                cursor.execute("""
                    INSERT INTO economic_events
                    (event_name, country, category, scheduled_datetime, actual_datetime,
                     impact_level, forecast_value, actual_value, previous_value,
                     source, is_released)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_name, event.country, event.category, event.scheduled_datetime,
                    event.actual_datetime, event.impact_level, event.forecast_value,
                    event.actual_value, event.previous_value, event.source,
                    int(event.is_released)
                ))
                event_id = cursor.lastrowid
            
            conn.commit()
            return event_id
    
    @staticmethod
    def record_event_impact(impact: EventImpact) -> None:
        """Record or update the calculated impact for an event."""
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Check if impact already exists
            cursor.execute("SELECT id FROM economic_event_impacts WHERE event_id = ?", (impact.event_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE economic_event_impacts SET
                        market_volatility_change=?, sp500_price_impact=?, vix_change=?,
                        fx_impact_magnitude=?, impact_score=?, analysis_timestamp=CURRENT_TIMESTAMP
                    WHERE event_id=?
                """, (
                    impact.market_volatility_change, impact.sp500_price_impact,
                    impact.vix_change, impact.fx_impact_magnitude, impact.impact_score,
                    impact.event_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO economic_event_impacts
                    (event_id, market_volatility_change, sp500_price_impact, vix_change,
                     fx_impact_magnitude, impact_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    impact.event_id, impact.market_volatility_change, impact.sp500_price_impact,
                    impact.vix_change, impact.fx_impact_magnitude, impact.impact_score
                ))
            
            conn.commit()


class PreferencesManager:
    """Manage user economic calendar preferences."""
    
    @staticmethod
    def get_preferences(user_id: int) -> Dict[str, Any]:
        """Get user preferences or return defaults if not found."""
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM economic_calendar_preferences WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return {
                    'user_id': user_id,
                    'country_list': [],
                    'category_list': [],
                    'min_impact_level': 'low',
                    'alert_enabled': True,
                    'alert_hours_before': 24,
                }
            
            return {
                'id': row['id'],
                'user_id': row['user_id'],
                'country_list': json.loads(row['country_list']) if row['country_list'] else [],
                'category_list': json.loads(row['category_list']) if row['category_list'] else [],
                'min_impact_level': row['min_impact_level'],
                'alert_enabled': bool(row['alert_enabled']),
                'alert_hours_before': row['alert_hours_before'],
            }
    
    @staticmethod
    def save_preferences(
        user_id: int,
        country_list: List[str],
        category_list: List[str],
        min_impact_level: str = 'low',
        alert_enabled: bool = True,
        alert_hours_before: int = 24,
    ) -> Dict[str, Any]:
        """Save or update user preferences."""
        # Validate
        if not isinstance(country_list, list) or not all(isinstance(c, str) for c in country_list):
            raise ValueError("country_list must be a list of strings")
        if not isinstance(category_list, list) or not all(isinstance(c, str) for c in category_list):
            raise ValueError("category_list must be a list of strings")
        if min_impact_level not in {'low', 'medium', 'high'}:
            raise ValueError("min_impact_level must be one of: low, medium, high")
        if alert_hours_before < 1 or alert_hours_before > 168:
            raise ValueError("alert_hours_before must be between 1 and 168")
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO economic_calendar_preferences
                (user_id, country_list, category_list, min_impact_level, alert_enabled, alert_hours_before)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    country_list=?, category_list=?, min_impact_level=?,
                    alert_enabled=?, alert_hours_before=?, updated_at=CURRENT_TIMESTAMP
            """, (
                user_id, json.dumps(country_list), json.dumps(category_list),
                min_impact_level, int(alert_enabled), alert_hours_before,
                json.dumps(country_list), json.dumps(category_list),
                min_impact_level, int(alert_enabled), alert_hours_before
            ))
            
            conn.commit()
        
        return PreferencesManager.get_preferences(user_id)


def _row_to_event(row) -> EconomicEvent:
    """Convert database row to EconomicEvent."""
    return EconomicEvent(
        id=row['id'],
        event_name=row['event_name'],
        country=row['country'],
        category=row['category'],
        scheduled_datetime=row['scheduled_datetime'],
        actual_datetime=row['actual_datetime'],
        impact_level=row['impact_level'],
        forecast_value=row['forecast_value'],
        actual_value=row['actual_value'],
        previous_value=row['previous_value'],
        source=row['source'],
        external_id=row['external_id'],
        is_released=bool(row['is_released']),
    )
---

--- FILE: backend/api/economic_calendar.py ---
"""
TickerPulse AI - Economic Calendar API
FastAPI/Flask blueprint for economic events and impact analysis.
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from backend.managers.economic_calendar_manager import (
    EconomicCalendarManager, PreferencesManager, EconomicEvent, EventImpact
)
from backend.utils.decorators import login_required, jsonify_response

logger = logging.getLogger(__name__)

bp = Blueprint('economic_calendar', __name__, url_prefix='/api/economic-calendar')


@bp.route('/upcoming', methods=['GET'])
@login_required
@jsonify_response
def get_upcoming_events():
    """Fetch upcoming economic events."""
    try:
        country = request.args.get('country', None)
        category = request.args.get('category', None)
        min_impact = request.args.get('min_impact', None)
        days_ahead = int(request.args.get('days_ahead', 30))
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        events, total_count = EconomicCalendarManager.fetch_upcoming_events(
            country=country,
            category=category,
            min_impact=min_impact,
            days_ahead=days_ahead,
            limit=limit,
            offset=offset,
        )
        
        return {
            'data': [e.to_dict() for e in events],
            'meta': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': (offset + limit) < total_count,
            }
        }, 200
    
    except ValueError as e:
        return {'errors': str(e)}, 400
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {e}", exc_info=True)
        return {'errors': 'Internal server error'}, 500


@bp.route('/history', methods=['GET'])
@login_required
@jsonify_response
def get_history():
    """Fetch historical economic events with impact data."""
    try:
        country = request.args.get('country', None)
        category = request.args.get('category', None)
        days_back = int(request.args.get('days_back', 90))
        min_impact_score = float(request.args.get('min_impact_score', 0))
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        events, total_count, avg_score = EconomicCalendarManager.fetch_history(
            country=country,
            category=category,
            days_back=days_back,
            min_impact_score=min_impact_score,
            limit=limit,
            offset=offset,
        )
        
        return {
            'data': events,
            'meta': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': (offset + limit) < total_count,
                'avg_impact_score': avg_score,
            }
        }, 200
    
    except ValueError as e:
        return {'errors': str(e)}, 400
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        return {'errors': 'Internal server error'}, 500


@bp.route('/<int:event_id>', methods=['GET'])
@login_required
@jsonify_response
def get_event_detail(event_id):
    """Fetch detailed information about a specific event."""
    try:
        detail = EconomicCalendarManager.get_event_detail(event_id)
        if not detail:
            return {'errors': 'Event not found'}, 404
        
        return {'data': detail}, 200
    
    except Exception as e:
        logger.error(f"Error fetching event detail: {e}", exc_info=True)
        return {'errors': 'Internal server error'}, 500


@bp.route('/preferences', methods=['GET'])
@login_required
@jsonify_response
def get_preferences():
    """Get user's calendar preferences."""
    try:
        from flask_login import current_user
        prefs = PreferencesManager.get_preferences(current_user.id)
        return {'data': prefs}, 200
    
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}", exc_info=True)
        return {'errors': 'Internal server error'}, 500


@bp.route('/preferences', methods=['POST'])
@login_required
@jsonify_response
def save_preferences():
    """Save user's calendar preferences."""
    try:
        from flask_login import current_user
        payload = request.json or {}
        
        country_list = payload.get('country_list', [])
        category_list = payload.get('category_list', [])
        min_impact_level = payload.get('min_impact_level', 'low')
        alert_enabled = payload.get('alert_enabled', True)
        alert_hours_before = payload.get('alert_hours_before', 24)
        
        prefs = PreferencesManager.save_preferences(
            user_id=current_user.id,
            country_list=country_list,
            category_list=category_list,
            min_impact_level=min_impact_level,
            alert_enabled=alert_enabled,
            alert_hours_before=alert_hours_before,
        )
        
        return {'data': prefs}, 200
    
    except ValueError as e:
        return {'errors': str(e)}, 400
    except Exception as e:
        logger.error(f"Error saving preferences: {e}", exc_info=True)
        return {'errors': 'Internal server error'}, 500


@bp.route('/impact-analysis', methods=['GET'])
@login_required
@jsonify_response
def impact_analysis():
    """Analyze impact of events on specific tickers or markets."""
    try:
        event_ids_str = request.args.get('event_ids', '')
        tickers_str = request.args.get('tickers', '')
        
        if not event_ids_str:
            return {'errors': 'event_ids parameter is required'}, 400
        
        try:
            event_ids = [int(eid.strip()) for eid in event_ids_str.split(',')]
        except ValueError:
            return {'errors': 'event_ids must be comma-separated integers'}, 400
        
        tickers = [t.strip().upper() for t in tickers_str.split(',')] if tickers_str else []
        
        # Fetch impact data for all events
        from backend.database import db_session
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.event_name, ei.impact_score,
                       ei.sp500_price_impact, ei.vix_change
                FROM economic_events e
                LEFT JOIN economic_event_impacts ei ON e.id = ei.event_id
                WHERE e.id IN ({})
            """.format(','.join('?' * len(event_ids))), event_ids)
            
            rows = cursor.fetchall()
        
        # Aggregate impact data
        total_events = len(rows)
        impacts = [row['impact_score'] or 0 for row in rows]
        avg_impact = sum(impacts) / len(impacts) if impacts else 0
        
        affected_tickers = {}
        if tickers and rows:
            # Simplified ticker impact analysis
            for ticker in tickers:
                price_impacts = [row['sp500_price_impact'] or 0 for row in rows if row['sp500_price_impact']]
                vix_impacts = [row['vix_change'] or 0 for row in rows if row['vix_change']]
                
                affected_tickers[ticker] = {
                    'avg_price_impact': sum(price_impacts) / len(price_impacts) if price_impacts else 0,
                    'total_volatility_increase': sum(vix_impacts) / len(vix_impacts) if vix_impacts else 0,
                    'events_impacted': len([r for r in rows if r['impact_score']]),
                }
        
        return {
            'data': {
                'events_analyzed': total_events,
                'avg_impact_score': avg_impact,
                'affected_tickers': affected_tickers,
            }
        }, 200
    
    except Exception as e:
        logger.error(f"Error analyzing impact: {e}", exc_info=True)
        return {'errors': 'Internal server error'}, 500


def register_blueprint(app):
    """Register the economic calendar blueprint with the Flask app."""
    app.register_blueprint(bp)
---

--- FILE: backend/tests/test_economic_calendar_manager.py ---
"""
Tests for economic calendar manager and preferences.
"""

import pytest
import json
from datetime import datetime, timedelta
from backend.managers.economic_calendar_manager import (
    EconomicCalendarManager, PreferencesManager, EconomicEvent, EventImpact
)
from backend.database import db_session


@pytest.fixture
def setup_event_data(test_db):
    """Setup test economic events."""
    with db_session(test_db) as conn:
        cursor = conn.cursor()
        
        # Create test events
        now = datetime.utcnow()
        future = (now + timedelta(days=7)).isoformat()
        past = (now - timedelta(days=7)).isoformat()
        
        cursor.execute("""
            INSERT INTO economic_events
            (event_name, country, category, scheduled_datetime, impact_level, 
             forecast_value, previous_value, source, external_id, is_released)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Non-Farm Payroll", "US", "employment", future, "high", "250k", "272k", "fred", "nfp_2026_03_06", 0))
        
        event1_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO economic_events
            (event_name, country, category, scheduled_datetime, actual_datetime,
             impact_level, forecast_value, actual_value, previous_value, source, 
             external_id, is_released)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("CPI Release", "US", "inflation", past, past, "medium", "3.2%", "3.1%", "3.4%", 
              "fred", "cpi_2026_02_27", 1))
        
        event2_id = cursor.lastrowid
        
        # Add impact for released event
        cursor.execute("""
            INSERT INTO economic_event_impacts
            (event_id, market_volatility_change, sp500_price_impact, vix_change, impact_score)
            VALUES (?, ?, ?, ?, ?)
        """, (event2_id, 5.2, 0.85, 8.3, 65.0))
        
        conn.commit()
        yield event1_id, event2_id


def test_fetch_upcoming_events_basic(test_db, setup_event_data):
    """Test fetching upcoming events."""
    event1_id, event2_id = setup_event_data
    
    events, count = EconomicCalendarManager.fetch_upcoming_events(limit=50, offset=0)
    
    assert count >= 1
    assert len(events) >= 1
    assert events[0].event_name == "Non-Farm Payroll"
    assert not events[0].is_released


def test_fetch_upcoming_with_filter_country(test_db, setup_event_data):
    """Test fetching upcoming events filtered by country."""
    events, count = EconomicCalendarManager.fetch_upcoming_events(country="US")
    
    assert all(e.country == "US" for e in events)


def test_fetch_upcoming_with_filter_category(test_db, setup_event_data):
    """Test fetching upcoming events filtered by category."""
    events, count = EconomicCalendarManager.fetch_upcoming_events(category="employment")
    
    assert all(e.category == "employment" for e in events)


def test_fetch_upcoming_with_min_impact(test_db, setup_event_data):
    """Test fetching upcoming events with minimum impact filter."""
    events, count = EconomicCalendarManager.fetch_upcoming_events(min_impact="high")
    
    assert all(e.impact_level == "high" for e in events)


def test_fetch_upcoming_pagination(test_db, setup_event_data):
    """Test pagination of upcoming events."""
    events1, count1 = EconomicCalendarManager.fetch_upcoming_events(limit=1, offset=0)
    
    assert len(events1) <= 1
    assert count1 >= 1


def test_fetch_upcoming_invalid_limit(test_db):
    """Test that invalid limit raises ValueError."""
    with pytest.raises(ValueError, match="limit must be between"):
        EconomicCalendarManager.fetch_upcoming_events(limit=101)
    
    with pytest.raises(ValueError, match="limit must be between"):
        EconomicCalendarManager.fetch_upcoming_events(limit=0)


def test_fetch_upcoming_invalid_impact(test_db):
    """Test that invalid impact level raises ValueError."""
    with pytest.raises(ValueError, match="min_impact must be one of"):
        EconomicCalendarManager.fetch_upcoming_events(min_impact="extreme")


def test_fetch_history_basic(test_db, setup_event_data):
    """Test fetching historical events."""
    events, count, avg_score = EconomicCalendarManager.fetch_history()
    
    assert count >= 1
    assert len(events) >= 1
    assert events[0]['event']['event_name'] == "CPI Release"
    assert events[0]['event']['is_released']
    assert events[0]['impact']['impact_score'] == 65.0


def test_fetch_history_with_min_impact_score(test_db, setup_event_data):
    """Test filtering history by minimum impact score."""
    events, count, avg_score = EconomicCalendarManager.fetch_history(min_impact_score=50)
    
    assert all(e['impact']['impact_score'] >= 50 for e in events)


def test_fetch_history_by_country(test_db, setup_event_data):
    """Test filtering history by country."""
    events, count, avg_score = EconomicCalendarManager.fetch_history(country="US")
    
    assert all(e['event']['country'] == "US" for e in events)


def test_fetch_history_pagination(test_db, setup_event_data):
    """Test pagination of historical events."""
    events, count, avg_score = EconomicCalendarManager.fetch_history(limit=1)
    
    assert len(events) <= 1


def test_get_event_detail(test_db, setup_event_data):
    """Test fetching event details."""
    event1_id, event2_id = setup_event_data
    
    detail = EconomicCalendarManager.get_event_detail(event2_id)
    
    assert detail is not None
    assert detail['event']['id'] == event2_id
    assert detail['event']['event_name'] == "CPI Release"
    assert detail['impact']['impact_score'] == 65.0


def test_get_event_detail_not_found(test_db):
    """Test fetching non-existent event returns None."""
    detail = EconomicCalendarManager.get_event_detail(99999)
    
    assert detail is None


def test_upsert_event_new(test_db):
    """Test inserting a new event."""
    event = EconomicEvent(
        id=None,
        event_name="Test Event",
        country="US",
        category="gdp",
        scheduled_datetime="2026-03-15T10:00:00Z",
        impact_level="medium",
        external_id="test_event_001",
    )
    
    event_id = EconomicCalendarManager.upsert_event(event)
    
    assert event_id > 0
    
    # Verify it was inserted
    detail = EconomicCalendarManager.get_event_detail(event_id)
    assert detail['event']['event_name'] == "Test Event"


def test_upsert_event_existing(test_db, setup_event_data):
    """Test updating an existing event."""
    event1_id, event2_id = setup_event_data
    
    # Update existing event
    updated_event = EconomicEvent(
        id=event1_id,
        event_name="Updated NFP",
        country="US",
        category="employment",
        scheduled_datetime="2026-03-06T13:30:00Z",
        impact_level="high",
        external_id="nfp_2026_03_06",
    )
    
    result_id = EconomicCalendarManager.upsert_event(updated_event)
    
    assert result_id == event1_id
    detail = EconomicCalendarManager.get_event_detail(event1_id)
    assert detail['event']['event_name'] == "Updated NFP"


def test_record_event_impact(test_db, setup_event_data):
    """Test recording event impact."""
    event1_id, event2_id = setup_event_data
    
    impact = EventImpact(
        event_id=event1_id,
        impact_score=75.5,
        market_volatility_change=6.2,
        sp500_price_impact=1.1,
        vix_change=12.0,
    )
    
    EconomicCalendarManager.record_event_impact(impact)
    
    # Verify it was recorded
    detail = EconomicCalendarManager.get_event_detail(event1_id)
    assert detail['impact']['impact_score'] == 75.5


def test_preferences_get_default(test_db):
    """Test getting default preferences for new user."""
    prefs = PreferencesManager.get_preferences(999)
    
    assert prefs['user_id'] == 999
    assert prefs['country_list'] == []
    assert prefs['category_list'] == []
    assert prefs['min_impact_level'] == 'low'
    assert prefs['alert_enabled'] is True
    assert prefs['alert_hours_before'] == 24


def test_preferences_save_and_retrieve(test_db):
    """Test saving and retrieving preferences."""
    prefs = PreferencesManager.save_preferences(
        user_id=123,
        country_list=['US', 'EU'],
        category_list=['employment', 'inflation'],
        min_impact_level='medium',
        alert_enabled=True,
        alert_hours_before=48,
    )
    
    assert prefs['user_id'] == 123
    assert prefs['country_list'] == ['US', 'EU']
    assert prefs['category_list'] == ['employment', 'inflation']
    assert prefs['min_impact_level'] == 'medium'
    assert prefs['alert_hours_before'] == 48
    
    # Retrieve and verify
    retrieved = PreferencesManager.get_preferences(123)
    assert retrieved['country_list'] == ['US', 'EU']


def test_preferences_invalid_min_impact(test_db):
    """Test that invalid min_impact_level raises ValueError."""
    with pytest.raises(ValueError, match="min_impact_level must be one of"):
        PreferencesManager.save_preferences(
            user_id=123,
            country_list=['US'],
            category_list=['employment'],
            min_impact_level='extreme',
        )


def test_preferences_invalid_alert_hours(test_db):
    """Test that invalid alert_hours_before raises ValueError."""
    with pytest.raises(ValueError, match="alert_hours_before must be between"):
        PreferencesManager.save_preferences(
            user_id=123,
            country_list=['US'],
            category_list=['employment'],
            alert_hours_before=200,
        )
---

--- FILE: backend/tests/test_economic_calendar_api.py ---
"""
Tests for economic calendar API endpoints.
"""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def auth_headers():
    """Mock auth headers."""
    return {'Authorization': 'Bearer test_token'}


def test_get_upcoming_events_success(client, auth_headers, test_db):
    """Test successful fetch of upcoming events."""
    # Mock the manager
    with patch('backend.api.economic_calendar.EconomicCalendarManager.fetch_upcoming_events') as mock_fetch:
        from backend.managers.economic_calendar_manager import EconomicEvent
        mock_fetch.return_value = (
            [EconomicEvent(
                id=1, event_name="NFP", country="US", category="employment",
                scheduled_datetime="2026-03-06T13:30:00Z", impact_level="high"
            )],
            150
        )
        
        response = client.get('/api/economic-calendar/upcoming', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert len(data['data']) == 1
    assert data['meta']['total_count'] == 150


def test_get_upcoming_events_invalid_limit(client, auth_headers):
    """Test invalid limit parameter."""
    response = client.get(
        '/api/economic-calendar/upcoming?limit=101',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert 'errors' in response.get_json()


def test_get_upcoming_events_filters(client, auth_headers):
    """Test filtering upcoming events by country and category."""
    with patch('backend.api.economic_calendar.EconomicCalendarManager.fetch_upcoming_events') as mock_fetch:
        mock_fetch.return_value = ([], 0)
        
        response = client.get(
            '/api/economic-calendar/upcoming?country=US&category=employment',
            headers=auth_headers
        )
    
    assert response.status_code == 200
    mock_fetch.assert_called_once()
    call_kwargs = mock_fetch.call_args[1]
    assert call_kwargs['country'] == 'US'
    assert call_kwargs['category'] == 'employment'


def test_get_history_success(client, auth_headers):
    """Test successful fetch of historical events."""
    with patch('backend.api.economic_calendar.EconomicCalendarManager.fetch_history') as mock_fetch:
        mock_fetch.return_value = (
            [{
                'event': {'id': 1, 'event_name': 'CPI', 'country': 'US', 'category': 'inflation', 'is_released': True},
                'impact': {'impact_score': 65.0, 'sp500_price_impact': 0.8}
            }],
            250,
            62.3
        )
        
        response = client.get('/api/economic-calendar/history', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert len(data['data']) == 1
    assert data['meta']['avg_impact_score'] == 62.3


def test_get_history_pagination(client, auth_headers):
    """Test pagination of historical events."""
    with patch('backend.api.economic_calendar.EconomicCalendarManager.fetch_history') as mock_fetch:
        mock_fetch.return_value = ([], 500, 50.0)
        
        response = client.get(
            '/api/economic-calendar/history?limit=25&offset=25',
            headers=auth_headers
        )
    
    assert response.status_code == 200
    mock_fetch.assert_called_once()
    call_kwargs = mock_fetch.call_args[1]
    assert call_kwargs['limit'] == 25
    assert call_kwargs['offset'] == 25


def test_get_event_detail_success(client, auth_headers):
    """Test fetching event detail."""
    with patch('backend.api.economic_calendar.EconomicCalendarManager.get_event_detail') as mock_get:
        mock_get.return_value = {
            'event': {'id': 1, 'event_name': 'NFP', 'country': 'US'},
            'impact': {'impact_score': 75.5},
            'related_events': []
        }
        
        response = client.get('/api/economic-calendar/1', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['event']['event_name'] == 'NFP'


def test_get_event_detail_not_found(client, auth_headers):
    """Test fetching non-existent event."""
    with patch('backend.api.economic_calendar.EconomicCalendarManager.get_event_detail') as mock_get:
        mock_get.return_value = None
        
        response = client.get('/api/economic-calendar/99999', headers=auth_headers)
    
    assert response.status_code == 404


def test_get_preferences_success(client, auth_headers):
    """Test fetching user preferences."""
    with patch('backend.api.economic_calendar.PreferencesManager.get_preferences') as mock_get:
        with patch('backend.api.economic_calendar.current_user') as mock_user:
            mock_user.id = 123
            mock_get.return_value = {
                'user_id': 123,
                'country_list': ['US'],
                'category_list': ['employment'],
                'min_impact_level': 'medium'
            }
            
            response = client.get('/api/economic-calendar/preferences', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['user_id'] == 123


def test_save_preferences_success(client, auth_headers):
    """Test saving user preferences."""
    with patch('backend.api.economic_calendar.PreferencesManager.save_preferences') as mock_save:
        with patch('backend.api.economic_calendar.current_user') as mock_user:
            mock_user.id = 123
            mock_save.return_value = {
                'user_id': 123,
                'country_list': ['US', 'EU'],
                'category_list': ['employment'],
                'min_impact_level': 'high',
                'alert_enabled': True,
                'alert_hours_before': 48
            }
            
            response = client.post(
                '/api/economic-calendar/preferences',
                json={
                    'country_list': ['US', 'EU'],
                    'category_list': ['employment'],
                    'min_impact_level': 'high',
                    'alert_enabled': True,
                    'alert_hours_before': 48
                },
                headers=auth_headers
            )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['country_list'] == ['US', 'EU']


def test_save_preferences_validation_error(client, auth_headers):
    """Test preferences validation error."""
    with patch('backend.api.economic_calendar.PreferencesManager.save_preferences') as mock_save:
        with patch('backend.api.economic_calendar.current_user') as mock_user:
            mock_user.id = 123
            mock_save.side_effect = ValueError("min_impact_level must be one of: low, medium, high")
            
            response = client.post(
                '/api/economic-calendar/preferences',
                json={'min_impact_level': 'invalid'},
                headers=auth_headers
            )
    
    assert response.status_code == 400


def test_impact_analysis_success(client, auth_headers):
    """Test impact analysis endpoint."""
    with patch('backend.api.economic_calendar.db_session') as mock_session:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'event_name': 'NFP',
                'impact_score': 75.0,
                'sp500_price_impact': 1.2,
                'vix_change': 15.0
            }
        ]
        mock_session.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        response = client.get(
            '/api/economic-calendar/impact-analysis?event_ids=1,2,3&tickers=SPY,GLD',
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'events_analyzed' in data['data']


def test_impact_analysis_missing_event_ids(client, auth_headers):
    """Test impact analysis without event_ids."""
    response = client.get(
        '/api/economic-calendar/impact-analysis?tickers=SPY',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert 'event_ids parameter is required' in response.get_json()['errors']
---

--- FILE: frontend/src/components/economic-calendar/EconomicCalendarWidget.tsx ---
```typescript
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { AlertCircle, TrendingUp, Calendar } from 'lucide-react';

interface EconomicEvent {
  id: number;
  event_name: string;
  country: string;
  category: string;
  scheduled_datetime: string;
  impact_level: 'low' | 'medium' | 'high';
  forecast_value?: string;
  previous_value?: string;
}

export const EconomicCalendarWidget: React.FC = () => {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUpcomingEvents = async () => {
      try {
        const response = await fetch(
          '/api/economic-calendar/upcoming?limit=5&min_impact=medium',
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
            },
          }
        );

        if (!response.ok) throw new Error('Failed to fetch events');

        const { data } = await response.json();
        setEvents(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading events');
      } finally {
        setLoading(false);
      }
    };

    fetchUpcomingEvents();
  }, []);

  const getImpactColor = (level: string): string => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
    };
    return colors[level] || colors.low;
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="h-32 animate-pulse bg-gray-200 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Economic Calendar
        </h3>
        <Link
          href="/dashboard/economic-calendar"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          View All →
        </Link>
      </div>

      <div className="space-y-3">
        {events.length === 0 ? (
          <p className="text-gray-500 text-sm">No upcoming events</p>
        ) : (
          events.map((event) => (
            <div key={event.id} className="flex items-start gap-3 pb-3 border-b border-gray-100 last:border-0">
              <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                event.impact_level === 'high' ? 'bg-red-500' :
                event.impact_level === 'medium' ? 'bg-yellow-500' :
                'bg-green-500'
              }`} />
              
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-gray-900 truncate">
                  {event.event_name}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {format(new Date(event.scheduled_datetime), 'MMM d, h:mm a')}
                </p>
              </div>

              <div className="flex-shrink-0">
                <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${getImpactColor(event.impact_level)}`}>
                  {event.impact_level.charAt(0).toUpperCase() + event.impact_level.slice(1)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
```