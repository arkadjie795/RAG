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

export async function streamPublicChatMessage(payload, onChunk, onMetadata) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data: ')) {
        try {
          const parsed = JSON.parse(trimmed.slice(6));
          if (parsed.type === 'token' && onChunk) {
            onChunk(parsed.token);
          } else if (parsed.type === 'metadata' && onMetadata) {
            onMetadata(parsed);
          }
        } catch (e) {
          console.warn('SSE parse error:', e);
        }
      }
    }
  }
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

function buildCleanQuery(params = {}) {
  const cleaned = {};
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null && val !== '' && val !== 'undefined' && val !== 'null') {
      cleaned[key] = val;
    }
  }
  const qs = new URLSearchParams(cleaned).toString();
  return qs ? `?${qs}` : '';
}

export async function getPublications(params = {}) {
  return request(`/api/data/publications${buildCleanQuery(params)}`);
}

export async function getPublicationTables(docId) {
  return request(`/api/data/publication/${encodeURIComponent(docId)}/tables`);
}

export async function verifyPublication(docId) {
  return request(`/api/data/publication/${encodeURIComponent(docId)}/verify`);
}

export async function getStatisticalTables(params = {}) {
  return request(`/api/data/tables${buildCleanQuery(params)}`);
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
