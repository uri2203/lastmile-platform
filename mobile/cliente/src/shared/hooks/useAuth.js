/**
 * @module hooks/useAuth
 * @description Authentication hook providing user state, login, logout, and token management.
 * Auth state is kept in a module-level snapshot shared by every hook instance so that
 * login/logout performed in any screen is immediately reflected app-wide.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  setToken,
  getToken,
  setRefreshToken,
  setUserData,
  getUserData,
  logout as clearAuth,
} from '../auth';
import { post } from '../api';

/** @type {{token: string|null, user: object|null, isLoading: boolean}} */
let snapshot = { token: null, user: null, isLoading: true };
const listeners = new Set();

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emit() {
  listeners.forEach((listener) => listener());
}

export default function useAuth() {
  const [state, setState] = useState(() => ({ ...snapshot }));

  useEffect(() => {
    const unsubscribe = subscribe(() => setState({ ...snapshot }));
    let cancelled = false;

    (async () => {
      try {
        const storedToken = await getToken();
        const storedUser = await getUserData();
        if (cancelled) return;
        snapshot = {
          token: storedToken || null,
          user: storedUser || null,
          isLoading: false,
        };
      } catch (error) {
        console.error('Failed to load stored auth:', error);
        if (cancelled) return;
        snapshot = { token: null, user: null, isLoading: false };
      }
      setState({ ...snapshot });
    })();

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (identifier, password) => {
    try {
      const response = await post('/api/auth/login', { user: identifier, pass: password }, false);
      if (!response?.success || !response?.token) {
        throw new Error(response?.error || 'Credenciales inválidas');
      }
      const userData = response.data || {};
      await setToken(response.token);
      if (response.refresh_token) await setRefreshToken(response.refresh_token);
      await setUserData(userData);
      snapshot = { token: response.token, user: userData, isLoading: false };
      emit();
    } catch (error) {
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await clearAuth();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      snapshot = { token: null, user: null, isLoading: false };
      emit();
    }
  }, []);

  return {
    user: state.user,
    token: state.token,
    login,
    logout,
    isLoading: state.isLoading,
    isAuthenticated: !!state.token && !!state.user,
  };
}
