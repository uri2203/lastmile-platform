/**
 * @module auth
 * @description Authentication utilities using expo-secure-store.
 * Manages JWT tokens, refresh tokens, and user data persistence.
 */

import * as SecureStore from 'expo-secure-store';

/** @type {string} Key for storing the JWT access token. */
export const TOKEN_KEY = 'lastmile_token';

/** @type {string} Key for storing the refresh token. */
export const REFRESH_TOKEN_KEY = 'lastmile_refresh_token';

/** @type {string} Key for storing serialized user data. */
export const USER_KEY = 'lastmile_user';

/**
 * @typedef {Object} UserData
 * @property {string|number} emp_id - Employee ID.
 * @property {string} nombre - User's full name.
 * @property {string} email - User's email address.
 * @property {string} rol - User's role (e.g., 'repartidor', 'admin').
 */

/**
 * Stores the JWT access token.
 * @param {string} token - The JWT token to store.
 * @returns {Promise<void>}
 */
export async function setToken(token) {
  if (!token) throw new Error('Token is required');
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

/**
 * Retrieves the stored JWT access token.
 * @returns {Promise<string|null>} The stored token or null.
 */
export async function getToken() {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

/**
 * Stores the refresh token.
 * @param {string} refreshToken - The refresh token to store.
 * @returns {Promise<void>}
 */
export async function setRefreshToken(refreshToken) {
  if (!refreshToken) throw new Error('Refresh token is required');
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * Retrieves the stored refresh token.
 * @returns {Promise<string|null>} The stored refresh token or null.
 */
export async function getRefreshToken() {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

/**
 * Stores user data as serialized JSON.
 * @param {UserData} userData - The user data to store.
 * @returns {Promise<void>}
 */
export async function setUserData(userData) {
  if (!userData) throw new Error('User data is required');
  await SecureStore.setItemAsync(USER_KEY, JSON.stringify(userData));
}

/**
 * Retrieves and parses stored user data.
 * @returns {Promise<UserData|null>} The user data or null.
 */
export async function getUserData() {
  const raw = await SecureStore.getItemAsync(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * Checks if the user is authenticated (has both token and user data).
 * @returns {Promise<boolean>}
 */
export async function isAuthenticated() {
  const token = await getToken();
  const user = await getUserData();
  return !!(token && user);
}

/**
 * Clears all stored authentication data (token, refresh token, user).
 * @returns {Promise<void>}
 */
export async function logout() {
  await Promise.all([
    SecureStore.deleteItemAsync(TOKEN_KEY),
    SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY),
    SecureStore.deleteItemAsync(USER_KEY),
  ]);
}

export default {
  TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  USER_KEY,
  setToken,
  getToken,
  setRefreshToken,
  getRefreshToken,
  setUserData,
  getUserData,
  isAuthenticated,
  logout,
};
