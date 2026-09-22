/**
 * @module components/Badge
 * @description Status badge component with color-coded pill shape.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, borderRadius, colors } from '../theme';
import { formatStatus } from '../formatters';

/**
 * @typedef {'sm' | 'md'} BadgeSize
 */

/**
 * Badge component.
 * @param {object} props
 * @param {string} props.status - Status code (e.g., 'PENDIENTE', 'EN_RUTA').
 * @param {BadgeSize} [props.size='md'] - Badge size.
 */
export default function Badge({ status, size = 'md' }) {
  const { label, color, bgColor } = formatStatus(status);

  const sizeStyles = {
    sm: { paddingVertical: 2, paddingHorizontal: spacing[2], text: { fontSize: typography.fontSize.xs } },
    md: { paddingVertical: spacing[1], paddingHorizontal: spacing[3], text: { fontSize: typography.fontSize.sm } },
  };

  const s = sizeStyles[size] || sizeStyles.md;

  return (
    <View style={[styles.base, { backgroundColor: bgColor }, { paddingVertical: s.paddingVertical, paddingHorizontal: s.paddingHorizontal }]}>
      <Text style={[styles.text, { color }, s.text]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    alignSelf: 'flex-start',
    borderRadius: borderRadius.full,
  },
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
});
