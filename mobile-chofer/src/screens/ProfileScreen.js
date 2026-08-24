import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Switch, Alert, Modal, FlatList, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing, shadow } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n, translateError } from '../i18n';
import { startTracking, stopTracking, isTracking } from '../services/location';
import { registerForPushNotifications } from '../services/notifications';
import { checkForUpdateManual, getCurrentUpdateInfo } from '../services/updates';
import { api } from '../api';

function SettingRow({ icon, iconColor, iconBg, title, subtitle, right, onPress, disabled }) {
  const Wrapper = onPress ? TouchableOpacity : View;
  return (
    <Wrapper style={styles.settingRow} onPress={onPress} disabled={disabled} activeOpacity={0.7}>
      <View style={[styles.settingIcon, { backgroundColor: iconBg }]}>
        <Ionicons name={icon} size={18} color={iconColor} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.settingTitle}>{title}</Text>
        {!!subtitle && <Text style={styles.settingSub}>{subtitle}</Text>}
      </View>
      {right}
    </Wrapper>
  );
}

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

  async function enviarPercance(motivo) {
    if (!choferProfile) return;
    try {
      const res = await api.reportarPercance(choferProfile.CHO_ID, motivo);
      // t() no soporta interpolacion de variables -- se arma el mensaje
      // concatenando la cantidad con el texto traducido.
      Alert.alert(t('chofer_app.listo_titulo'), `${t('chofer_app.percance_enviado_msg')} (${res.pedidos_afectados})`);
    } catch (e) {
      Alert.alert(t('chofer_app.error_titulo'), translateError(t, e));
    }
  }

  function handleReportarPercance() {
    if (!choferProfile) return;
    const confirmarYPedirMotivo = () => {
      if (Alert.prompt) {
        Alert.prompt(t('chofer_app.percance_motivo_titulo'), t('chofer_app.percance_motivo_desc'), (motivo) => {
          enviarPercance((motivo || '').trim());
        });
      } else {
        enviarPercance('');
      }
    };
    Alert.alert(
      t('chofer_app.percance_confirm_titulo'),
      t('chofer_app.percance_confirm_desc'),
      [
        { text: t('chofer_app.cancelar'), style: 'cancel' },
        { text: t('chofer_app.reportar_percance'), style: 'destructive', onPress: confirmarYPedirMotivo },
      ]
    );
  }

  const currentLang = availableLanguages.find(l => l.code === lang);
  const displayName = choferProfile ? `${choferProfile.CHO_NOMBRE || ''} ${choferProfile.CHO_APELLIDO || ''}`.trim() : (user?.nombre || t('chofer.subtitle'));
  const initials = displayName.split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase() || 'C';

  return (
    <View style={styles.container}>
      <View style={styles.heroCard}>
        <View style={styles.heroBlob} />
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>
        <Text style={styles.name}>{displayName}</Text>
        <Text style={styles.company}>{user?.empresa || ''}</Text>
        <View style={styles.roleBadge}>
          <Ionicons name="car-sport" size={12} color={colors.accent} />
          <Text style={styles.roleBadgeText}>{t('chofer.subtitle')}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <SettingRow
          icon="location"
          iconColor={colors.success}
          iconBg={colors.successBg}
          title={t('chofer_app.compartir_ubicacion')}
          subtitle={t('chofer_app.compartir_ubicacion_desc')}
          right={<Switch value={tracking} onValueChange={toggleTracking} disabled={busy} trackColor={{ true: colors.accent }} />}
        />
        <View style={styles.divider} />
        <SettingRow
          icon="language"
          iconColor={colors.info}
          iconBg={colors.infoBg}
          title={t('chofer_app.idioma_titulo')}
          subtitle={currentLang ? `${currentLang.flag} ${currentLang.name}` : lang}
          onPress={() => setShowLangModal(true)}
          right={<Ionicons name="chevron-forward" size={18} color={colors.textMuted} />}
        />
        <View style={styles.divider} />
        <SettingRow
          icon="cloud-download"
          iconColor={colors.accent}
          iconBg={colors.accentDeep + '33'}
          title={t('chofer_app.buscar_actualizaciones')}
          subtitle={updateInfo.updateId ? t('chofer_app.version_instalada') : t('chofer_app.version_embebida')}
          onPress={handleCheckUpdate}
          disabled={checkingUpdate}
          right={checkingUpdate ? <ActivityIndicator color={colors.accent} /> : <Ionicons name="refresh" size={18} color={colors.accent} />}
        />
      </View>

      {!!choferProfile && (
        <TouchableOpacity style={styles.percanceButton} onPress={handleReportarPercance} activeOpacity={0.8}>
          <Ionicons name="warning" size={18} color={colors.warning} />
          <Text style={styles.percanceButtonText}>{t('chofer_app.reportar_percance')}</Text>
        </TouchableOpacity>
      )}

      <TouchableOpacity style={styles.logoutButton} onPress={confirmLogout} activeOpacity={0.8}>
        <Ionicons name="log-out-outline" size={18} color={colors.danger} />
        <Text style={styles.logoutText}>{t('chofer.cerrar_sesion')}</Text>
      </TouchableOpacity>

      <Modal visible={showLangModal} transparent animationType="slide" onRequestClose={() => setShowLangModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>{t('chofer_app.idioma_titulo')}</Text>
            <FlatList
              data={availableLanguages}
              keyExtractor={(item) => item.code}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[styles.langRow, item.code === lang && styles.langRowActive]}
                  onPress={() => { setLanguage(item.code); setShowLangModal(false); }}
                  activeOpacity={0.7}
                >
                  <Text style={styles.langText}>{item.flag} {item.name}</Text>
                  {item.code === lang && <Ionicons name="checkmark-circle" size={20} color={colors.accent} />}
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
  heroCard: { backgroundColor: colors.bgCard, borderRadius: radius.xl, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.lg, marginBottom: spacing.md, alignItems: 'center', overflow: 'hidden', ...shadow.card },
  heroBlob: { position: 'absolute', top: -60, right: -60, width: 160, height: 160, borderRadius: 80, backgroundColor: colors.accent, opacity: 0.12 },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm, ...shadow.glow },
  avatarText: { color: '#fff', fontWeight: '800', fontSize: 24 },
  name: { color: colors.textPrimary, fontSize: 18, fontWeight: '800' },
  company: { color: colors.textMuted, fontSize: 13, marginTop: 2 },
  roleBadge: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: colors.accentDeep + '33', borderRadius: radius.full, paddingHorizontal: 10, paddingVertical: 4, marginTop: spacing.sm },
  roleBadgeText: { color: colors.accentBright, fontSize: 11, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  section: { backgroundColor: colors.bgCard, borderRadius: radius.xl, borderWidth: 1, borderColor: colors.borderPrimary, marginBottom: spacing.md, overflow: 'hidden', ...shadow.soft },
  settingRow: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, gap: spacing.sm },
  settingIcon: { width: 38, height: 38, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
  settingTitle: { color: colors.textPrimary, fontSize: 14, fontWeight: '600' },
  settingSub: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
  divider: { height: 1, backgroundColor: colors.borderPrimary, marginLeft: spacing.md + 38 + spacing.sm },
  logoutButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, padding: 14, marginTop: spacing.sm },
  logoutText: { color: colors.danger, fontWeight: '700', fontSize: 14 },
  percanceButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, borderWidth: 1, borderColor: colors.warning, backgroundColor: colors.warningBg, borderRadius: radius.lg, padding: 13, marginTop: spacing.xs },
  percanceButtonText: { color: colors.warning, fontWeight: '700', fontSize: 14 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bgCard, borderTopLeftRadius: radius.xl, borderTopRightRadius: radius.xl, padding: spacing.lg, maxHeight: '70%' },
  modalHandle: { width: 40, height: 4, borderRadius: 2, backgroundColor: colors.borderSecondary, alignSelf: 'center', marginBottom: spacing.md },
  modalTitle: { color: colors.textPrimary, fontSize: 16, fontWeight: '700', marginBottom: spacing.sm },
  langRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, paddingHorizontal: spacing.sm, borderRadius: radius.md },
  langRowActive: { backgroundColor: colors.accentDeep + '22' },
  langText: { color: colors.textPrimary, fontSize: 15 },
});
