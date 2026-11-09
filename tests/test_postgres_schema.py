import pytest
from config.database import get_db_connection
from modules.storage.postgres_migrator import PostgresMigrator

def test_postgres_tables_exist():
    migrator = PostgresMigrator()
    migrator.run_migrations()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN 
                ('publications', 'statistical_tables', 'vector_chunks', 'embedding_cache');
            """)
            tables = [r[0] for r in cur.fetchall()]
            assert "publications" in tables
            assert "statistical_tables" in tables
            assert "vector_chunks" in tables
            assert "embedding_cache" in tables
