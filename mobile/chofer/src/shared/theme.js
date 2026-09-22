/**
 * @module theme
 * @description Design tokens for the Last Mile Delivery app.
 * Includes colors, typography, spacing, border radii, shadows, and full theme objects.
 */

export const colors = {
  primary: {
    50: '#eef2ff',
    100: '#e0e7ff',
    200: '#c7d2fe',
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#6366f1',
    600: '#4f46e5',
    700: '#4338ca',
    800: '#3730a3',
    900: '#312e81',
  },
  accent: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
    600: '#d97706',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  },
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  white: '#ffffff',
  black: '#000000',
};

export const typography = {
  fontFamily: {
    regular: 'Inter-Regular',
    medium: 'Inter-Medium',
    semibold: 'Inter-SemiBold',
    bold: 'Inter-Bold',
  },
  fontSize: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const spacing = {
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
};

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 16,
  xl: 24,
  full: 9999,
};

/**
 * Generates elevation shadows.
 * @param {number} level - Shadow intensity (1-5).
 * @returns {object} Shadow styles.
 */
function elevation(level) {
  const map = {
    1: { shadowOffset: { width: 0, height: 1 }, shadowRadius: 3, shadowOpacity: 0.08 },
    2: { shadowOffset: { width: 0, height: 2 }, shadowRadius: 6, shadowOpacity: 0.1 },
    3: { shadowOffset: { width: 0, height: 4 }, shadowRadius: 12, shadowOpacity: 0.12 },
    4: { shadowOffset: { width: 0, height: 6 }, shadowRadius: 16, shadowOpacity: 0.15 },
    5: { shadowOffset: { width: 0, height: 8 }, shadowRadius: 24, shadowOpacity: 0.18 },
  };
  return map[level] || map[1];
}

export const shadows = {
  sm: { ...elevation(1), shadowColor: '#000' },
  md: { ...elevation(2), shadowColor: '#000' },
  lg: { ...elevation(3), shadowColor: '#000' },
  xl: { ...elevation(4), shadowColor: '#000' },
  '2xl': { ...elevation(5), shadowColor: '#000' },
};

export const lightTheme = {
  dark: false,
  colors: {
    background: colors.neutral[50],
    surface: colors.white,
    surfaceVariant: colors.neutral[100],
    primary: colors.primary[500],
    primaryLight: colors.primary[100],
    onPrimary: colors.white,
    accent: colors.accent[500],
    text: colors.neutral[900],
    textSecondary: colors.neutral[500],
    textDisabled: colors.neutral[300],
    border: colors.neutral[200],
    error: colors.error[500],
    success: colors.success[500],
    warning: colors.warning[500],
    card: colors.white,
    cardBorder: colors.neutral[200],
  },
};

export const darkTheme = {
  dark: true,
  colors: {
    background: colors.neutral[900],
    surface: colors.neutral[800],
    surfaceVariant: colors.neutral[700],
    primary: colors.primary[400],
    primaryLight: colors.primary[900],
    onPrimary: colors.neutral[900],
    accent: colors.accent[400],
    text: colors.neutral[50],
    textSecondary: colors.neutral[400],
    textDisabled: colors.neutral[600],
    border: colors.neutral[700],
    error: colors.error[500],
    success: colors.success[500],
    warning: colors.warning[500],
    card: colors.neutral[800],
    cardBorder: colors.neutral[700],
  },
};

export default {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  lightTheme,
  darkTheme,
};
