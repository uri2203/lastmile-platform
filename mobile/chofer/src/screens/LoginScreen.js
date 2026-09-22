import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import useAuth from '../hooks/useAuth';
import Input from '../../shared/components/Input';
import Button from '../../shared/components/Button';
import { validateEmail } from '../../shared/validators';
import { colors, typography, spacing, borderRadius, shadows } from '../../shared/theme';

const { width, height } = Dimensions.get('window');

export default function LoginScreen() {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const logoScale = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(logoScale, {
        toValue: 1,
        friction: 4,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const validateForm = () => {
    let valid = true;
    setLoginError('');

    const emailResult = validateEmail(email);
    if (!emailResult.valid) {
      setEmailError(emailResult.error);
      valid = false;
    } else {
      setEmailError('');
    }

    if (!password || password.length < 4) {
      setPasswordError('La contraseña es requerida');
      valid = false;
    } else {
      setPasswordError('');
    }

    return valid;
  };

  const handleLogin = async () => {
    if (!validateForm()) return;

    setLoginLoading(true);
    setLoginError('');
    try {
      await login(email.trim(), password);
    } catch (error) {
      const message =
        error?.data?.message ||
        error?.message ||
        'Error al iniciar sesión. Verifica tus credenciales.';
      setLoginError(message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleForgotPassword = () => {
    Alert.alert(
      'Recuperar contraseña',
      'Contacta al administrador para restablecer tu contraseña.',
      [{ text: 'Entendido' }]
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#312e81', '#4f46e5', '#6366f1']}
        style={styles.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <KeyboardAvoidingView
          style={styles.flex}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <Animated.View
              style={[
                styles.content,
                {
                  opacity: fadeAnim,
                  transform: [{ translateY: slideAnim }],
                },
              ]}
            >
              <Animated.View
                style={[styles.logoContainer, { transform: [{ scale: logoScale }] }]}
              >
                <View style={styles.logo}>
                  <Ionicons name="cube" size={40} color="#ffffff" />
                </View>
                <Text style={styles.appName}>Last Mile</Text>
                <Text style={styles.appSubtitle}>Chofer</Text>
              </Animated.View>

              <View style={styles.formCard}>
                <Text style={styles.formTitle}>Iniciar Sesión</Text>
                <Text style={styles.formSubtitle}>
                  Ingresa tus credenciales para continuar
                </Text>

                {loginError ? (
                  <View style={styles.errorBanner}>
                    <Ionicons name="alert-circle" size={18} color={colors.error[600]} />
                    <Text style={styles.errorBannerText}>{loginError}</Text>
                  </View>
                ) : null}

                <Input
                  label="Correo electrónico"
                  value={email}
                  onChangeText={(text) => {
                    setEmail(text);
                    if (emailError) setEmailError('');
                    if (loginError) setLoginError('');
                  }}
                  placeholder="correo@ejemplo.com"
                  error={emailError}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  icon={<Ionicons name="mail-outline" size={20} color={colors.neutral[400]} />}
                  required
                />

                <Input
                  label="Contraseña"
                  value={password}
                  onChangeText={(text) => {
                    setPassword(text);
                    if (passwordError) setPasswordError('');
                    if (loginError) setLoginError('');
                  }}
                  placeholder="Ingresa tu contraseña"
                  error={passwordError}
                  secureTextEntry={!showPassword}
                  icon={<Ionicons name="lock-closed-outline" size={20} color={colors.neutral[400]} />}
                  rightIcon={
                    <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                      <Ionicons
                        name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                        size={20}
                        color={colors.neutral[400]}
                      />
                    </TouchableOpacity>
                  }
                  required
                />

                <View style={styles.optionsRow}>
                  <TouchableOpacity
                    style={styles.rememberRow}
                    onPress={() => setRememberMe(!rememberMe)}
                  >
                    <View
                      style={[
                        styles.checkbox,
                        rememberMe && styles.checkboxChecked,
                      ]}
                    >
                      {rememberMe && (
                        <Ionicons name="checkmark" size={14} color="#ffffff" />
                      )}
                    </View>
                    <Text style={styles.rememberText}>Recordar</Text>
                  </TouchableOpacity>

                  <TouchableOpacity onPress={handleForgotPassword}>
                    <Text style={styles.forgotText}>¿Olvidaste tu contraseña?</Text>
                  </TouchableOpacity>
                </View>

                <Button
                  title="Iniciar Sesión"
                  onPress={handleLogin}
                  loading={loginLoading}
                  disabled={loginLoading}
                  size="lg"
                  style={styles.loginButton}
                />
              </View>

              <View style={styles.footer}>
                <Ionicons name="shield-checkmark" size={16} color="rgba(255,255,255,0.6)" />
                <Text style={styles.footerText}>
                  Conexión segura con Last Mile Platform
                </Text>
              </View>
            </Animated.View>
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing[6],
    paddingVertical: spacing[10],
  },
  content: {
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: spacing[8],
  },
  logo: {
    width: 88,
    height: 88,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing[4],
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  appName: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: '800',
    color: '#ffffff',
    letterSpacing: -0.5,
  },
  appSubtitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: '500',
    color: 'rgba(255,255,255,0.7)',
    marginTop: -2,
  },
  formCard: {
    backgroundColor: '#ffffff',
    borderRadius: borderRadius.xl,
    padding: spacing[6],
    width: '100%',
    ...shadows.xl,
  },
  formTitle: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: '700',
    color: colors.neutral[900],
    marginBottom: spacing[1],
  },
  formSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.neutral[500],
    marginBottom: spacing[6],
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.error[50],
    borderRadius: borderRadius.md,
    padding: spacing[3],
    marginBottom: spacing[4],
    borderWidth: 1,
    borderColor: colors.error[100],
  },
  errorBannerText: {
    fontSize: typography.fontSize.sm,
    color: colors.error[600],
    marginLeft: spacing[2],
    flex: 1,
  },
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing[6],
  },
  rememberRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: colors.neutral[300],
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing[2],
  },
  checkboxChecked: {
    backgroundColor: colors.primary[500],
    borderColor: colors.primary[500],
  },
  rememberText: {
    fontSize: typography.fontSize.sm,
    color: colors.neutral[600],
  },
  forgotText: {
    fontSize: typography.fontSize.sm,
    color: colors.primary[500],
    fontWeight: '600',
  },
  loginButton: {
    width: '100%',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing[6],
  },
  footerText: {
    fontSize: typography.fontSize.xs,
    color: 'rgba(255,255,255,0.6)',
    marginLeft: spacing[2],
  },
});
