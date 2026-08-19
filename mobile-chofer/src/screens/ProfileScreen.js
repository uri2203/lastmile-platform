import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Switch, Alert, Modal, FlatList, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n, translateError } from '../i18n';
import { startTracking, stopTracking, isTracking } from '../services/location';
import { registerForPushNotifications } from '../services/notifications';
import { checkForUpdateManual, getCurrentUpdateInfo } from '../services/updates';

export default function ProfileScreen() {
  const { user, choferProfile, logout } = useAuth();
  const { t, lang, setLanguage, availableLanguages } = useI18n();
  const [tracking, setTracking] = useState(false);
  const [busy, setBusy] = useState(false);
  const [showLangModal, setShowLangModal] = useState(false);
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const updateInfo = getCurrentUpdateInfo();

  async function handleCheckUpdate() {
    setCheckingUpdate(true);
    const result = await checkForUpdateManual();
    setCheckingUpdate(false);
    if (result.status === 'up-to-date') {
      Alert.alert(t('chofer_app.listo_titulo'), t('chofer_app.update_al_dia'));
    } else if (result.status === 'disabled') {
      Alert.alert(t('chofer_app.no_disponible_titulo'), t('chofer_app.update_disabled'));
    } else if (result.status === 'error') {
      Alert.alert(t('chofer_app.error_titulo'), t('chofer_app.network_error'));
    }
    // status === 'updated': reloadAsync() ya reinicio la app, no llega aca.
  }

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
        await startTracking(choferProfile.CHO_ID, t('chofer_app.app_title'), t('chofer_app.gps_notif_body'));
      } else {
        await stopTracking();
      }
      setTracking(value);
    } catch (e) {
      Alert.alert(t('chofer_app.error_titulo'), translateError(t, e));
    } finally {
      setBusy(false);
    }
  }

  function confirmLogout() {
    Alert.alert(t('chofer_app.cerrar_sesion_confirm_titulo'), t('chofer_app.cerrar_sesion_confirm_msg'), [
      { text: t('chofer_app.cancelar'), style: 'cancel' },
      { text: t('chofer_app.salir'), style: 'destructive', onPress: logout },
    ]);
  }

  const currentLang = availableLanguages.find(l => l.code === lang);

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.avatar}>
          <Ionicons name="person" size={28} color="#fff" />
        </View>
        <Text style={styles.name}>{choferProfile ? `${choferProfile.CHO_NOMBRE || ''} ${choferProfile.CHO_APELLIDO || ''}`.trim() : (user?.nombre || t('chofer.subtitle'))}</Text>
        <Text style={styles.company}>{user?.empresa || ''}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.rowBetween}>
          <View style={{ flex: 1 }}>
            <Text style={styles.settingTitle}>{t('chofer_app.compartir_ubicacion')}</Text>
            <Text style={styles.settingSub}>{t('chofer_app.compartir_ubicacion_desc')}</Text>
          </View>
          <Switch value={tracking} onValueChange={toggleTracking} disabled={busy} trackColor={{ true: colors.accent }} />
        </View>
      </View>

      <TouchableOpacity style={styles.card} onPress={() => setShowLangModal(true)}>
        <View style={styles.rowBetween}>
          <View style={{ flex: 1 }}>
            <Text style={styles.settingTitle}>{t('chofer_app.idioma_titulo')}</Text>
            <Text style={styles.settingSub}>{currentLang ? `${currentLang.flag} ${currentLang.name}` : lang}</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </View>
      </TouchableOpacity>

      <TouchableOpacity style={styles.card} onPress={handleCheckUpdate} disabled={checkingUpdate}>
        <View style={styles.rowBetween}>
          <View style={{ flex: 1 }}>
            <Text style={styles.settingTitle}>{t('chofer_app.buscar_actualizaciones')}</Text>
            <Text style={styles.settingSub}>
              {updateInfo.updateId ? t('chofer_app.version_instalada') : t('chofer_app.version_embebida')}
            </Text>
          </View>
          {checkingUpdate ? <ActivityIndicator color={colors.accent} /> : <Ionicons name="refresh" size={18} color={colors.accent} />}
        </View>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutButton} onPress={confirmLogout}>
        <Ionicons name="log-out-outline" size={18} color={colors.danger} />
        <Text style={styles.logoutText}>{t('chofer.cerrar_sesion')}</Text>
      </TouchableOpacity>

      <Modal visible={showLangModal} transparent animationType="slide" onRequestClose={() => setShowLangModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <FlatList
              data={availableLanguages}
              keyExtractor={(item) => item.code}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.langRow}
                  onPress={() => { setLanguage(item.code); setShowLangModal(false); }}
                >
                  <Text style={styles.langText}>{item.flag} {item.name}</Text>
                  {item.code === lang && <Ionicons name="checkmark" size={18} color={colors.accent} />}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
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
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bgCard, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, maxHeight: '70%' },
  langRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: colors.borderPrimary },
  langText: { color: colors.textPrimary, fontSize: 15 },
});
