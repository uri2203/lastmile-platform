/**
 * @module components/Button
 * @description Reusable button component with variants, sizes, loading state, and animated press feedback.
 */

import React, { useRef } from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Animated,
  View,
} from 'react-native';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';

/**
 * @typedef {'primary' | 'secondary' | 'ghost' | 'danger'} ButtonVariant
 * @typedef {'sm' | 'md' | 'lg'} ButtonSize
 */

/**
 * Button component.
 * @param {object} props
 * @param {string} props.title - Button text.
 * @param {() => void} props.onPress - Press handler.
 * @param {ButtonVariant} [props.variant='primary'] - Visual variant.
 * @param {ButtonSize} [props.size='md'] - Button size.
 * @param {boolean} [props.loading=false] - Shows spinner when true.
 * @param {boolean} [props.disabled=false] - Disables the button.
 * @param {React.ReactNode} [props.icon] - Optional icon element.
 * @param {object} [props.style] - Additional container styles.
 */
export default function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  style,
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.96,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4,
    }).start();
  };

  const variantStyles = {
    primary: {
      container: { backgroundColor: colors.primary[500] },
      text: { color: colors.white },
    },
    secondary: {
      container: {
        backgroundColor: colors.primary[50],
        borderWidth: 1,
        borderColor: colors.primary[200],
      },
      text: { color: colors.primary[600] },
    },
    ghost: {
      container: { backgroundColor: 'transparent' },
      text: { color: colors.primary[500] },
    },
    danger: {
      container: { backgroundColor: colors.error[500] },
      text: { color: colors.white },
    },
  };

  const sizeStyles = {
    sm: { container: { paddingVertical: spacing[1], paddingHorizontal: spacing[3] }, text: { fontSize: typography.fontSize.sm } },
    md: { container: { paddingVertical: spacing[2], paddingHorizontal: spacing[4] }, text: { fontSize: typography.fontSize.base } },
    lg: { container: { paddingVertical: spacing[3], paddingHorizontal: spacing[6] }, text: { fontSize: typography.fontSize.lg } },
  };

  const isDisabled = disabled || loading;
  const v = variantStyles[variant] || variantStyles.primary;
  const s = sizeStyles[size] || sizeStyles.md;

  return (
    <Animated.View style={[{ transform: [{ scale: scaleAnim }] }, style]}>
      <TouchableOpacity
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={isDisabled}
        activeOpacity={0.8}
        style={[
          styles.base,
          v.container,
          s.container,
          isDisabled && styles.disabled,
          variant !== 'ghost' && shadows.sm,
        ]}
      >
        {loading ? (
          <ActivityIndicator size="small" color={v.text.color} style={styles.loader} />
        ) : icon ? (
          <View style={styles.iconWrapper}>
            {icon}
            <Text style={[styles.text, s.text, v.text, styles.iconSpacing]}>{title}</Text>
          </View>
        ) : (
          <Text style={[styles.text, s.text, v.text]}>{title}</Text>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.md,
    minHeight: 44,
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
  loader: {
    marginVertical: 2,
  },
  iconWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconSpacing: {
    marginLeft: spacing[2],
  },
});
