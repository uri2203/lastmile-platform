/**
 * @module hooks/useAuth
 * @description Authentication hook providing user state, login, logout, and token management.
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

export default function useAuth() {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  async function loadStoredAuth() {
    try {
      const storedToken = await getToken();
      const storedUser = await getUserData();
      if (storedToken && storedUser) {
        setTokenState(storedToken);
        setUser(storedUser);
      }
    } catch (error) {
      console.error('Failed to load stored auth:', error);
    } finally {
      setIsLoading(false);
    }
  }

  const login = useCallback(async (identifier, password) => {
    setIsLoading(true);
    try {
      const response = await post('/api/auth/login', { user: identifier, pass: password }, false);
      if (!response?.success || !response?.token) {
        throw new Error(response?.error || 'Credenciales inválidas');
      }
      const userData = response.data || {};
      await setToken(response.token);
      if (response.refresh_token) await setRefreshToken(response.refresh_token);
      await setUserData(userData);
      setTokenState(response.token);
      setUser(userData);
    } catch (error) {
      setTokenState(null);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await clearAuth();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setTokenState(null);
      setUser(null);
    }
  }, []);

  return {
    user,
    token,
    login,
    logout,
    isLoading,
    isAuthenticated: !!token && !!user,
  };
}
