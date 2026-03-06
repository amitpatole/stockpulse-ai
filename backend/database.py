```python
"""SQLite database management with WAL mode and idempotent migrations."""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional

import aiosqlite

from backend.config import Config

logger = logging.getLogger(__name__)

# ── Synchronous helpers ─────────────────────────────────────────────

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory enabled."""
    path = db_path or Config.DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_session(db_path: Optional[str] = None):
    """Context manager that yields a connection and auto-closes it."""
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Async helpers ───────────────────────────────────────────────────

async def get_async_db(db_path: Optional[str] = None) -> aiosqlite.Connection:
    """Return an async SQLite connection."""
    path = db_path or Config.DB_PATH
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


# ── Schema ──────────────────────────────────────────────────────────

_TABLES_SQL = [
    # Agents
    """
    CREATE TABLE IF NOT EXISTS agents (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        role            TEXT NOT NULL,
        character_name  TEXT NOT NULL,
        provider        TEXT NOT NULL,
        model           TEXT NOT NULL,
        state           TEXT NOT NULL DEFAULT 'sleeping',
        current_task_id TEXT,
        desk_x          INTEGER DEFAULT 0,
        desk_y          INTEGER DEFAULT 0,
        avatar_color    TEXT DEFAULT '#6366f1',
        total_tasks     INTEGER DEFAULT 0,
        total_prs       INTEGER DEFAULT 0,
        total_cost      REAL DEFAULT 0.0,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Tasks (the 23 enhancements + subtasks)
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id              TEXT PRIMARY KEY,
        title           TEXT NOT NULL,
        description     TEXT,
        task_type       TEXT NOT NULL DEFAULT 'feature',
        status          TEXT NOT NULL DEFAULT 'backlog',
        priority        INTEGER DEFAULT 0,
        story_points    INTEGER DEFAULT 0,
        assigned_to     TEXT,
        sprint_id       TEXT,
        parent_task_id  TEXT,
        branch_name     TEXT,
        pr_number       INTEGER,
        design_doc      TEXT,
        project_id      TEXT DEFAULT 'proj-tickerpulse',
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at    TIMESTAMP,
        FOREIGN KEY (assigned_to) REFERENCES agents(id),
        FOREIGN KEY (sprint_id) REFERENCES sprints(id)
    )
    """,
    # Sprints
    """
    CREATE TABLE IF NOT EXISTS sprints (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        goal            TEXT,
        status          TEXT NOT NULL DEFAULT 'planning',
        sprint_number   INTEGER NOT NULL,
        planned_points  INTEGER DEFAULT 0,
        completed_points INTEGER DEFAULT 0,
        start_date      TEXT,
        end_date        TEXT,
        retro_notes     TEXT,
        project_id      TEXT DEFAULT 'proj-tickerpulse',
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Inter-agent messages
    """
    CREATE TABLE IF NOT EXISTS messages (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id       TEXT NOT NULL,
        channel         TEXT NOT NULL DEFAULT 'general',
        content         TEXT NOT NULL,
        message_type    TEXT NOT NULL DEFAULT 'chat',
        metadata        TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES agents(id)
    )
    """,
    # LLM code generation runs
    """
    CREATE TABLE IF NOT EXISTS code_runs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id        TEXT NOT NULL,
        task_id         TEXT,
        provider        TEXT NOT NULL,
        model           TEXT NOT NULL,
        prompt_type     TEXT NOT NULL,
        tokens_input    INTEGER DEFAULT 0,
        tokens_output   INTEGER DEFAULT 0,
        estimated_cost  REAL DEFAULT 0.0,
        duration_ms     INTEGER DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'pending',
        output_summary  TEXT,
        error           TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """,
    # Office events (meetings, breaks, phase changes)
    """
    CREATE TABLE IF NOT EXISTS office_events (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type      TEXT NOT NULL,
        title           TEXT NOT NULL,
        description     TEXT,
        participants    TEXT,
        office_time     TEXT NOT NULL,
        metadata        TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Pull requests
    """
    CREATE TABLE IF NOT EXISTS pull_requests (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id         TEXT NOT NULL,
        pr_number       INTEGER,
        branch_name     TEXT NOT NULL,
        title           TEXT NOT NULL,
        description     TEXT,
        status          TEXT NOT NULL DEFAULT 'open',
        files_changed   TEXT,
        review_comments TEXT,
        reviewer_id     TEXT,
        github_url      TEXT,
        branch_url      TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        merged_at       TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (reviewer_id) REFERENCES agents(id)
    )
    """,
    # Task activity log (status changes, assignments, PR events)
    """
    CREATE TABLE IF NOT EXISTS task_activities (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id         TEXT NOT NULL,
        agent_id        TEXT,
        action          TEXT NOT NULL,
        detail          TEXT,
        metadata        TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """,
    # Cost tracking ledger
    """
    CREATE TABLE IF NOT EXISTS cost_tracking (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        date            TEXT NOT NULL,
        agent_id        TEXT,
        provider        TEXT,
        model           TEXT,
        tokens_input    INTEGER DEFAULT 0,
        tokens_output   INTEGER DEFAULT 0,
        estimated_cost  REAL DEFAULT 0.0,
        job_type        TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    """,
    # Task token estimates (budget tracking)
    """
    CREATE TABLE IF NOT EXISTS task_token_estimates (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id                 TEXT NOT NULL UNIQUE,
        task_title              TEXT,
        task_type               TEXT,
        estimated_story_points  INTEGER DEFAULT 0,
        estimated_tokens        INTEGER DEFAULT 0,
        created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """,
    # Agent task execution attempts (accountability tracking)
    """
    CREATE TABLE IF NOT EXISTS agent_task_attempts (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id            TEXT NOT NULL,
        task_id             TEXT NOT NULL,
        attempt_num         INTEGER NOT NULL,
        status              TEXT NOT NULL,
        tokens_used         INTEGER DEFAULT 0,
        estimated_tokens    INTEGER DEFAULT 0,
        budget_variance     INTEGER DEFAULT 0,
        exceeded_budget     INTEGER DEFAULT 0,
        error_reason        TEXT,
        duration_seconds    REAL DEFAULT 0.0,
        output_generated    INTEGER DEFAULT 0,
        metadata            TEXT,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """,
    # Agent daily metrics (aggregated performance)
    """
    CREATE TABLE IF NOT EXISTS agent_daily_metrics (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id            TEXT NOT NULL,
        metric_date         TEXT NOT NULL,
        tasks_attempted     INTEGER DEFAULT 0,
        tasks_completed     INTEGER DEFAULT 0,
        success_rate_pct    REAL DEFAULT 0.0,
        tokens_used         INTEGER DEFAULT 0,
        total_cost          REAL DEFAULT 0.0,
        avg_duration_seconds REAL DEFAULT 0.0,
        critical_issues     INTEGER DEFAULT 0,
        escalations         INTEGER DEFAULT 0,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(agent_id, metric_date),
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )
    """,
    # Token budget system tables
    # Project token budgets
    """
    CREATE TABLE IF NOT EXISTS project_token_budgets (
        project_id TEXT PRIMARY KEY,
        base_budget INTEGER NOT NULL,
        buffer_pct REAL NOT NULL DEFAULT 0.40,
        total_budget INTEGER NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        tokens_remaining INTEGER,
        efficiency_ratio REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Agent token allocations
    """
    CREATE TABLE IF NOT EXISTS agent_token_allocations (
        allocation_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        allocated_tokens INTEGER NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        tasks_assigned INTEGER DEFAULT 0,
        tasks_completed INTEGER DEFAULT 0,
        avg_tokens_per_task REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES project_token_budgets(project_id),
        UNIQUE(project_id, agent_id)
    )
    """,
    # Task token records
    """
    CREATE TABLE IF NOT EXISTS task_token_records (
        record_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL UNIQUE,
        project_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        estimated_tokens INTEGER,
        actual_tokens_used INTEGER NOT NULL,
        buffer_tokens_used INTEGER,
        status TEXT,
        efficiency_ratio REAL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES project_token_budgets(project_id)
    )
    """,
    # Project costs and billing
    """
    CREATE TABLE IF NOT EXISTS project_costs (
        cost_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL UNIQUE,
        base_cost DECIMAL(10, 2),
        hourly_rate INTEGER,
        execution_hours REAL,
        efficiency_bonus DECIMAL(10, 2),
        subtotal DECIMAL(10, 2),
        profit_margin_pct REAL DEFAULT 0.70,
        customer_price DECIMAL(10, 2),
        discount_pct REAL DEFAULT 0.0,
        discount_amount DECIMAL(10, 2),
        final_price DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES project_token_budgets(project_id)
    )
    """,
    # Token estimation history
    """
    CREATE TABLE IF NOT EXISTS token_estimation_history (
        history_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        task_type TEXT,
        estimated_tokens INTEGER,
        actual_tokens INTEGER,
        efficiency_ratio REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Projects
    """
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        repo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Teams
    """
    CREATE TABLE IF NOT EXISTS teams (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        project_id TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """,
    # Team members
    """
    CREATE TABLE IF NOT EXISTS team_members (
        id TEXT PRIMARY KEY,
        team_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        role TEXT,
        character_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES teams(id),
        FOREIGN KEY (member_id) REFERENCES agents(id)
    )
    """,
]

_INDEXES_SQL = [
    # Single-column indexes for common filters
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_sprint ON tasks(sprint_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)",
    "CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel)",
    "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_code_runs_agent ON code_runs(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_code_runs_task ON code_runs(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_office_events_type ON office_events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_pull_requests_task ON pull_requests(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_pull_requests_status ON pull_requests(status)",
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_date ON cost_tracking(date)",
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_agent ON cost_tracking(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_activities_task ON task_activities(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_activities_created ON task_activities(created_at)",
    
    # Accountability indexes
    "CREATE INDEX IF NOT EXISTS idx_task_token_estimates_task ON task_token_estimates(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_agent_task_attempts_agent ON agent_task_attempts(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_agent_task_attempts_task ON agent_task_attempts(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_agent_task_attempts_created ON agent_task_attempts(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_agent_task_attempts_status ON agent_task_attempts(status)",
    "CREATE INDEX IF NOT EXISTS idx_agent_daily_metrics_agent ON agent_daily_metrics(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_agent_daily_metrics_date ON agent_daily_metrics(metric_date)",
    
    # Token budget indexes
    "CREATE INDEX IF NOT EXISTS idx_project_tokens ON project_token_budgets(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_agent_allocations ON agent_token_allocations(project_id, agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_records ON task_token_records(project_id, agent_id, task_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_costs ON project_costs(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_token_history ON token_estimation_history(project_id, created_at)",
    
    # Composite indexes for hot-path queries
    # Tasks: filter by status within a sprint, or by assigned agent
    "CREATE INDEX IF NOT EXISTS idx_tasks_status_sprint ON tasks(status, sprint_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_assigned_status ON tasks(assigned_to, status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status)",
    
    # Task activities: get recent activities for a specific task
    "CREATE INDEX IF NOT EXISTS idx_task_activities_task_created ON task_activities(task_id, created_at DESC)",
    
    # Agent task attempts: track attempts by agent and status, ordered by date
    "CREATE INDEX IF NOT EXISTS idx_agent_task_attempts_agent_status ON agent_task_attempts(agent_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_agent_task_attempts_agent_created ON agent_task_attempts(agent_id, created_at DESC)",
    
    # Pull requests: get PRs for a task by status
    "CREATE INDEX IF NOT EXISTS idx_pull_requests_task_status ON pull_requests(task_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_pull_requests_status_created ON pull_requests(status, created_at DESC)",
    
    # Messages: get messages from sender, ordered by time
    "CREATE INDEX IF NOT EXISTS idx_messages_sender_created ON messages(sender_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_messages_channel_created ON messages(channel, created_at DESC)",
    
    # Cost tracking: get costs by agent within date range
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_agent_date ON cost_tracking(agent_id, date)",
    
    # Agent token allocations: get allocations for a project
    "CREATE INDEX IF NOT EXISTS idx_agent_allocations_project ON agent_token_allocations(project_id)",
]


# ── Seed data: 23 TickerPulse enhancements ──────────────────────────

# Onboarding tasks - agents analyze the real TickerPulse repo and create their own backlog
BACKLOG_TASKS = [
    ("TP-001", "Project Onboarding: Analyze TickerPulse AI Repository",
     "Read the full README.md, CLAUDE.md, .env.example, and project structure of the TickerPulse AI repository. Understand: project goals, architecture (Flask backend + Next.js frontend), multi-agent system (Scanner, Researcher, Regime, Investigator), data providers, scheduler jobs, API endpoints, database schema. Create a comprehensive docs/PROJECT_ANALYSIS.md file committed to the repo.",
     "feature", 8),
    ("TP-002", "Codebase Audit: Backend Architecture & Code Quality",
     "Deep audit of backend/ - inspect every Python file, understand Flask app factory, blueprints, agent system, data providers, scheduler, database.py, config.py. Identify: code quality issues, missing error handling, security gaps, performance bottlenecks, TODO/FIXME comments, dead code, missing tests. Create docs/BACKEND_AUDIT.md committed to the repo with severity ratings.",
     "feature", 8),
    ("TP-003", "Codebase Audit: Frontend Architecture & UI Review",
     "Deep audit of frontend/ - inspect Next.js app structure, pages, components, API integration, SSE streaming, TradingView charts, agent mission control UI. Identify: missing features, UI/UX gaps, accessibility issues, performance problems. Create docs/FRONTEND_AUDIT.md committed to the repo.",
     "feature", 8),
    ("TP-004", "Gap Analysis: Features Documented vs Actually Implemented",
     "Compare what the README promises vs what the code actually delivers. Check each feature: multi-agent system working?, all 18+ scheduler jobs implemented?, all API endpoints functional?, all data providers working?, cost tracking accurate?, SSE streaming reliable? Create docs/GAP_ANALYSIS.md committed to the repo.",
     "feature", 5),
    ("TP-005", "Sprint Planning: Create Prioritized Backlog from Analysis",
     "Based on findings from TP-001 through TP-004, create a prioritized backlog of real tasks. Each task should have: clear title, detailed description, story points, priority, task type. Create docs/SPRINT_BACKLOG.md committed to the repo with story points and sprint plan.",
     "feature", 5),
]


def init_all_tables(db_path: Optional[str] = None) -> None:
    """Create every table and apply indexes. Safe to call multiple times."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        for sql in _TABLES_SQL:
            cursor.execute(sql)
        for sql in _INDEXES_SQL:
            cursor.execute(sql)
        conn.commit()
        logger.info("Database tables initialized with composite indexes")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_backlog(db_path: Optional[str] = None) -> None:
    """Seed the 23 TickerPulse enhancement tasks if not already present."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        existing = cursor.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'TP-%'").fetchone()[0]
        if existing > 0:
            logger.info(f"Backlog already seeded ({existing} tasks)")
            return
        for task_id, title, description, task_type, points in BACKLOG_TASKS:
            cursor.execute(
                """INSERT INTO tasks (id, title, description, task_type, status, story_points, priority)
                   VALUES (?, ?, ?, ?, 'backlog', ?, ?)""",
                (task_id, title, description, task_type, points, int(task_id.split("-")[1])),
            )
        logger.info(f"Seeded {len(BACKLOG_TASKS)} backlog tasks")


def migrate_add_github_urls(db_path: Optional[str] = None) -> None:
    """Add github_url and branch_url columns if they don't exist."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        # Check if columns exist
        info = cursor.execute("PRAGMA table_info(pull_requests)").fetchall()
        col_names = {row[1] for row in info}
        if "github_url" not in col_names:
            cursor.execute("ALTER TABLE pull_requests ADD COLUMN github_url TEXT")
            logger.info("Added github_url column to pull_requests")
        if "branch_url" not in col_names:
            cursor.execute("ALTER TABLE pull_requests ADD COLUMN branch_url TEXT")
            logger.info("Added branch_url column to pull_requests")


def migrate_add_project_id_to_sprints(db_path: Optional[str] = None) -> None:
    """Add project_id column to sprints table if it doesn't exist."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        # Check if column exists
        info = cursor.execute("PRAGMA table_info(sprints)").fetchall()
        col_names = {row[1] for row in info}
        if "project_id" not in col_names:
            cursor.execute("ALTER TABLE sprints ADD COLUMN project_id TEXT DEFAULT 'proj-tickerpulse'")
            logger.info("Added project_id column to sprints")


def migrate_add_project_id_to_tasks(db_path: Optional[str] = None) -> None:
    """Add project_id column to tasks table if it doesn't exist."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        # Check if column exists
        info = cursor.execute("PRAGMA table_info(tasks)").fetchall()
        col_names = {row[1] for row in info}
        if "project_id" not in col_names:
            cursor.execute("ALTER TABLE tasks ADD COLUMN project_id TEXT DEFAULT 'proj-tickerpulse'")
            logger.info("Added project_id column to tasks")


def migrate_add_inter_agent_messaging(db_path: Optional[str] = None) -> None:
    """Add columns for inter-agent messaging to messages table."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        # Check if columns exist
        info = cursor.execute("PRAGMA table_info(messages)").fetchall()
        col_names = {row[1] for row in info}

        # Add recipient_id column
        if "recipient_id" not in col_names:
            cursor.execute("ALTER TABLE messages ADD COLUMN recipient_id TEXT")
            logger.info("Added recipient_id column to messages")

        # Add is_response column
        if "is_response" not in col_names:
            cursor.execute("ALTER TABLE messages ADD COLUMN is_response INTEGER DEFAULT 0")
            logger.info("Added is_response column to messages")

        # Add parent_message_id column
        if "parent_message_id" not in col_names:
            cursor.execute("ALTER TABLE messages ADD COLUMN parent_message_id TEXT")
            logger.info("Added parent_message_id column to messages")

        # Add context column
        if "context" not in col_names:
            cursor.execute("ALTER TABLE messages ADD COLUMN context TEXT")
            logger.info("Added context column to messages")


def seed_agents(db_path: Optional[str] = None) -> None:
    """Seed the 8 AI agent employees if not already present."""
    agents = [
        ("ceo", "CEO/PM", "Marcus Webb", "anthropic", "sonnet", 3, 3, "#f59e0b"),
        ("architect", "Architect", "Diana Torres", "anthropic", "sonnet", 7, 3, "#8b5cf6"),
        ("frontend-dev", "Frontend Dev", "Kai Nakamura", "anthropic", "sonnet", 11, 3, "#3b82f6"),
        ("backend-dev", "Backend Dev", "Priya Sharma", "anthropic", "sonnet", 3, 7, "#10b981"),
        ("qa", "QA Engineer", "Jordan Blake", "anthropic", "haiku", 7, 7, "#ef4444"),
        ("devops", "DevOps", "Sam Chen", "anthropic", "haiku", 11, 7, "#06b6d4"),
        ("researcher", "Research Analyst", "Elena Volkov", "anthropic", "haiku", 3, 11, "#ec4899"),
        ("ideation", "Ideation", "Theo Park", "anthropic", "sonnet", 7, 11, "#f97316"),
    ]
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        existing = cursor.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        if existing > 0:
            # Update desk positions for existing agents
            for agent_id, role, name, provider, model, dx, dy, color in agents:
                cursor.execute(
                    "UPDATE agents SET desk_x=?, desk_y=?, avatar_color=? WHERE id=?",
                    (dx, dy, color, agent_id),
                )
            logger.info(f"Updated desk positions for {existing} agents")
            return
        for agent_id, role, name, provider, model, dx, dy, color in agents:
            cursor.execute(
                """INSERT INTO agents (id, name, role, character_name, provider, model, desk_x, desk_y, avatar_color)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent_id, name, role, name, provider, model, dx, dy, color),
            )
        logger.info(f"Seeded {len(agents)} agents")


def seed_projects(db_path: Optional[str] = None) -> None:
    """Seed default projects if not already present."""
    projects = [
        ("proj-tickerpulse", "TickerPulse AI", "Real-time financial data analysis platform with AI-powered insights", "git@github.com:amitpatole/tickerpulse-ai.git"),
    ]
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        existing = cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if existing > 0:
            logger.info(f"Projects already seeded ({existing} projects)")
            return
        for project_id, name, description, repo in projects:
            cursor.execute(
                """INSERT INTO projects (id, name, description, repo)
                   VALUES (?, ?, ?, ?)""",
                (project_id, name, description, repo),
            )
        logger.info(f"Seeded {len(projects)} projects")
```