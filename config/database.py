"""
PostgreSQL and pgvector Database Connection Manager for BPS RAG3321.
"""
import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor
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
