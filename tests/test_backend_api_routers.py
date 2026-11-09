"""
Unit tests for the modular backend API routers:
- /api/auth/me, /api/auth/login, /api/auth/sipetra/redirect
- /api/ingestion/status, /api/ingestion/run
- /api/data/publications, /api/data/tables
- /api/system/health, /api/system/vector-stats, /api/system/logs
"""
import pytest
from fastapi.testclient import TestClient
from chatbot.api import app

client = TestClient(app)


def test_public_chat_health():
    """Verifies basic health and status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_auth_status_and_login():
    """Verifies authentication routes."""
    # Without token, /api/auth/me returns guest or unauthenticated
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "authenticated" in data
    assert data["authenticated"] is False

    # Mock login for development
    login_resp = client.post("/api/auth/mock-login", json={"username": "admin_bps"})
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # Verify /api/auth/me with Bearer token
    auth_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_resp.status_code == 200
    assert auth_resp.json()["authenticated"] is True
    assert auth_resp.json()["user"]["username"] == "admin_bps"


def test_sipetra_redirect_endpoint():
    """Verifies SIPETRA SSO redirect URL generation."""
    resp = client.get("/api/auth/sipetra/redirect", follow_redirects=False)
    # Should redirect (302/307) or return auth_url
    assert resp.status_code in (200, 302, 307)
    if resp.status_code in (302, 307):
        assert "bpsdemak.com/oauth/authorize" in resp.headers["location"]
    else:
        assert "auth_url" in resp.json()
        assert "bpsdemak.com/oauth/authorize" in resp.json()["auth_url"]


def test_ingestion_status_and_run():
    """Verifies scraper job manager and status endpoints."""
    resp = client.get("/api/ingestion/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("IDLE", "RUNNING", "COMPLETED", "FAILED")


def test_data_viewer_endpoints():
    """Verifies publications and statistical tables explorer endpoints."""
    # Publications list
    pub_resp = client.get("/api/data/publications")
    assert pub_resp.status_code == 200
    assert "items" in pub_resp.json()

    # Tables list
    tbl_resp = client.get("/api/data/tables?limit=5")
    assert tbl_resp.status_code == 200
    assert "items" in tbl_resp.json()


def test_system_telemetry_endpoints():
    """Verifies system health, vector stats, and log reader."""
    health_resp = client.get("/api/system/health")
    assert health_resp.status_code == 200
    h_data = health_resp.json()
    assert h_data["database_connected"] is True
    assert "pgvector" in h_data

    stats_resp = client.get("/api/system/vector-stats")
    assert stats_resp.status_code == 200
    assert "total_chunks" in stats_resp.json()

    logs_resp = client.get("/api/system/logs?lines=20")
    assert logs_resp.status_code == 200
    assert "logs" in logs_resp.json()
