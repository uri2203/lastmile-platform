/**
 * @module components/EmptyState
 * @description Empty state component with icon, text, and optional action button.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, typography, spacing } from '../theme';
import Button from './Button';

/**
 * EmptyState component.
 * @param {object} props
 * @param {React.ReactNode} [props.icon] - Icon element.
 * @param {string} props.title - Main message.
 * @param {string} [props.subtitle] - Secondary message.
 * @param {string} [props.actionLabel] - Action button label.
 * @param {() => void} [props.onAction] - Action button handler.
 */
export default function EmptyState({ icon, title, subtitle, actionLabel, onAction }) {
  return (
    <View style={styles.container}>
      {icon && <View style={styles.iconWrapper}>{icon}</View>}
      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      {actionLabel && onAction && (
        <Button
          title={actionLabel}
          onPress={onAction}
          variant="primary"
          size="md"
          style={styles.button}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing[8],
    paddingVertical: spacing[12],
  },
  iconWrapper: {
    marginBottom: spacing[4],
    opacity: 0.6,
  },
  title: {
    fontSize: typography.fontSize.lg,
    fontWeight: '600',
    color: colors.neutral[700],
    textAlign: 'center',
    marginBottom: spacing[2],
  },
  subtitle: {
    fontSize: typography.fontSize.base,
    color: colors.neutral[500],
    textAlign: 'center',
    lineHeight: typography.fontSize.base * typography.lineHeight.normal,
  },
  button: {
    marginTop: spacing[6],
    minWidth: 160,
  },
});
