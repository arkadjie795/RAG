import os
import sys
import psycopg2

sys.path.insert(0, os.path.abspath("."))
from config.settings import settings

def create_chat_tables():
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_DATABASE,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT DEFAULT 'Percakapan Baru',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id SERIAL PRIMARY KEY,
            session_id TEXT REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_chat_msg_session ON chat_messages (session_id, created_at);
    """)
    conn.commit()
    print("Created chat_sessions and chat_messages tables in PostgreSQL successfully!")

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name IN ('chat_sessions', 'chat_messages');")
    print("Tables verified in PostgreSQL:", cur.fetchall())

    cur.close()
    conn.close()

if __name__ == "__main__":
    create_chat_tables()
