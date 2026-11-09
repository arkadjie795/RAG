"""
Authentication and SIPETRA SSO (OAuth2) Router for BPS Demak Admin Portal.
Supports both official SIPETRA SSO and local development mock-login.
"""
import os
import time
import urllib.parse
from typing import Dict, Any, Optional
import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication & SSO"])

# Secret key for simple JWT/bearer token signature
JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "supersecret_jwt_bps_demak_3321")
SIPETRA_CLIENT_ID = os.getenv("SIPETRA_CLIENT_ID", "")
SIPETRA_CLIENT_SECRET = os.getenv("SIPETRA_CLIENT_SECRET", "")
SIPETRA_REDIRECT_URI = os.getenv("SIPETRA_REDIRECT_URI", "http://localhost:8000/api/auth/sipetra/callback")
SIPETRA_BASE_URL = os.getenv("SIPETRA_BASE_URL", "https://bpsdemak.com").rstrip("/")
DEFAULT_SCOPES = "identity_pegawai:read employee:read contact:read roles:read"

# Simple token store for session verification
_ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


class MockLoginRequest(BaseModel):
    username: str
    name: Optional[str] = "Admin BPS Demak"
    nip: Optional[str] = "199001012015011001"
    role: Optional[str] = "admin"


def create_token(user_payload: Dict[str, Any]) -> str:
    """Generates simple signed bearer token for session tracking."""
    token = f"bps_{user_payload.get('username', 'user')}_{int(time.time())}"
    _ACTIVE_SESSIONS[token] = {
        **user_payload,
        "issued_at": time.time()
    }
    return token


def verify_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates token from Authorization header."""
    if not token:
        return None
    clean_token = token.replace("Bearer ", "").strip()
    return _ACTIVE_SESSIONS.get(clean_token)


@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Returns currently authenticated user profile or guest status."""
    user = verify_token(authorization)
    if user:
        return {
            "authenticated": True,
            "user": user
        }
    return {
        "authenticated": False,
        "user": None
    }


@router.post("/mock-login")
def mock_login(req: MockLoginRequest) -> Dict[str, Any]:
    """Provides local development login when SIPETRA SSO credentials are not yet configured."""
    user_payload = {
        "id": "mock_admin_1",
        "username": req.username,
        "name": req.name,
        "nip": req.nip,
        "role": req.role,
        "email": f"{req.username}@bps.go.id",
        "source": "mock_login"
    }
    token = create_token(user_payload)
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": user_payload
    }


@router.get("/sipetra/redirect")
def sipetra_redirect(client_redirect: Optional[str] = None):
    """
    Builds SIPETRA OAuth2 authorization URL and redirects user.
    If called via API, returns auth_url. If in browser navigation, performs 302 redirect.
    """
    state = f"state_{int(time.time())}"
    params = {
        "client_id": SIPETRA_CLIENT_ID or "unconfigured_client_id",
        "redirect_uri": SIPETRA_REDIRECT_URI,
        "response_type": "code",
        "scope": DEFAULT_SCOPES,
        "state": state
    }
    query_str = urllib.parse.urlencode(params)
    auth_url = f"{SIPETRA_BASE_URL}/oauth/authorize?{query_str}"

    return {
        "status": "success",
        "auth_url": auth_url,
        "client_id": SIPETRA_CLIENT_ID or "BELUM_DIKONFIGURASI",
        "redirect_uri": SIPETRA_REDIRECT_URI
    }


@router.get("/sipetra/callback")
def sipetra_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Handles OAuth2 callback from SIPETRA (bpsdemak.com).
    Exchanges code for access token, fetches employee profile, and redirects to frontend.
    """
    if error or not code:
        frontend_error_url = "http://localhost:5173/admin/login?error=sso_cancelled"
        return RedirectResponse(url=frontend_error_url)

    try:
        # 1. Exchange code for access token
        token_url = f"{SIPETRA_BASE_URL}/oauth/token"
        token_payload = {
            "grant_type": "authorization_code",
            "client_id": SIPETRA_CLIENT_ID,
            "client_secret": SIPETRA_CLIENT_SECRET,
            "redirect_uri": SIPETRA_REDIRECT_URI,
            "code": code
        }
        with httpx.Client(timeout=15.0) as client:
            token_resp = client.post(token_url, json=token_payload)
            token_data = token_resp.json()
            access_token = token_data.get("access_token")

            if not access_token:
                frontend_err = f"http://localhost:5173/admin/login?error=token_exchange_failed"
                return RedirectResponse(url=frontend_err)

            # 2. Fetch user profile from SIPETRA API
            user_url = f"{SIPETRA_BASE_URL}/api/user"
            user_resp = client.get(
                user_url,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            )
            sso_user = user_resp.json()

        # 3. Create local session token
        local_user = {
            "id": sso_user.get("id"),
            "username": sso_user.get("email") or sso_user.get("name"),
            "name": sso_user.get("name"),
            "email": sso_user.get("email"),
            "nip": sso_user.get("nip"),
            "jabatan": sso_user.get("jabatan"),
            "avatar": sso_user.get("avatar"),
            "source": "sipetra_sso"
        }
        session_token = create_token(local_user)

        # 4. Redirect to Frontend Admin Dashboard
        frontend_dest = f"http://localhost:5173/admin/ingestion?token={session_token}"
        return RedirectResponse(url=frontend_dest)

    except Exception as ex:
        err_url = f"http://localhost:5173/admin/login?error=sso_exception"
        return RedirectResponse(url=err_url)


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Clears active session token."""
    if authorization:
        clean_token = authorization.replace("Bearer ", "").strip()
        _ACTIVE_SESSIONS.pop(clean_token, None)
    return {"status": "success", "message": "Berhasil logout dari sistem"}
