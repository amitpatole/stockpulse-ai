"""
TickerPulse AI v3.0 - Database Adapter Tests
Comprehensive tests for adapter pattern (SQLite and PostgreSQL).
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock, PropertyMock
from backend.adapters import get_db_adapter
from backend.adapters.sqlite_adapter import SQLiteAdapter
from backend.adapters.postgres_adapter import PostgresAdapter


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestGetDbAdapter:
    """Test factory function get_db_adapter()."""

    def test_factory_returns_sqlite_adapter_from_config(self):
        """AC1: Factory returns SQLiteAdapter when DB_TYPE='sqlite'."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DB_TYPE = "sqlite"
            mock_config.DB_PATH = ":memory:"

            adapter = get_db_adapter()

            assert isinstance(adapter, SQLiteAdapter)
            assert adapter.db_path == ":memory:"

    def test_factory_returns_sqlite_adapter_explicit(self):
        """Factory returns SQLiteAdapter when explicitly passed 'sqlite'."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DB_PATH = "/tmp/test.db"

            adapter = get_db_adapter("sqlite")

            assert isinstance(adapter, SQLiteAdapter)
            assert adapter.db_path == "/tmp/test.db"

    @patch("backend.adapters.postgres_adapter.psycopg", MagicMock())
    def test_factory_returns_postgres_adapter_from_config(self):
        """AC2: Factory returns PostgresAdapter when DB_TYPE='postgres'."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DB_TYPE = "postgres"
            mock_config.DATABASE_URL = "postgresql://user:pass@localhost/db"
            mock_config.DB_POOL_SIZE = 20

            adapter = get_db_adapter()

            assert isinstance(adapter, PostgresAdapter)
            assert adapter.database_url == "postgresql://user:pass@localhost/db"
            assert adapter.pool_size == 20

    @patch("backend.adapters.postgres_adapter.psycopg", MagicMock())
    def test_factory_returns_postgres_adapter_explicit(self):
        """Factory returns PostgresAdapter when explicitly passed 'postgres'."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DATABASE_URL = "postgresql://localhost/test"
            mock_config.DB_POOL_SIZE = 15

            adapter = get_db_adapter("postgres")

            assert isinstance(adapter, PostgresAdapter)
            assert adapter.database_url == "postgresql://localhost/test"
            assert adapter.pool_size == 15

    def test_factory_case_insensitive_sqlite(self):
        """Factory handles case-insensitive 'SQLite' input."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DB_PATH = "/tmp/test.db"

            adapter = get_db_adapter("SQLite")

            assert isinstance(adapter, SQLiteAdapter)

    @patch("backend.adapters.postgres_adapter.psycopg", MagicMock())
    def test_factory_case_insensitive_postgres(self):
        """Factory handles case-insensitive 'PostgreSQL' input."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DATABASE_URL = "postgresql://localhost/db"
            mock_config.DB_POOL_SIZE = 10

            adapter = get_db_adapter("POSTGRES")

            assert isinstance(adapter, PostgresAdapter)

    def test_factory_raises_valueerror_invalid_type(self):
        """AC3: Factory raises ValueError for unsupported DB types."""
        with patch("backend.config.Config"):
            with pytest.raises(ValueError) as exc_info:
                get_db_adapter("mysql")

            assert "Unsupported database type" in str(exc_info.value)
            assert "mysql" in str(exc_info.value)

    def test_factory_raises_valueerror_for_empty_string(self):
        """Factory raises ValueError for empty DB type."""
        with patch("backend.config.Config"):
            with pytest.raises(ValueError):
                get_db_adapter("")

    @patch("backend.adapters.postgres_adapter.psycopg", MagicMock())
    def test_factory_respects_explicit_override_over_config(self):
        """AC4: Explicit db_type parameter overrides Config.DB_TYPE."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DB_TYPE = "sqlite"
            mock_config.DB_PATH = "/tmp/test.db"
            mock_config.DATABASE_URL = "postgresql://localhost/db"
            mock_config.DB_POOL_SIZE = 10

            # Override: use postgres even though config says sqlite
            adapter = get_db_adapter("postgres")

            assert isinstance(adapter, PostgresAdapter)
            assert adapter.database_url == "postgresql://localhost/db"


# ============================================================================
# SQLiteAdapter Tests
# ============================================================================


class TestSQLiteAdapter:
    """Test SQLiteAdapter implementation."""

    def test_sqlite_connect_initializes_connection(self):
        """SQLiteAdapter.connect() initializes sqlite3 connection."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        assert adapter._connection is not None
        assert isinstance(adapter._connection, sqlite3.Connection)

        adapter.disconnect()

    def test_sqlite_connect_sets_row_factory(self):
        """SQLiteAdapter.connect() sets row_factory to sqlite3.Row."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        assert adapter._connection.row_factory == sqlite3.Row

        adapter.disconnect()

    def test_sqlite_connect_enables_foreign_keys(self):
        """SQLiteAdapter.connect() enables PRAGMA foreign_keys."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        cursor = adapter._connection.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()

        # Result should be (1,) for enabled, (0,) for disabled
        assert result[0] == 1, "Foreign keys should be enabled"

        adapter.disconnect()

    def test_sqlite_disconnect_closes_connection(self):
        """SQLiteAdapter.disconnect() closes connection and sets to None."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()
        assert adapter._connection is not None

        adapter.disconnect()

        assert adapter._connection is None

    def test_sqlite_disconnect_idempotent(self):
        """SQLiteAdapter.disconnect() can be called multiple times safely."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()
        adapter.disconnect()
        adapter.disconnect()  # Should not raise

        assert adapter._connection is None

    def test_sqlite_get_connection_context_manager(self):
        """SQLiteAdapter.get_connection() works as context manager."""
        adapter = SQLiteAdapter(":memory:")

        with adapter.get_connection() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

    def test_sqlite_get_connection_auto_commits(self):
        """SQLiteAdapter.get_connection() auto-commits on success."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        # Create a table and insert via context manager
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test (name) VALUES ('test')")

        # Verify commit by querying in new connection context
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test")
            rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0]["name"] == "test"

        adapter.disconnect()

    def test_sqlite_get_connection_auto_rollback_on_error(self):
        """SQLiteAdapter.get_connection() auto-rollbacks on exception."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        # Create a table first
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test (name) VALUES ('original')")

        # Try to insert and raise an error
        try:
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO test (name) VALUES ('should_rollback')")
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # Verify only original row exists (rollback worked)
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]

        assert count == 1

        adapter.disconnect()

    def test_sqlite_execute_returns_cursor(self):
        """SQLiteAdapter.execute() returns cursor with executed query."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER)")
            assert cursor is not None

        adapter.disconnect()

    def test_sqlite_fetchall_returns_rows(self):
        """SQLiteAdapter.fetchall() returns all rows from cursor."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER, name TEXT)")
            adapter.execute(conn, "INSERT INTO test VALUES (1, 'a')")
            adapter.execute(conn, "INSERT INTO test VALUES (2, 'b')")

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "SELECT * FROM test")
            rows = adapter.fetchall(cursor)

        assert len(rows) == 2
        assert rows[0]["id"] == 1
        assert rows[0]["name"] == "a"

        adapter.disconnect()

    def test_sqlite_fetchone_returns_single_row(self):
        """SQLiteAdapter.fetchone() returns single row from cursor."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER, name TEXT)")
            adapter.execute(conn, "INSERT INTO test VALUES (1, 'a')")

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "SELECT * FROM test LIMIT 1")
            row = adapter.fetchone(cursor)

        assert row is not None
        assert row["id"] == 1

        adapter.disconnect()

    def test_sqlite_execute_with_parameters(self):
        """SQLiteAdapter.execute() handles parameterized queries."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER, name TEXT)")
            cursor = adapter.execute(conn, "INSERT INTO test VALUES (?, ?)", (1, "test"))

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "SELECT * FROM test WHERE id = ?", (1,))
            row = adapter.fetchone(cursor)

        assert row["name"] == "test"

        adapter.disconnect()

    def test_sqlite_executemany(self):
        """SQLiteAdapter.executemany() handles bulk inserts."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER, name TEXT)")
            data = [(1, "a"), (2, "b"), (3, "c")]
            cursor = adapter.executemany(conn, "INSERT INTO test VALUES (?, ?)", data)

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]

        assert count == 3

        adapter.disconnect()


# ============================================================================
# PostgresAdapter Tests
# ============================================================================


class TestPostgresAdapter:
    """Test PostgresAdapter implementation (with mocking)."""

    def test_postgres_init_raises_on_missing_psycopg(self):
        """PostgresAdapter.__init__() raises ImportError if psycopg not installed."""
        with patch("backend.adapters.postgres_adapter.psycopg", None):
            with pytest.raises(ImportError) as exc_info:
                PostgresAdapter("postgresql://localhost/db", 10)

            assert "psycopg" in str(exc_info.value)

    def test_postgres_init_stores_config(self):
        """PostgresAdapter.__init__() stores database URL and pool size."""
        with patch("backend.adapters.postgres_adapter.psycopg"):
            adapter = PostgresAdapter("postgresql://localhost/db", 25)

            assert adapter.database_url == "postgresql://localhost/db"
            assert adapter.pool_size == 25

    def test_postgres_init_default_pool_size(self):
        """PostgresAdapter.__init__() uses default pool_size=10."""
        with patch("backend.adapters.postgres_adapter.psycopg"):
            adapter = PostgresAdapter("postgresql://localhost/db")

            assert adapter.pool_size == 10

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_connect_creates_pool(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.connect() creates SimpleConnectionPool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db", 15)
        adapter.connect()

        mock_pool_class.assert_called_once_with(
            "postgresql://localhost/db", min_size=1, max_size=15
        )
        assert adapter._pool == mock_pool

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_disconnect_closes_pool(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.disconnect() closes pool and sets to None."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()
        adapter.disconnect()

        mock_pool.close.assert_called_once()
        assert adapter._pool is None

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_disconnect_idempotent(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.disconnect() safe to call multiple times."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()
        adapter.disconnect()
        adapter.disconnect()  # Should not raise

        assert adapter._pool is None

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_get_connection_context_manager(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter.get_connection() works as context manager."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        with adapter.get_connection() as conn:
            assert conn == mock_conn

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_get_connection_auto_commits(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter.get_connection() auto-commits on success."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        with adapter.get_connection() as conn:
            pass  # Success path

        mock_conn.commit.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_get_connection_auto_rollback_on_error(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter.get_connection() auto-rollbacks on exception."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        try:
            with adapter.get_connection() as conn:
                raise ValueError("Intentional error")
        except ValueError:
            pass

        mock_conn.rollback.assert_called_once()
        # Connection still returned to pool
        mock_pool.putconn.assert_called_once_with(mock_conn)

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_returns_connection_to_pool_in_finally(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter.get_connection() returns conn to pool in finally block."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        try:
            with adapter.get_connection() as conn:
                raise RuntimeError("Critical error")
        except RuntimeError:
            pass

        # Verify connection returned even on exception
        mock_pool.putconn.assert_called_once_with(mock_conn)

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_execute_returns_cursor(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.execute() returns cursor."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        result = adapter.execute(mock_conn, "SELECT * FROM users", (1,))

        assert result == mock_cursor
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users", (1,))

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_fetchall_returns_rows(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.fetchall() returns all rows."""
        mock_cursor = MagicMock()
        mock_rows = [(1, "alice"), (2, "bob")]
        mock_cursor.fetchall.return_value = mock_rows

        adapter = PostgresAdapter("postgresql://localhost/db")
        result = adapter.fetchall(mock_cursor)

        assert result == mock_rows

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_fetchone_returns_single_row(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.fetchone() returns single row."""
        mock_cursor = MagicMock()
        mock_row = (1, "alice")
        mock_cursor.fetchone.return_value = mock_row

        adapter = PostgresAdapter("postgresql://localhost/db")
        result = adapter.fetchone(mock_cursor)

        assert result == mock_row

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_executemany_bulk_insert(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.executemany() handles bulk operations."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        data = [(1, "a"), (2, "b")]
        result = adapter.executemany(mock_conn, "INSERT INTO test VALUES (%s, %s)", data)

        mock_cursor.executemany.assert_called_once_with(
            "INSERT INTO test VALUES (%s, %s)", data
        )
        assert result == mock_cursor

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_commit_calls_connection_commit(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter.commit() calls connection.commit()."""
        mock_conn = MagicMock()

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.commit(mock_conn)

        mock_conn.commit.assert_called_once()

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_rollback_calls_connection_rollback(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter.rollback() calls connection.rollback()."""
        mock_conn = MagicMock()

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.rollback(mock_conn)

        mock_conn.rollback.assert_called_once()

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_close_is_noop(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.close() is no-op (connection returned to pool)."""
        mock_conn = MagicMock()

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.close(mock_conn)

        # Should not raise, and not call any connection methods
        mock_conn.close.assert_not_called()


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestAdapterEdgeCases:
    """Test edge cases and cross-adapter behavior."""

    def test_sqlite_adapter_empty_parameter_list(self):
        """SQLiteAdapter handles execute with empty params tuple."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER)")
            cursor = adapter.execute(conn, "SELECT 1")
            row = adapter.fetchone(cursor)

        assert row is not None

        adapter.disconnect()

    def test_sqlite_adapter_handles_none_values(self):
        """SQLiteAdapter correctly handles NULL values in results."""
        adapter = SQLiteAdapter(":memory:")
        adapter.connect()

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "CREATE TABLE test (id INTEGER, name TEXT)")
            cursor = adapter.execute(conn, "INSERT INTO test (id, name) VALUES (1, NULL)")

        with adapter.get_connection() as conn:
            cursor = adapter.execute(conn, "SELECT * FROM test")
            row = adapter.fetchone(cursor)

        assert row["id"] == 1
        assert row["name"] is None

        adapter.disconnect()

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_adapter_empty_parameter_list(
        self, mock_psycopg, mock_pool_class
    ):
        """PostgresAdapter handles execute with empty params tuple."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db")
        adapter.connect()

        result = adapter.execute(mock_conn, "SELECT 1")

        # Should call execute with empty params tuple
        mock_cursor.execute.assert_called_once_with("SELECT 1", ())

    def test_factory_with_none_db_type_uses_config(self):
        """Factory uses Config.DB_TYPE when db_type=None."""
        with patch("backend.config.Config") as mock_config:
            mock_config.DB_TYPE = "sqlite"
            mock_config.DB_PATH = ":memory:"

            adapter = get_db_adapter(None)

            assert isinstance(adapter, SQLiteAdapter)

    @patch("backend.adapters.postgres_adapter.SimpleConnectionPool")
    @patch("backend.adapters.postgres_adapter.psycopg")
    def test_postgres_pool_size_honored(self, mock_psycopg, mock_pool_class):
        """PostgresAdapter.connect() uses correct pool_size."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        adapter = PostgresAdapter("postgresql://localhost/db", pool_size=50)
        adapter.connect()

        # Verify max_size parameter was passed
        call_args = mock_pool_class.call_args
        assert call_args[1]["max_size"] == 50
