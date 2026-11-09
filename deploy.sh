#!/usr/bin/env bash
# ==============================================================================
# Sahabat Data BPS Demak (RAG3321) - Production Deployment Script
# Multi-Stage Docker Container Launcher (FastAPI + Vue 3 Light Mode)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo -e "${CYAN}==============================================================================${NC}"
echo -e "${CYAN}📊 SAHABAT DATA BPS KABUPATEN DEMAK (3321) - DOCKER DEPLOYMENT${NC}"
echo -e "${CYAN}==============================================================================${NC}"

# 1. Pastikan file .env tersedia
if [ ! -f .env ]; then
    echo -e "${YELLOW}[!] File .env tidak ditemukan. Menyalin dari .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}[!] Silakan edit .env untuk memasukkan GEMINI_API_KEY Anda jika belum terisi.${NC}"
fi

# Muat variabel environment
set -a
source .env 2>/dev/null || true
set +a

APP_PORT="${APP_PORT:-8001}"

# 2. Pastikan direktori volume persisten ada
mkdir -p data_publikasi database logs

# 3. Build & Jalankan Container
echo -e "${BLUE}[1/3] Menjalankan Docker Compose Build & Up...${NC}"
docker compose up -d --build

# 4. Tunggu inisialisasi container
echo -e "${BLUE}[2/3] Menunggu inisialisasi service dan model AI (5 detik)...${NC}"
sleep 5

# 5. Cek Status Container
echo -e "${BLUE}[3/3] Memeriksa status kesehatan container...${NC}"
docker compose ps

echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT BERHASIL! APLIKASI AKTIF PADA:${NC}"
echo -e "   👉 Portal Publik (Chatbot AI) : ${BOLD}http://localhost:${APP_PORT}/${NC}"
echo -e "   👉 Portal Admin Command Center: ${BOLD}http://localhost:${APP_PORT}/admin/${NC}"
echo -e "   👉 OpenAPI Swagger Docs       : ${BOLD}http://localhost:${APP_PORT}/docs${NC}"
echo -e "   👉 Database PostgreSQL Aktif  : ${BOLD}10.133.21.24:5433 (bps_rag3321)${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
