export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function csrfToken() {
  return document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))?.split('=')[1];
}

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers);

  // 1. Attach Clerk session JWT if user is signed in
  if (typeof window !== 'undefined' && window.Clerk?.session) {
    try {
      const clerkToken = await window.Clerk.session.getToken();
      if (clerkToken) {
        headers.set('Authorization', `Bearer ${clerkToken}`);
      }
    } catch (err) {
      console.warn('Failed to retrieve Clerk token:', err);
    }
  }

  // 2. Retain CSRF token for Django non-GET requests
  if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
    const token = csrfToken();
    if (token) headers.set('X-CSRFToken', decodeURIComponent(token));
  }

  return fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' });
}

