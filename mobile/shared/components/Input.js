/**
 * @module components/Input
 * @description Reusable text input component with label, error, icons, and focus styling.
 */

import React, { useState } from 'react';
import { View, TextInput, Text, StyleSheet } from 'react-native';
import { colors, typography, spacing, borderRadius } from '../theme';

/**
 * Input component.
 * @param {object} props
 * @param {string} [props.label] - Input label text.
 * @param {string} [props.value] - Current value.
 * @param {(text: string) => void} [props.onChangeText] - Text change handler.
 * @param {string} [props.placeholder] - Placeholder text.
 * @param {string} [props.error] - Error message to display.
 * @param {boolean} [props.secureTextEntry] - Masks input.
 * @param {React.ReactNode} [props.icon] - Icon element (left side).
 * @param {React.ReactNode} [props.rightIcon] - Icon element (right side).
 * @param {string} [props.keyboardType] - Keyboard type.
 * @param {boolean} [props.required] - Shows asterisk on label.
 * @param {boolean} [props.disabled] - Disables the input.
 * @param {object} [props.style] - Additional container styles.
 * @param {object} [props.inputStyle] - Additional input styles.
 */
export default function Input({
  label,
  value,
  onChangeText,
  placeholder,
  error,
  secureTextEntry,
  icon,
  rightIcon,
  keyboardType,
  required = false,
  disabled = false,
  style,
  inputStyle,
  ...rest
}) {
  const [isFocused, setIsFocused] = useState(false);

  const borderColor = error
    ? colors.error[500]
    : isFocused
      ? colors.primary[500]
      : colors.neutral[200];

  return (
    <View style={[styles.container, style]}>
      {label && (
        <Text style={styles.label}>
          {label}
          {required && <Text style={styles.asterisk}> *</Text>}
        </Text>
      )}
      <View style={[styles.inputWrapper, { borderColor }, isFocused && styles.inputWrapperFocused]}>
        {icon && <View style={styles.iconLeft}>{icon}</View>}
        <TextInput
          style={[
            styles.input,
            icon && styles.inputWithLeftIcon,
            rightIcon && styles.inputWithRightIcon,
            disabled && styles.inputDisabled,
            inputStyle,
          ]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.neutral[400]}
          secureTextEntry={secureTextEntry}
          keyboardType={keyboardType}
          editable={!disabled}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...rest}
        />
        {rightIcon && <View style={styles.iconRight}>{rightIcon}</View>}
      </View>
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing[4],
  },
  label: {
    fontSize: typography.fontSize.sm,
    fontWeight: '500',
    color: colors.neutral[700],
    marginBottom: spacing[1],
  },
  asterisk: {
    color: colors.error[500],
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderRadius: borderRadius.md,
    backgroundColor: colors.white,
    minHeight: 48,
  },
  inputWrapperFocused: {
    shadowColor: colors.primary[500],
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  input: {
    flex: 1,
    fontSize: typography.fontSize.base,
    color: colors.neutral[900],
    paddingHorizontal: spacing[3],
    paddingVertical: spacing[2],
  },
  inputWithLeftIcon: {
    paddingLeft: 0,
  },
  inputWithRightIcon: {
    paddingRight: 0,
  },
  inputDisabled: {
    backgroundColor: colors.neutral[100],
    color: colors.neutral[400],
  },
  iconLeft: {
    paddingLeft: spacing[3],
  },
  iconRight: {
    paddingRight: spacing[3],
  },
  error: {
    fontSize: typography.fontSize.xs,
    color: colors.error[500],
    marginTop: spacing[1],
  },
});
