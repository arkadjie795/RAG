"""
Conversation Memory Module for Multi-Turn Chatbot Interactions.
Maintains session histories in PostgreSQL (with graceful in-memory fallback),
manages context sliding window, and formats dialogue for LLM.
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger

from chatbot.config import bot_config
from config.settings import settings


class ChatSession:
    """Represents a single conversational session with message history backed by PostgreSQL."""

    def __init__(self, session_id: str, max_turns: int = bot_config.MAX_HISTORY_TURNS):
        self.session_id = session_id
        self.max_turns = max_turns
        self.history: List[Dict[str, Any]] = []
        self._load_from_db()

    def _get_db_conn(self):
        try:
            import psycopg2
            return psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                dbname=settings.DB_DATABASE,
                user=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
                connect_timeout=3
            )
        except Exception as e:
            logger.debug(f"[ChatSession] DB connection skipped/unavailable: {e}")
            return None

    def _load_from_db(self) -> None:
        """Loads recent message history from PostgreSQL if available."""
        conn = self._get_db_conn()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content, citations, created_at 
                    FROM chat_messages 
                    WHERE session_id = %s 
                    ORDER BY created_at ASC;
                    """,
                    (self.session_id,)
                )
                rows = cur.fetchall()
                for role, content, citations, created_at in rows:
                    self.history.append({
                        "role": role,
                        "content": content,
                        "citations": citations if isinstance(citations, list) else json.loads(citations or "[]"),
                        "timestamp": created_at.isoformat() if created_at else datetime.now().isoformat()
                    })
            self._truncate()
            logger.debug(f"[ChatSession] Loaded {len(self.history)} messages from PostgreSQL for session '{self.session_id}'.")
        except Exception as e:
            logger.warning(f"[ChatSession] Error loading session history from DB: {e}")
        finally:
            conn.close()

    def _persist_message(self, role: str, content: str, citations: Optional[List[Dict[str, Any]]] = None) -> None:
        """Persists a new message to PostgreSQL."""
        conn = self._get_db_conn()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                # Ensure session exists
                cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, updated_at) 
                    VALUES (%s, NOW()) 
                    ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW();
                    """,
                    (self.session_id,)
                )
                # Insert message
                cit_json = json.dumps(citations or [], ensure_ascii=False)
                cur.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content, citations, created_at)
                    VALUES (%s, %s, %s, %s::jsonb, NOW());
                    """,
                    (self.session_id, role, content, cit_json)
                )
            conn.commit()
        except Exception as e:
            logger.warning(f"[ChatSession] Error persisting message to DB: {e}")
        finally:
            conn.close()

    def add_user_message(self, content: str) -> None:
        self.history.append({
            "role": "user",
            "content": content,
            "citations": [],
            "timestamp": datetime.now().isoformat()
        })
        self._truncate()
        self._persist_message("user", content, [])

    def add_assistant_message(self, content: str, citations: Optional[List[Dict[str, Any]]] = None) -> None:
        cits = citations or []
        self.history.append({
            "role": "assistant",
            "content": content,
            "citations": cits,
            "timestamp": datetime.now().isoformat()
        })
        self._truncate()
        self._persist_message("assistant", content, cits)

    def _truncate(self) -> None:
        """Keeps the in-memory history within max_turns * 2 messages."""
        max_messages = self.max_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def format_for_prompt(self) -> str:
        """Formats the history as readable text for the LLM prompt."""
        if not self.history:
            return "(Belum ada riwayat percakapan sebelumnya)"

        formatted = []
        for msg in self.history:
            role = "Pengguna" if msg["role"] == "user" else "Asisten BPS"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)

    def clear(self) -> None:
        """Clears all session messages from memory and PostgreSQL."""
        self.history.clear()
        conn = self._get_db_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM chat_messages WHERE session_id = %s;", (self.session_id,))
                    cur.execute("DELETE FROM chat_sessions WHERE session_id = %s;", (self.session_id,))
                conn.commit()
                logger.info(f"[ChatSession] Cleared DB messages for session '{self.session_id}'.")
            except Exception as e:
                logger.warning(f"[ChatSession] Error clearing DB messages: {e}")
            finally:
                conn.close()


class SessionManager:
    """Manages active chat sessions across multiple users or interaction threads."""

    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create(self, session_id: str = "default") -> ChatSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id=session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            del self._sessions[session_id]
        else:
            # Clear directly from DB
            dummy = ChatSession(session_id=session_id)
            dummy.clear()
