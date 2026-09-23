/**
 * @module api
 * @description Professional API client for Last Mile Delivery Platform.
 * Features: JWT management, auto-refresh, interceptors, timeout, network error handling.
 * @baseURL https://lastmile-platform.onrender.com
 */

import * as SecureStore from 'expo-secure-store';
import { TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from './auth';

const BASE_URL = 'https://lastmile-platform.onrender.com';
const TIMEOUT_MS = 30000;

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function buildHeaders(authenticated = true) {
  const headers = { 'Content-Type': 'application/json' };
  if (authenticated) {
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

async function refreshAccessToken() {
  const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
  if (!refreshToken) throw new ApiError('No refresh token available', 401);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(`${BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
      await SecureStore.deleteItemAsync(USER_KEY);
      throw new ApiError('Session expired', 401);
    }

    const data = await response.json();
    if (!data?.success || !data?.token) {
      throw new ApiError('Session expired', 401);
    }
    await SecureStore.setItemAsync(TOKEN_KEY, data.token);
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) throw error;
    throw new ApiError('Session expired', 401);
  }
}

async function request(endpoint, options = {}, authenticated = true, retryOn401 = true) {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;
  const headers = await buildHeaders(authenticated);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      headers: { ...headers, ...options.headers },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401 && retryOn401) {
      try {
        await refreshAccessToken();
        return await request(endpoint, options, authenticated, false);
      } catch {
        throw new ApiError('Unauthorized', 401);
      }
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = null;
      }
      throw new ApiError(
        errorData?.error || errorData?.message || `Request failed with status ${response.status}`,
        response.status,
        errorData
      );
    }

    if (response.status === 204) return null;
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) throw error;
    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out', 408);
    }
    throw new ApiError('Network error. Please check your connection.', 0);
  }
}

export async function get(endpoint, params = {}, authenticated = true) {
  const filtered = {};
  Object.keys(params || {}).forEach((k) => {
    if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
      filtered[k] = params[k];
    }
  });
  const queryString = Object.keys(filtered).length
    ? '?' + new URLSearchParams(filtered).toString()
    : '';
  return request(`${endpoint}${queryString}`, { method: 'GET' }, authenticated);
}

export async function post(endpoint, body = null, authenticated = true) {
  return request(
    endpoint,
    { method: 'POST', body: body ? JSON.stringify(body) : undefined },
    authenticated
  );
}

export async function put(endpoint, body = null, authenticated = true) {
  return request(
    endpoint,
    { method: 'PUT', body: body ? JSON.stringify(body) : undefined },
    authenticated
  );
}

export async function del(endpoint, authenticated = true) {
  return request(endpoint, { method: 'DELETE' }, authenticated);
}

export default { get, post, put, del, ApiError, BASE_URL };
