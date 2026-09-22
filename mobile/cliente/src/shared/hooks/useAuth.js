/**
 * @module hooks/useAuth
 * @description Authentication hook providing user state, login, logout, and token management.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  setToken,
  getToken,
  setRefreshToken,
  getRefreshToken,
  setUserData,
  getUserData,
  isAuthenticated as checkAuth,
  logout as clearAuth,
} from '../auth';
import { post } from '../api';

/**
 * Authentication hook.
 * @returns {{
 *   user: import('../auth').UserData | null,
 *   token: string | null,
 *   login: (email: string, password: string) => Promise<void>,
 *   logout: () => Promise<void>,
 *   isLoading: boolean,
 *   isAuthenticated: boolean
 * }}
 */
export default function useAuth() {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  /**
   * Loads stored authentication data on mount.
   */
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

  /**
   * Authenticates the user with email and password.
   * @param {string} email - User email.
   * @param {string} password - User password.
   * @throws {Error} On authentication failure.
   */
  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    try {
      const response = await post('/api/auth/login', { email, password }, false);
      const { accessToken, refreshToken, user: userData } = response;

      await setToken(accessToken);
      if (refreshToken) await setRefreshToken(refreshToken);
      await setUserData(userData);

      setTokenState(accessToken);
      setUser(userData);
    } catch (error) {
      setTokenState(null);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Clears all stored authentication data and resets state.
   */
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
