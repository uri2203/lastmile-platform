import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api, getToken, setToken, getStoredUser, setStoredUser } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null); // {emp_id, empresa, nombre, rol, usuario}
  const [choferProfile, setChoferProfile] = useState(null); // {CHO_ID, ...}
  const [profileError, setProfileError] = useState(null);

  const loadProfile = useCallback(async () => {
    try {
      const res = await api.getMyProfile();
      setChoferProfile(res.data);
      setProfileError(null);
    } catch (e) {
      setChoferProfile(null);
      setProfileError(e.message);
    }
  }, []);

  useEffect(() => {
    (async () => {
      const [token, storedUser] = await Promise.all([getToken(), getStoredUser()]);
      if (token) {
        // Arranque INSTANTANEO: se muestra la app de una con la sesion guardada
        // y se libera el loading sin esperar ninguna red. El perfil de chofer
        // (getMyProfile) y la validacion real del token se resuelven en segundo
        // plano -- si el token expiro, el primer request da 401 y se limpia.
        setUser(storedUser || { token });
        setLoading(false);
        loadProfile(); // sin await: no bloquea el arranque
      } else {
        setLoading(false);
      }
    })();
  }, [loadProfile]);

  const login = useCallback(async (usuario, pass) => {
    const res = await api.login(usuario, pass);
    if (!res.success || !res.token) {
      const err = new Error(res.error || 'invalid credentials');
      err.code = res.error ? 'BACKEND' : 'INVALID_CREDENTIALS';
      throw err;
    }
    if (res.data?.rol !== 'chofer') {
      const err = new Error('wrong role');
      err.code = 'WRONG_ROLE';
      throw err;
    }
    await setToken(res.token);
    await setStoredUser(res.data);
    setUser(res.data);
    await loadProfile();
    return res.data;
  }, [loadProfile]);

  const logout = useCallback(async () => {
    await setToken(null);
    await setStoredUser(null);
    setUser(null);
    setChoferProfile(null);
  }, []);

  return (
    <AuthContext.Provider value={{ loading, user, choferProfile, profileError, login, logout, reloadProfile: loadProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
