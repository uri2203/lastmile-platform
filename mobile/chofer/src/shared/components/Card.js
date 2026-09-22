/**
 * @module components/Card
 * @description Reusable card component with shadow, border, and optional press animation.
 */

import React, { useRef } from 'react';
import { View, TouchableOpacity, StyleSheet, Animated } from 'react-native';
import { colors, spacing, borderRadius, shadows } from '../theme';

/**
 * @typedef {'default' | 'elevated' | 'outlined'} CardVariant
 */

/**
 * Card component.
 * @param {object} props
 * @param {React.ReactNode} props.children - Card content.
 * @param {object} [props.style] - Additional container styles.
 * @param {() => void} [props.onPress] - Press handler (makes card touchable).
 * @param {CardVariant} [props.variant='default'] - Visual variant.
 */
export default function Card({ children, style, onPress, variant = 'default' }) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    if (!onPress) return;
    Animated.spring(scaleAnim, {
      toValue: 0.98,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4,
    }).start();
  };

  const handlePressOut = () => {
    if (!onPress) return;
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4,
    }).start();
  };

  const variantStyles = {
    default: {
      backgroundColor: colors.white,
      borderWidth: 0,
      ...shadows.sm,
    },
    elevated: {
      backgroundColor: colors.white,
      borderWidth: 0,
      ...shadows.lg,
    },
    outlined: {
      backgroundColor: colors.white,
      borderWidth: 1,
      borderColor: colors.neutral[200],
    },
  };

  const v = variantStyles[variant] || variantStyles.default;

  const content = (
    <View style={[styles.base, v, style]}>
      {children}
    </View>
  );

  if (onPress) {
    return (
      <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
        <TouchableOpacity
          onPress={onPress}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          activeOpacity={0.8}
        >
          {content}
        </TouchableOpacity>
      </Animated.View>
    );
  }

  return content;
}

const styles = StyleSheet.create({
  base: {
    borderRadius: borderRadius.lg,
    padding: spacing[4],
  },
});
