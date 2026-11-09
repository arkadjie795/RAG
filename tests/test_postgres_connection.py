import pytest
from config.database import get_db_connection, verify_pgvector_installed

def test_postgres_connection_and_pgvector():
    conn = get_db_connection()
    assert conn is not None
    assert verify_pgvector_installed(conn) is True
    conn.close()
