# ========================================================
# Stage 1: Build Vue 3 + Tailwind CSS Frontend
# ========================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# ========================================================
# Stage 2: Production Python Backend Server
# ========================================================
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Jakarta

# Install system dependencies (build-essential & libpq-dev for psycopg2, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Pre-install lightweight CPU-only PyTorch (prevents downloading 2.5GB CUDA dependencies)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Install remaining Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy Python backend codebase
COPY . .

# 4. Copy compiled Vue 3 frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose unified application port (serves both Public Chat, Admin Hub, and FastAPI endpoints)
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl --fail http://localhost:8000/api/health || exit 1

# Launch FastAPI app (which seamlessly serves the Vue 3 SPA frontend on / and /admin)
CMD ["uvicorn", "chatbot.api:app", "--host", "0.0.0.0", "--port", "8000"]
