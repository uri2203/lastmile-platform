import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import * as Localization from 'expo-localization';
import * as SecureStore from 'expo-secure-store';
import { BASE_URL } from '../api';
import fallbackEs from './fallback';

const LANG_KEY = 'lastmile_chofer_lang';

// Mismos 12 idiomas que soporta el resto de la plataforma (ver
// api/web/js/i18n.js). Se listan aca para el selector de idioma.
export const AVAILABLE_LANGUAGES = [
  { code: 'es', name: 'Espanol', flag: '🇲🇽' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'pt', name: 'Portugues', flag: '🇧🇷' },
  { code: 'fr', name: 'Francais', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
];
const VALID_CODES = AVAILABLE_LANGUAGES.map(l => l.code);

function detectDeviceLang() {
  try {
    const locales = Localization.getLocales();
    const code = locales?.[0]?.languageCode;
    return VALID_CODES.includes(code) ? code : 'es';
  } catch (e) {
    return 'es';
  }
}

function getNested(obj, dottedKey) {
  const parts = dottedKey.split('.');
  let val = obj;
  for (const p of parts) {
    if (val && typeof val === 'object' && p in val) val = val[p];
    else return undefined;
  }
  return typeof val === 'string' ? val : undefined;
}

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState('es');
  const [translations, setTranslations] = useState(fallbackEs);
  const [ready, setReady] = useState(false);

  const loadLanguage = useCallback(async (code) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    try {
      const res = await fetch(`${BASE_URL}/i18n/${code}.json`, { signal: controller.signal });
      if (!res.ok) throw new Error('fetch failed');
      const json = await res.json();
      setTranslations(json);
    } catch (e) {
      // Sin conexion: se sigue usando lo que ya estaba cargado (fallback o
      // el ultimo idioma descargado con exito).
      console.warn('[i18n] no se pudo descargar', code, e.message);
    } finally {
      clearTimeout(timeoutId);
    }
  }, []);

  useEffect(() => {
    (async () => {
      let stored = null;
      try {
        stored = await SecureStore.getItemAsync(LANG_KEY);
      } catch (e) {}
      const initial = VALID_CODES.includes(stored) ? stored : detectDeviceLang();
      setLangState(initial);
      await loadLanguage(initial);
      setReady(true);
    })();
  }, [loadLanguage]);

  const setLanguage = useCallback(async (code) => {
    if (!VALID_CODES.includes(code)) return;
    setLangState(code);
    await SecureStore.setItemAsync(LANG_KEY, code);
    await loadLanguage(code);
  }, [loadLanguage]);

  const t = useCallback((key) => {
    return getNested(translations, key) || getNested(fallbackEs, key) || key;
  }, [translations]);

  return (
    <I18nContext.Provider value={{ lang, setLanguage, t, ready, availableLanguages: AVAILABLE_LANGUAGES }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n debe usarse dentro de I18nProvider');
  return ctx;
}

const ERROR_CODE_KEYS = {
  NETWORK: 'chofer_app.network_error',
  SERVER: 'chofer_app.server_error',
  SESSION_EXPIRED: 'chofer_app.session_expired',
  INVALID_CREDENTIALS: 'login.error_creds',
  WRONG_ROLE: 'chofer_app.wrong_role',
  LOCATION_PERMISSION: 'chofer_app.location_permission_denied',
};

// Traduce errores lanzados por api.js/AuthContext (con e.code) a texto en el
// idioma activo. Errores 'BACKEND' (texto libre del servidor, no i18n'd) se
// muestran tal cual vienen.
export function translateError(t, err) {
  if (!err) return '';
  const key = ERROR_CODE_KEYS[err.code];
  return key ? t(key) : err.message;
}
