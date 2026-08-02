/**
 * VisionX — API Client Utility
 * Centralized API calls to FastAPI backend
 */

// Same-origin by default. In dev the Vite proxy forwards /api → the backend;
// in production nginx does the same. Hardcoding http://localhost:8000 here
// bypassed both and broke as soon as the app was served from anywhere else.
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    try {
      const auth = JSON.parse(localStorage.getItem('vx-auth') || '{}');
      return auth?.state?.token || null;
    } catch {
      return null;
    }
  }

  async request<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, signal } = options;
    const token = this.getToken();

    const config: RequestInit = {
      method,
      signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    };

    if (body && method !== 'GET') {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  get<T = any>(endpoint: string, signal?: AbortSignal) {
    return this.request<T>(endpoint, { signal });
  }

  post<T = any>(endpoint: string, body?: any) {
    return this.request<T>(endpoint, { method: 'POST', body });
  }

  put<T = any>(endpoint: string, body?: any) {
    return this.request<T>(endpoint, { method: 'PUT', body });
  }

  patch<T = any>(endpoint: string, body?: any) {
    return this.request<T>(endpoint, { method: 'PATCH', body });
  }

  delete<T = any>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient(API_BASE);
