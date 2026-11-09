#!/usr/bin/env bash
# ==============================================================================
# BPS Demak Data Command Center (RAG3321) Dual-Portal Launcher
# ==============================================================================

echo "Menyalakan Backend FastAPI (Port 8000)..."
python3 -m uvicorn chatbot.api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Menyalakan Frontend Vue 3 + Vite (Port 5173)..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo "Portal Publik: http://localhost:5173/"
echo "Portal Admin : http://localhost:5173/admin/"
wait
