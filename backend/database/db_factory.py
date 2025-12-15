"""Database factory and connection abstractions for Ignisyl"""
import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional, Dict
from pathlib import Path
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


class DatabaseConnection(ABC):
    """Abstract base class for database connections"""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute a query that modifies data (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries

        Returns:
            Result of the query execution
        """
        pass

    @abstractmethod
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query multiple times with different parameters

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        pass

    @abstractmethod
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Fetch a single row from the database

        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries

        Returns:
            Single row as tuple or None
        """
        pass

    @abstractmethod
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Fetch all rows from the database

        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries

        Returns:
            List of rows as tuples
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit current transaction"""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback current transaction"""
        pass

    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            logger.error(f"Transaction failed: {e}")
            raise


class SQLiteConnection(DatabaseConnection):
    """SQLite database connection implementation"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize SQLite connection

        Args:
            config: Configuration dictionary with 'path' key
        """
        self.db_path = config.get('path', 'data/ignisyl.db')
        self.connection = None
        self.cursor = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        """Establish SQLite connection"""
        try:
            # Ensure directory exists
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to SQLite database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute a query that modifies data"""
        with self._lock:
            try:
                if params:
                    result = self.cursor.execute(query, params)
                else:
                    result = self.cursor.execute(query)
                self.connection.commit()
                return result
            except sqlite3.Error as e:
                logger.error(f"Query execution failed: {e}\nQuery: {query}\nParams: {params}")
                self.connection.rollback()
                raise

    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query multiple times with different parameters"""
        with self._lock:
            try:
                self.cursor.executemany(query, params_list)
                self.connection.commit()
            except sqlite3.Error as e:
                logger.error(f"Batch execution failed: {e}\nQuery: {query}")
                self.connection.rollback()
                raise

    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Fetch a single row from the database"""
        with self._lock:
            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                return self.cursor.fetchone()
            except sqlite3.Error as e:
                logger.error(f"Fetch one failed: {e}\nQuery: {query}\nParams: {params}")
                raise

    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Fetch all rows from the database"""
        with self._lock:
            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                return self.cursor.fetchall()
            except sqlite3.Error as e:
                logger.error(f"Fetch all failed: {e}\nQuery: {query}\nParams: {params}")
                raise

    def commit(self) -> None:
        """Commit current transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """Rollback current transaction"""
        if self.connection:
            self.connection.rollback()

    def close(self) -> None:
        """Close SQLite connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("SQLite connection closed")


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL database connection implementation"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize PostgreSQL connection

        Args:
            config: Configuration dictionary with host, port, database, user, password
        """
        self.config = config
        self.connection = None
        self.cursor = None
        self._pool = None

    def connect(self) -> None:
        """Establish PostgreSQL connection with connection pooling"""
        try:
            import psycopg2
            from psycopg2 import pool

            # Create connection pool for production use
            self._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database', 'ignisyl'),
                user=self.config.get('user', 'ignisyl_user'),
                password=self.config.get('password', ''),
                connect_timeout=10
            )

            # Get a connection from pool
            self.connection = self._pool.getconn()
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to PostgreSQL database: {self.config.get('database')}")
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL database: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute a query that modifies data"""
        try:
            if params:
                result = self.cursor.execute(query, params)
            else:
                result = self.cursor.execute(query)
            self.connection.commit()
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}\nParams: {params}")
            self.connection.rollback()
            raise

    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query multiple times with different parameters"""
        try:
            self.cursor.executemany(query, params_list)
            self.connection.commit()
        except Exception as e:
            logger.error(f"Batch execution failed: {e}\nQuery: {query}")
            self.connection.rollback()
            raise

    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Fetch a single row from the database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Fetch one failed: {e}\nQuery: {query}\nParams: {params}")
            raise

    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Fetch all rows from the database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Fetch all failed: {e}\nQuery: {query}\nParams: {params}")
            raise

    def commit(self) -> None:
        """Commit current transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """Rollback current transaction"""
        if self.connection:
            self.connection.rollback()

    def close(self) -> None:
        """Close PostgreSQL connection and return to pool"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self._pool:
            self._pool.putconn(self.connection)
            logger.info("PostgreSQL connection returned to pool")
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL connection pool closed")


class MySQLConnection(DatabaseConnection):
    """MySQL database connection implementation"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize MySQL connection

        Args:
            config: Configuration dictionary with host, port, database, user, password
        """
        self.config = config
        self.connection = None
        self.cursor = None
        self._pool = None

    def connect(self) -> None:
        """Establish MySQL connection with connection pooling"""
        try:
            import mysql.connector
            from mysql.connector import pooling

            # Create connection pool for production use
            pool_config = {
                'pool_name': 'ignisyl_pool',
                'pool_size': 10,
                'host': self.config.get('host', 'localhost'),
                'port': self.config.get('port', 3306),
                'database': self.config.get('database', 'ignisyl'),
                'user': self.config.get('user', 'ignisyl_user'),
                'password': self.config.get('password', ''),
                'connect_timeout': 10
            }

            self._pool = pooling.MySQLConnectionPool(**pool_config)
            self.connection = self._pool.get_connection()
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to MySQL database: {self.config.get('database')}")
        except ImportError:
            logger.error("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MySQL database: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute a query that modifies data"""
        try:
            if params:
                result = self.cursor.execute(query, params)
            else:
                result = self.cursor.execute(query)
            self.connection.commit()
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}\nParams: {params}")
            self.connection.rollback()
            raise

    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query multiple times with different parameters"""
        try:
            self.cursor.executemany(query, params_list)
            self.connection.commit()
        except Exception as e:
            logger.error(f"Batch execution failed: {e}\nQuery: {query}")
            self.connection.rollback()
            raise

    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Fetch a single row from the database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Fetch one failed: {e}\nQuery: {query}\nParams: {params}")
            raise

    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Fetch all rows from the database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Fetch all failed: {e}\nQuery: {query}\nParams: {params}")
            raise

    def commit(self) -> None:
        """Commit current transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """Rollback current transaction"""
        if self.connection:
            self.connection.rollback()

    def close(self) -> None:
        """Close MySQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("MySQL connection closed")


class DatabaseFactory:
    """Factory class for creating database connections"""

    @staticmethod
    def get_database(config: Dict[str, Any]) -> DatabaseConnection:
        """Get appropriate database connection based on configuration

        Args:
            config: Configuration dictionary with 'type' key and db-specific settings

        Returns:
            DatabaseConnection instance

        Raises:
            ValueError: If database type is not supported
        """
        db_type = config.get('type', 'sqlite').lower()

        if db_type == 'sqlite':
            db = SQLiteConnection(config)
        elif db_type == 'postgresql' or db_type == 'postgres':
            db = PostgreSQLConnection(config)
        elif db_type == 'mysql':
            db = MySQLConnection(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        db.connect()
        return db

    @staticmethod
    def get_database_from_env(environment: str = 'development') -> DatabaseConnection:
        """Get database connection based on environment

        Args:
            environment: Environment name ('development', 'production', etc.)

        Returns:
            DatabaseConnection instance
        """
        from backend.config.database_config import DATABASE_CONFIG

        if environment not in DATABASE_CONFIG:
            raise ValueError(f"Unknown environment: {environment}")

        config = DATABASE_CONFIG[environment]
        return DatabaseFactory.get_database(config)
