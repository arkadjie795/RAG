/**
 * Centralized API Client for BPS Demak Portal (Public & Admin).
 * Automatically injects Bearer token for admin operations and handles CORS/proxies.
 */

const TOKEN_KEY = 'bps_admin_token';
const USER_KEY = 'bps_admin_user';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function setAuthSession(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getCachedUser() {
  const raw = localStorage.getItem(USER_KEY);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function request(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(endpoint, {
    ...options,
    headers
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail || errorBody.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// ==========================================
// PUBLIC CHAT API
// ==========================================

export async function sendPublicChatMessage(payload) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

// ==========================================
// AUTH & SIPETRA SSO API
// ==========================================

export async function checkAuthStatus() {
  return request('/api/auth/me');
}

export async function loginMockAdmin(username = 'admin_bps') {
  const res = await request('/api/auth/mock-login', {
    method: 'POST',
    body: JSON.stringify({ username })
  });
  if (res.access_token) {
    setAuthSession(res.access_token, res.user);
  }
  return res;
}

export async function getSipetraRedirectInfo() {
  return request('/api/auth/sipetra/redirect');
}

export async function logoutAdmin() {
  try {
    await request('/api/auth/logout', { method: 'POST' });
  } finally {
    clearAuthSession();
  }
}

// ==========================================
// INGESTION & SCRAPER HUB API
// ==========================================

export async function getIngestionStatus() {
  return request('/api/ingestion/status');
}

export async function triggerIngestionRun(mode = 'statis', maxPages = 2, pdfPath = null) {
  return request('/api/ingestion/run', {
    method: 'POST',
    body: JSON.stringify({ mode, max_pages: maxPages, pdf_path: pdfPath })
  });
}

export async function stopIngestionRun() {
  return request('/api/ingestion/stop', { method: 'POST' });
}

// ==========================================
// DATA EXPLORER & PROOF OF DATA API
// ==========================================

export async function getPublications(params = {}) {
  const query = new URLSearchParams(params).toString();
  return request(`/api/data/publications${query ? '?' + query : ''}`);
}

export async function getStatisticalTables(params = {}) {
  const query = new URLSearchParams(params).toString();
  return request(`/api/data/tables${query ? '?' + query : ''}`);
}

export async function getTableDetail(tableId) {
  return request(`/api/data/table/${encodeURIComponent(tableId)}`);
}

// ==========================================
// SYSTEM TELEMETRY & OBSERVABILITY API
// ==========================================

export async function getSystemHealth() {
  return request('/api/system/health');
}

export async function getVectorStats() {
  return request('/api/system/vector-stats');
}

export async function runSearchPlayground(query, daerah = null, tahun = null, topK = 4) {
  return request('/api/system/test-search', {
    method: 'POST',
    body: JSON.stringify({ query, daerah, tahun, top_k: topK })
  });
}

export async function getRecentLogs(lines = 60) {
  return request(`/api/system/logs?lines=${lines}`);
}
