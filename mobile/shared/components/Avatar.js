/**
 * @module components/Avatar
 * @description User avatar component with initials fallback, generated color, and online indicator.
 */

import React, { useMemo } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { colors, typography, borderRadius } from '../theme';

/**
 * Generates a consistent color from a name string.
 * @param {string} name - The user's name.
 * @returns {string} Hex color.
 */
function getColorFromName(name) {
  const palette = [
    '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
    '#ec4899', '#f43f5e', '#ef4444', '#f97316',
    '#f59e0b', '#eab308', '#84cc16', '#22c55e',
    '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return palette[Math.abs(hash) % palette.length];
}

/**
 * Extracts initials from a name (max 2 characters).
 * @param {string} name - The user's name.
 * @returns {string} Initials.
 */
function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

/**
 * Avatar component.
 * @param {object} props
 * @param {string} [props.name] - User name for initials/color.
 * @param {'sm' | 'md' | 'lg' | number} [props.size='md'] - Avatar size.
 * @param {string} [props.imageUri] - Remote image URI.
 * @param {boolean} [props.online=false] - Shows online indicator dot.
 */
export default function Avatar({ name = '', size = 'md', imageUri, online = false }) {
  const sizeMap = { sm: 32, md: 44, lg: 64 };
  const px = typeof size === 'number' ? size : (sizeMap[size] || 44);

  const bgColor = useMemo(() => getColorFromName(name), [name]);
  const initials = useMemo(() => getInitials(name), [name]);

  const fontSize = px * 0.38;

  return (
    <View style={[styles.container, { width: px, height: px }]}>
      {imageUri ? (
        <Image source={{ uri: imageUri }} style={[styles.image, { width: px, height: px }]} />
      ) : (
        <View style={[styles.fallback, { width: px, height: px, backgroundColor: bgColor, borderRadius: px / 2 }]}>
          <Text style={[styles.initials, { fontSize }]}>{initials}</Text>
        </View>
      )}
      {online && (
        <View style={[styles.onlineDot, { right: 0, bottom: 0 }]} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  image: {
    borderRadius: borderRadius.full,
  },
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  initials: {
    color: colors.white,
    fontWeight: '700',
  },
  onlineDot: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.success[500],
    borderWidth: 2,
    borderColor: colors.white,
  },
});
