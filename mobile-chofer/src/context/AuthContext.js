import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api, getToken, setToken } from '../api';

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
      const token = await getToken();
      if (token) {
        // No hay endpoint "whoami"; se valida el token al primer request real
        // (getMyProfile). Si el token expiro, api.js lo limpia solo (401).
        try {
          await loadProfile();
          setUser({ token });
        } catch (e) {
          // token invalido/expirado
        }
      }
      setLoading(false);
    })();
  }, [loadProfile]);

  const login = useCallback(async (usuario, pass) => {
    const res = await api.login(usuario, pass);
    if (!res.success || !res.token) {
      throw new Error(res.error || 'Usuario o contrasena incorrectos');
    }
    if (res.data?.rol !== 'chofer') {
      throw new Error('Esta app es solo para choferes. Tu cuenta tiene otro rol.');
    }
    await setToken(res.token);
    setUser(res.data);
    await loadProfile();
    return res.data;
  }, [loadProfile]);

  const logout = useCallback(async () => {
    await setToken(null);
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
