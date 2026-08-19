import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n, translateError } from '../i18n';

export default function LoginScreen() {
  const { login } = useAuth();
  const { t } = useI18n();
  const [usuario, setUsuario] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <StatusBar style="light" />
      <View style={styles.card}>
        <View style={styles.logoBox}>
          <Text style={styles.logoText}>LM</Text>
        </View>
        <Text style={styles.title}>{t('chofer_app.app_title')}</Text>
        <Text style={styles.subtitle}>{t('chofer_app.login_subtitle')}</Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Text style={styles.label}>{t('login.usuario').toUpperCase()}</Text>
        <TextInput
          style={styles.input}
          value={usuario}
          onChangeText={setUsuario}
          placeholder={t('login.usuario_ph')}
          placeholderTextColor={colors.textMuted}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <Text style={styles.label}>{t('login.contrasena').toUpperCase()}</Text>
        <TextInput
          style={styles.input}
          value={pass}
          onChangeText={setPass}
          placeholder={t('login.contrasena_ph')}
          placeholderTextColor={colors.textMuted}
          secureTextEntry
        />

        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>{t('login.btn_entrar')}</Text>}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary, alignItems: 'center', justifyContent: 'center', padding: spacing.lg },
  card: { width: '100%', maxWidth: 400, backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.lg, alignItems: 'center' },
  logoBox: { width: 56, height: 56, borderRadius: radius.md, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  logoText: { color: '#fff', fontWeight: '700', fontSize: 20 },
  title: { color: colors.textPrimary, fontSize: 20, fontWeight: '700', marginBottom: 4 },
  subtitle: { color: colors.textSecondary, fontSize: 13, marginBottom: spacing.lg, textAlign: 'center' },
  error: { color: colors.danger, backgroundColor: colors.dangerBg, padding: spacing.sm, borderRadius: radius.md, marginBottom: spacing.md, width: '100%', textAlign: 'center', fontSize: 13 },
  label: { color: colors.textMuted, fontSize: 11, fontWeight: '600', alignSelf: 'flex-start', marginBottom: 6, marginTop: spacing.sm, letterSpacing: 0.5 },
  input: { width: '100%', backgroundColor: colors.bgPrimary, borderWidth: 1, borderColor: colors.borderPrimary, borderRadius: radius.md, padding: 12, color: colors.textPrimary, fontSize: 15 },
  button: { width: '100%', backgroundColor: colors.accent, borderRadius: radius.md, padding: 14, alignItems: 'center', marginTop: spacing.lg },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
