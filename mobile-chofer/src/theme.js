/**
 * Paleta alineada al design-system.css del resto de la plataforma
 * (mismo acento #6366f1, mismo fondo oscuro que panel-chofer.html).
 */
export const colors = {
  bgPrimary: '#0d0d12',
  bgSecondary: '#15151d',
  bgCard: '#1a1a24',
  borderPrimary: 'rgba(255,255,255,0.08)',
  borderSecondary: 'rgba(255,255,255,0.16)',
  textPrimary: '#e8e8ed',
  textSecondary: '#a0a0ad',
  textMuted: '#6b6b78',
  accent: '#6366f1',
  success: '#10b981',
  successBg: 'rgba(16,185,129,0.12)',
  danger: '#ef4444',
  dangerBg: 'rgba(239,68,68,0.12)',
  warning: '#f59e0b',
  warningBg: 'rgba(245,158,11,0.12)',
  info: '#3b82f6',
  infoBg: 'rgba(59,130,246,0.12)',
  accentBright: '#818cf8',
  accentDeep: '#4338ca',
};

export const radius = {
  md: 8,
  lg: 12,
  xl: 20,
  full: 999,
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

// Sombras consistentes en vez de flat design -- se usan en cards/botones
// clave para darle profundidad sin agregar ninguna libreria nueva (evita
// otro rebuild nativo del APK).
export const shadow = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 4,
  },
  soft: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 2,
  },
  glow: {
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 6,
  },
};
