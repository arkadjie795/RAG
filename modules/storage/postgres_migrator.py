"""
Database Migration Runner for BPS RAG3321 PostgreSQL & pgvector Schema.
"""
from pathlib import Path
from loguru import logger
from config.database import get_db_connection


class PostgresMigrator:
    """Manages executing DDL schema migrations idempotently."""

    def __init__(self, schema_file: Path = None):
        self.schema_file = schema_file or Path(__file__).parent / "postgres_schema.sql"

    def run_migrations(self) -> bool:
        """Executes the DDL schema against the configured PostgreSQL database."""
        if not self.schema_file.exists():
            raise FileNotFoundError(f"Schema file not found at {self.schema_file}")

        sql_content = self.schema_file.read_text(encoding="utf-8")
        logger.info(f"[Migrator] Running PostgreSQL migrations from {self.schema_file.name}...")

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_content)
            conn.commit()

        logger.info("[Migrator] Schema migrations completed successfully.")
        return True


if __name__ == "__main__":
    migrator = PostgresMigrator()
    migrator.run_migrations()
