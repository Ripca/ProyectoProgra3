"""
Database Manager for UMG Biometric System
Handles database connections and query execution
"""
import mysql.connector
from mysql.connector import pooling, Error
from contextlib import contextmanager
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections with connection pooling"""
    
    _pool = None
    
    @classmethod
    def initialize_pool(cls, pool_size=5):
        """Initialize connection pool"""
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="umg_pool",
                    pool_size=pool_size,
                    **Config.DB_CONFIG
                )
                logger.info("Database connection pool initialized")
            except Error as e:
                logger.error(f"Error creating connection pool: {e}")
                raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool"""
        if cls._pool is None:
            cls.initialize_pool()
        
        connection = None
        try:
            connection = cls._pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @classmethod
    def execute_query(cls, query, params=None, fetch=True):
        """
        Execute a query and return results
        
        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch: Whether to fetch results (False for INSERT/UPDATE/DELETE)
        
        Returns:
            List of rows for SELECT queries, or affected row count for others
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params or ())
                
                if fetch:
                    results = cursor.fetchall()
                    return results
                else:
                    conn.commit()
                    return cursor.rowcount
                    
            except Error as e:
                conn.rollback()
                logger.error(f"Query execution error: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def execute_insert(cls, query, params=None):
        """
        Execute INSERT query and return the last inserted ID
        
        Args:
            query: INSERT SQL query
            params: Query parameters
        
        Returns:
            Last inserted ID
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid
            except Error as e:
                conn.rollback()
                logger.error(f"Insert error: {e}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def execute_many(cls, query, params_list):
        """
        Execute multiple queries with different parameters
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        
        Returns:
            Number of affected rows
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
            except Error as e:
                conn.rollback()
                logger.error(f"Batch execution error: {e}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def test_connection(cls):
        """Test database connection"""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                logger.info("Database connection test successful")
                return True
        except Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False
