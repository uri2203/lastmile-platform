import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

const BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl || 'https://lastmile-platform.onrender.com';

const TOKEN_KEY = 'lastmile_chofer_token';

export async function getToken() {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function setToken(token) {
  if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
  else await SecureStore.deleteItemAsync(TOKEN_KEY);
}

const REQUEST_TIMEOUT_MS = 15000;

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  let res;
  // Sin esto, un backend lento (p.ej. Render "despertando" de cold start) o
  // una red que nunca falla del todo pero tampoco responde deja el fetch
  // colgado sin limite -- eso es lo que se vio como "pantalla en blanco
  // 10 minutos" al arrancar (login/perfil sin timeout).
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (e) {
    const err = new Error('network');
    err.code = 'NETWORK';
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  let json;
  try {
    json = await res.json();
  } catch (e) {
    const err = new Error(`server (${res.status})`);
    err.code = 'SERVER';
    throw err;
  }
  if (res.status === 401) {
    await setToken(null);
    const err = new Error('session expired');
    err.code = 'SESSION_EXPIRED';
    throw err;
  }
  if (!res.ok && !json.success) {
    // json.error viene del backend en texto plano (no i18n); se muestra tal
    // cual cuando existe, ya que traducirlo requeriria mapear cada mensaje.
    const err = new Error(json.error || `server (${res.status})`);
    err.code = json.error ? 'BACKEND' : 'SERVER';
    throw err;
  }
  return json;
}

export const api = {
  // Auth. Contrato real del backend: POST /api/auth/login {user, pass}.
  login: (user, pass) => request('/api/auth/login', { method: 'POST', body: { user, pass }, auth: false }),

  // Perfil de chofer vinculado al usuario logueado (GET /api/choferes/me).
  getMyProfile: () => request('/api/choferes/me'),

  // Entregas asignadas a un chofer.
  getMyDeliveries: (choId) => request(`/api/entregas/chofer/${choId}`),

  // Marcar entrega completada o fallida (PUT /api/entregas/<id>).
  markDelivered: (entId, evidencia) =>
    request(`/api/entregas/${entId}`, {
      method: 'PUT',
      body: { estado: 'ENTREGADO', hora: new Date().toISOString(), evidencia },
    }),
  markFailed: (entId, motivo) =>
    request(`/api/entregas/${entId}`, { method: 'PUT', body: { estado: 'NO_ENTREGADO', motivo } }),

  // Reportar posicion GPS (POST /api/tracking).
  reportLocation: (choId, latitud, longitud, velocidad = 0) =>
    request('/api/tracking', { method: 'POST', body: { choId, latitud, longitud, velocidad } }),

  // Cobro en efectivo (COD) de un pedido.
  collectCash: (pedId, monto, notas) =>
    request(`/api/pedidos/${pedId}/collect-cash`, { method: 'POST', body: { monto, notas } }),

  // Rendimiento del chofer (para la pantalla de estadisticas).
  getRendimiento: () => request('/api/choferes/rendimiento'),
};

export { BASE_URL };
