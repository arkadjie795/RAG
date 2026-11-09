@echo off
TITLE BPS Demak Data Command Center (RAG3321)
COLOR 0B

echo ==============================================================================
echo   SAHABAT DATA BPS KABUPATEN DEMAK (3321) & COMMAND CENTER
echo   Dual-Portal System: Public AI Assistant + Admin Management Hub
echo ==============================================================================
echo.

:: Detect Python
set PYTHON_CMD=python
if exist "C:\laragon\bin\python\python-3.10\python.exe" (
    set "PYTHON_CMD=C:\laragon\bin\python\python-3.10\python.exe"
)

echo [1/3] Menyalakan Backend FastAPI (Port 8000)...
start "BPS Backend FastAPI" cmd /c "%PYTHON_CMD% -m uvicorn chatbot.api:app --host 127.0.0.1 --port 8000"

echo [2/3] Menyalakan Frontend Vue 3 + Vite (Port 5173)...
start "BPS Frontend Vite" cmd /c "cd frontend && npm run dev"

echo [3/3] Menunggu service aktif...
timeout /t 3 /nobreak >nul

echo.
echo ==============================================================================
echo   PORTAL AKTIF:
echo   - Portal Publik (Chatbot):  http://localhost:5173/
echo   - Portal Admin (Monitoring): http://localhost:5173/admin/
echo   - Swagger API Docs:          http://127.0.0.1:8000/docs
echo ==============================================================================
echo.

start http://localhost:5173/
pause
