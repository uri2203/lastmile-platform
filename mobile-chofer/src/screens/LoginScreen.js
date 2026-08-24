import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing, shadow } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n, translateError } from '../i18n';

export default function LoginScreen() {
  const { login } = useAuth();
  const { t } = useI18n();
  const [usuario, setUsuario] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);

  async function handleLogin() {
    if (!usuario.trim() || !pass) {
      setError(t('login.error_vacios'));
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login(usuario.trim(), pass);
    } catch (e) {
      setError(translateError(t, e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      {/* Formas decorativas de fondo -- le dan profundidad sin agregar
          ninguna libreria de imagenes/gradientes nueva. */}
      <View style={styles.blobTop} />
      <View style={styles.blobBottom} />

      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <View style={styles.logoBox}>
            <Text style={styles.logoText}>LM</Text>
          </View>
          <Text style={styles.title}>{t('chofer_app.app_title')}</Text>
          <Text style={styles.subtitle}>{t('chofer_app.login_subtitle')}</Text>

          <View style={styles.card}>
            {error ? (
              <View style={styles.error}>
                <Ionicons name="alert-circle" size={16} color={colors.danger} />
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}

            <Text style={styles.label}>{t('login.usuario').toUpperCase()}</Text>
            <View style={styles.inputRow}>
              <Ionicons name="person-outline" size={18} color={colors.textMuted} />
              <TextInput
                style={styles.input}
                value={usuario}
                onChangeText={setUsuario}
                placeholder={t('login.usuario_ph')}
                placeholderTextColor={colors.textMuted}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <Text style={styles.label}>{t('login.contrasena').toUpperCase()}</Text>
            <View style={styles.inputRow}>
              <Ionicons name="lock-closed-outline" size={18} color={colors.textMuted} />
              <TextInput
                style={styles.input}
                value={pass}
                onChangeText={setPass}
                placeholder={t('login.contrasena_ph')}
                placeholderTextColor={colors.textMuted}
                secureTextEntry={!showPass}
              />
              <TouchableOpacity onPress={() => setShowPass(v => !v)} hitSlop={8}>
                <Ionicons name={showPass ? 'eye-off-outline' : 'eye-outline'} size={18} color={colors.textMuted} />
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading} activeOpacity={0.85}>
              {loading ? <ActivityIndicator color="#fff" /> : (
                <>
                  <Text style={styles.buttonText}>{t('login.btn_entrar')}</Text>
                  <Ionicons name="arrow-forward" size={18} color="#fff" />
                </>
              )}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bgPrimary, overflow: 'hidden' },
  blobTop: { position: 'absolute', top: -120, right: -100, width: 280, height: 280, borderRadius: 140, backgroundColor: colors.accent, opacity: 0.16 },
  blobBottom: { position: 'absolute', bottom: -140, left: -120, width: 300, height: 300, borderRadius: 150, backgroundColor: colors.accentDeep, opacity: 0.18 },
  container: { flex: 1 },
  scrollContent: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.lg },
  logoBox: { width: 72, height: 72, borderRadius: radius.xl, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md, ...shadow.glow },
  logoText: { color: '#fff', fontWeight: '800', fontSize: 26, letterSpacing: 0.5 },
  title: { color: colors.textPrimary, fontSize: 24, fontWeight: '800', marginBottom: 4, textAlign: 'center' },
  subtitle: { color: colors.textSecondary, fontSize: 14, marginBottom: spacing.xl, textAlign: 'center' },
  card: { width: '100%', maxWidth: 400, backgroundColor: colors.bgCard, borderRadius: radius.xl, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.lg, ...shadow.card },
  error: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: colors.dangerBg, padding: spacing.sm, borderRadius: radius.md, marginBottom: spacing.md, width: '100%' },
  errorText: { color: colors.danger, fontSize: 13, flex: 1 },
  label: { color: colors.textMuted, fontSize: 11, fontWeight: '700', alignSelf: 'flex-start', marginBottom: 6, marginTop: spacing.sm, letterSpacing: 0.8 },
  inputRow: { flexDirection: 'row', alignItems: 'center', gap: 10, width: '100%', backgroundColor: colors.bgPrimary, borderWidth: 1, borderColor: colors.borderPrimary, borderRadius: radius.md, paddingHorizontal: 14 },
  input: { flex: 1, paddingVertical: 13, color: colors.textPrimary, fontSize: 15 },
  button: { flexDirection: 'row', width: '100%', backgroundColor: colors.accent, borderRadius: radius.md, padding: 15, alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: spacing.xl, ...shadow.glow },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
