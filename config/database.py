"""
PostgreSQL and pgvector Database Connection Manager for BPS RAG3321.
"""
import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from loguru import logger

from config.settings import settings


def get_db_connection(database: str = None) -> PgConnection:
    """
    Returns a connection to the PostgreSQL database with pgvector support.
    """
    dbname = database or settings.DB_DATABASE
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSWORD,
            dbname=dbname,
            connect_timeout=settings.DB_TIMEOUT
        )
        return conn
    except Exception as e:
        logger.error(f"[Database] Failed to connect to PostgreSQL at {settings.DB_HOST}:{settings.DB_PORT}/{dbname}: {e}")
        raise


@contextmanager
def get_db_cursor(database: str = None, commit: bool = False):
    """
    Safe context manager yielding a cursor and always guaranteeing connection closure.
    Prevents PostgreSQL connection leaks in high-frequency FastAPI endpoints.
    """
    conn = get_db_connection(database=database)
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def verify_pgvector_installed(conn: PgConnection) -> bool:
    """
    Checks if pgvector extension is installed and active in the database.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
            row = cur.fetchone()
            return row is not None
    except Exception as e:
        logger.warning(f"[Database] Error checking vector extension: {e}")
        return False
