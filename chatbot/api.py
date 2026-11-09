"""
API and Web Integration Module for BPS AI Chatbot.
Provides lightweight interface ready for FastAPI, Flask, Streamlit, or webhook bots.
"""
from typing import Dict, Any, Optional
from chatbot.bot import BPSChatbot

# Global singleton chatbot instance for API serving
_global_bot: Optional[BPSChatbot] = None


def get_chatbot() -> BPSChatbot:
    """Returns singleton instance of BPSChatbot."""
    global _global_bot
    if _global_bot is None:
        _global_bot = BPSChatbot()
    return _global_bot


def handle_chat_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standard request handler suitable for any web framework or message webhook.

    Expected payload:
    {
        "message": "Berapa jumlah penduduk di Demak tahun 2024?",
        "session_id": "optional_user_id",
        "daerah": "optional_override",
        "tahun": "optional_year",
        "kategori": "optional_category",
        "top_k": 4
    }
    """
    bot = get_chatbot()
    message = payload.get("message", "")
    session_id = payload.get("session_id", "default")
    daerah = payload.get("daerah")
    tahun = payload.get("tahun")
    kategori = payload.get("kategori")
    top_k = payload.get("top_k")

    result = bot.ask(
        question=message,
        session_id=session_id,
        daerah=daerah,
        tahun=tahun,
        kategori=kategori,
        top_k=top_k
    )

    return {
        "status": "success",
        "data": {
            "answer": result["answer"],
            "citations": result["citations"],
            "session_id": result["session_id"],
            "total_references": len(result["citations"])
        }
    }


# Optional FastAPI application if installed
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    # Import Modular Routers
    from api.routers.auth import router as auth_router
    from api.routers.ingestion import router as ingestion_router
    from api.routers.data_viewer import router as data_viewer_router
    from api.routers.system_telemetry import router as system_telemetry_router

    app = FastAPI(
        title="BPS Demak Command Center & AI Assistant API",
        description="Unified Enterprise Backend for Sahabat Data BPS Demak (3321)",
        version="2.0.0"
    )

    # Allow CORS for Frontend development & local serving
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Sub-Routers
    app.include_router(auth_router)
    app.include_router(ingestion_router)
    app.include_router(data_viewer_router)
    app.include_router(system_telemetry_router)

    # Top-level callback alias for SIPETRA OAuth2 (/auth/callback)
    @app.get("/auth/callback")
    def top_level_auth_callback(
        code: Optional[str] = None,
        state: Optional[str] = None,
        error: Optional[str] = None
    ):
        from api.routers.auth import sipetra_callback
        return sipetra_callback(code=code, state=state, error=error)

    class ChatRequest(BaseModel):
        message: str
        session_id: Optional[str] = "default"
        daerah: Optional[str] = None
        tahun: Optional[str] = None
        kategori: Optional[str] = None
        top_k: Optional[int] = 4

    @app.post("/api/chat")
    def api_chat(req: ChatRequest):
        res = handle_chat_request(req.model_dump())
        return res

    @app.delete("/api/session/{session_id}")
    def api_clear_session(session_id: str):
        bot = get_chatbot()
        bot.clear_memory(session_id)
        return {"status": "success", "message": f"Session '{session_id}' cleared"}

    @app.get("/api/health")
    def api_health():
        return {"status": "healthy", "service": "BPS Chatbot RAG Engine"}

    # Mount production Vue 3 static build if frontend/dist/index.html exists
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse

    DIST_INDEX_PATH = "frontend/dist/index.html"
    DIST_ASSETS_DIR = "frontend/dist/assets"

    if os.path.exists(DIST_INDEX_PATH):
        if os.path.exists(DIST_ASSETS_DIR):
            app.mount("/assets", StaticFiles(directory=DIST_ASSETS_DIR), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Endpoint API tidak ditemukan")

            file_path = os.path.join("frontend/dist", full_path)
            if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)

            if os.path.exists(DIST_INDEX_PATH):
                return FileResponse(
                    DIST_INDEX_PATH,
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
                )
            return HTMLResponse(
                "<h3>Sahabat Data BPS Frontend Not Found</h3><p>Jalankan build frontend.</p>",
                status_code=503
            )

except ImportError:
    app = None
