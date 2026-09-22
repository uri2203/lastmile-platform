/**
 * @module components/LoadingScreen
 * @description Full-screen loading spinner with optional message and animated dots.
 */

import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, ActivityIndicator } from 'react-native';
import { colors, typography, spacing } from '../theme';

/**
 * LoadingScreen component.
 * @param {object} props
 * @param {string} [props.message='Cargando...'] - Loading message.
 */
export default function LoadingScreen({ message = 'Cargando...' }) {
  const dotAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(dotAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
        Animated.timing(dotAnim, { toValue: 0, duration: 600, useNativeDriver: true }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [dotAnim]);

  const opacity1 = dotAnim.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1] });
  const opacity2 = dotAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.3, 0.3, 1],
  });
  const opacity3 = dotAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.3, 0.3, 1],
  });

  return (
    <View style={styles.container}>
      <View style={styles.logoContainer}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>LM</Text>
        </View>
      </View>
      <ActivityIndicator size="large" color={colors.primary[500]} style={styles.spinner} />
      <View style={styles.messageRow}>
        <Text style={styles.message}>{message}</Text>
        <View style={styles.dots}>
          <Animated.Text style={[styles.dot, { opacity: opacity1 }]}>.</Animated.Text>
          <Animated.Text style={[styles.dot, { opacity: opacity2 }]}>.</Animated.Text>
          <Animated.Text style={[styles.dot, { opacity: opacity3 }]}>.</Animated.Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.white,
  },
  logoContainer: {
    marginBottom: spacing[6],
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 20,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.white,
  },
  spinner: {
    marginBottom: spacing[4],
  },
  messageRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  message: {
    fontSize: typography.fontSize.base,
    color: colors.neutral[500],
    fontWeight: '500',
  },
  dots: {
    flexDirection: 'row',
    marginLeft: 2,
  },
  dot: {
    fontSize: typography.fontSize.lg,
    color: colors.neutral[500],
    fontWeight: '700',
    lineHeight: 20,
  },
});
