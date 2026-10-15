export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function csrfToken() {
  return document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))?.split('=')[1];
}

export function apiFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
    const token = csrfToken();
    if (token) headers.set('X-CSRFToken', decodeURIComponent(token));
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' });
}
