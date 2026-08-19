import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Switch, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { startTracking, stopTracking, isTracking } from '../services/location';
import { registerForPushNotifications } from '../services/notifications';

export default function ProfileScreen() {
  const { user, choferProfile, logout } = useAuth();
  const [tracking, setTracking] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    isTracking().then(setTracking);
  }, []);

  useEffect(() => {
    if (choferProfile?.CHO_USU_ID) {
      registerForPushNotifications(choferProfile.CHO_USU_ID, choferProfile.CHO_ID).catch(() => {});
    }
  }, [choferProfile]);

  async function toggleTracking(value) {
    if (!choferProfile) return;
    setBusy(true);
    try {
      if (value) {
        await startTracking(choferProfile.CHO_ID);
      } else {
        await stopTracking();
      }
      setTracking(value);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setBusy(false);
    }
  }

  function confirmLogout() {
    Alert.alert('Cerrar sesion', 'Vas a salir de tu cuenta.', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Salir', style: 'destructive', onPress: logout },
    ]);
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.avatar}>
          <Ionicons name="person" size={28} color="#fff" />
        </View>
        <Text style={styles.name}>{choferProfile ? `${choferProfile.CHO_NOMBRE || ''} ${choferProfile.CHO_APELLIDO || ''}`.trim() : (user?.nombre || 'Chofer')}</Text>
        <Text style={styles.company}>{user?.empresa || ''}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.rowBetween}>
          <View style={{ flex: 1 }}>
            <Text style={styles.settingTitle}>Compartir mi ubicacion</Text>
            <Text style={styles.settingSub}>Reporta tu posicion en tiempo real mientras trabajas</Text>
          </View>
          <Switch value={tracking} onValueChange={toggleTracking} disabled={busy} trackColor={{ true: colors.accent }} />
        </View>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={confirmLogout}>
        <Ionicons name="log-out-outline" size={18} color={colors.danger} />
        <Text style={styles.logoutText}>Cerrar sesion</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary, padding: spacing.md },
  card: { backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.lg, marginBottom: spacing.md, alignItems: 'center' },
  avatar: { width: 60, height: 60, borderRadius: 30, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  name: { color: colors.textPrimary, fontSize: 17, fontWeight: '700' },
  company: { color: colors.textMuted, fontSize: 13, marginTop: 2 },
  rowBetween: { flexDirection: 'row', alignItems: 'center', width: '100%' },
  settingTitle: { color: colors.textPrimary, fontSize: 14, fontWeight: '600' },
  settingSub: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
  logoutButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, padding: 14, marginTop: spacing.md },
  logoutText: { color: colors.danger, fontWeight: '600', fontSize: 14 },
});
