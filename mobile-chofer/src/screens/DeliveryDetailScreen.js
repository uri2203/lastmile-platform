import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert, ActivityIndicator, Image, Modal, Linking } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import SignatureScreen from 'react-native-signature-canvas';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { api } from '../api';
import { useI18n, translateError } from '../i18n';
import { enqueue } from '../services/offlineQueue';

function hasCoords(entrega) {
  return typeof entrega.PED_LATITUD === 'number' && typeof entrega.PED_LONGITUD === 'number'
    && entrega.PED_LATITUD !== 0 && entrega.PED_LONGITUD !== 0;
}

export default function DeliveryDetailScreen({ route, navigation }) {
  const { entrega } = route.params;
  const { t } = useI18n();
  const [photo, setPhoto] = useState(null);
  const [signature, setSignature] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [showSignature, setShowSignature] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);
  const [saving, setSaving] = useState(false);

  const [showCodModal, setShowCodModal] = useState(false);
  const [monto, setMonto] = useState('');
  const [notas, setNotas] = useState('');
  const [savingCod, setSavingCod] = useState(false);
  const isCod = (entrega.PED_FORMA_PAGO || '').toUpperCase() === 'EFECTIVO';

  function handleNavigate() {
    const destination = hasCoords(entrega)
      ? `${entrega.PED_LATITUD},${entrega.PED_LONGITUD}`
      : encodeURIComponent(entrega.PED_DESTINO_DIR || '');
    if (!destination) return;
    // URL universal de Google Maps: si esta instalada la app la abre ahi,
    // si no cae al navegador. No se intenta armar navegacion propia dentro
    // de la app -- eso ya lo resuelve mejor Maps/Waze.
    Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${destination}`).catch(() => {});
  }

  function handleCall() {
    const phone = (entrega.PED_CLIENTE_TELEFONO || '').replace(/[^0-9+]/g, '');
    if (!phone) return;
    Linking.openURL(`tel:${phone}`).catch(() => {});
  }

  async function openCamera() {
    if (!permission?.granted) {
      const res = await requestPermission();
      if (!res.granted) {
        Alert.alert(t('chofer_app.permiso_camara_titulo'), t('chofer_app.permiso_camara_msg'));
        return;
      }
    }
    setShowCamera(true);
  }

  async function takePhoto() {
    if (!cameraRef.current) return;
    const result = await cameraRef.current.takePictureAsync({ quality: 0.5, base64: true });
    setPhoto({ uri: result.uri, base64: result.base64 });
    setShowCamera(false);
  }

  function handleSignatureOK(dataUri) {
    // react-native-signature-canvas devuelve "data:image/png;base64,XXXX"
    setSignature(dataUri);
    setShowSignature(false);
  }

  async function handleMarkDelivered() {
    // Comprobante: foto O firma, cualquiera de las dos alcanza (algunos
    // clientes prefieren firmar en vez de que les fotografien el paquete).
    if (!photo && !signature) {
      Alert.alert(t('chofer_app.falta_foto_titulo'), t('chofer_app.falta_comprobante_desc'));
      return;
    }
    setSaving(true);
    const evidencia = signature ? 'firma_local' : `foto_local:${photo?.uri}`;
    const evidenciaBase64 = signature ? signature.replace(/^data:image\/\w+;base64,/, '') : photo?.base64;
    const evidenciaTipo = signature ? 'image/png' : 'image/jpeg';
    try {
      // Se manda el base64 al backend, que lo sube a Supabase Storage y
      // guarda la URL publica; si el storage no esta configurado, sigue
      // funcionando con la referencia local como antes.
      await api.markDelivered(entrega.ENT_ID, evidencia, evidenciaBase64, evidenciaTipo);
      Alert.alert(t('chofer_app.listo_titulo'), t('chofer_app.entrega_registrada_msg'), [
        { text: t('chofer_app.ok'), onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      if (e.code === 'NETWORK') {
        // Offline: se guarda solo la referencia local, sin base64 (podria
        // ser pesado para guardar en AsyncStorage por mucho tiempo) -- al
        // reconectar se sincroniza el estado de la entrega igual, aunque la
        // foto/firma no se suba a Storage en ese caso particular.
        await enqueue({ type: 'markDelivered', entId: entrega.ENT_ID, evidencia });
        Alert.alert(t('chofer_app.listo_titulo'), t('chofer.entrega_offline'), [
          { text: t('chofer_app.ok'), onPress: () => navigation.goBack() },
        ]);
      } else {
        Alert.alert(t('chofer_app.error_titulo'), translateError(t, e));
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleMarkFailed() {
    Alert.prompt
      ? Alert.prompt(t('chofer_app.motivo_titulo'), t('chofer_app.motivo_desc'), async (motivo) => {
          if (!motivo) return;
          try {
            await api.markFailed(entrega.ENT_ID, motivo);
            navigation.goBack();
          } catch (e) {
            if (e.code === 'NETWORK') {
              await enqueue({ type: 'markFailed', entId: entrega.ENT_ID, motivo });
              Alert.alert(t('chofer_app.listo_titulo'), t('chofer.incidencia_offline'));
              navigation.goBack();
            } else {
              Alert.alert(t('chofer_app.error_titulo'), translateError(t, e));
            }
          }
        })
      : Alert.alert(t('chofer_app.no_disponible_titulo'), t('chofer_app.no_disponible_desc'));
  }

  async function handleCollectCash() {
    const montoNum = parseFloat(monto);
    if (!montoNum || montoNum <= 0) {
      Alert.alert(t('chofer_app.monto_invalido_titulo'), t('chofer_app.monto_invalido_desc'));
      return;
    }
    setSavingCod(true);
    try {
      await api.collectCash(entrega.PED_ID, montoNum, notas);
      setShowCodModal(false);
      Alert.alert(t('chofer_app.listo_titulo'), t('chofer_app.cobro_registrado_msg'));
    } catch (e) {
      Alert.alert(t('chofer_app.error_titulo'), translateError(t, e));
    } finally {
      setSavingCod(false);
    }
  }

  if (showCamera) {
    return (
      <View style={{ flex: 1, backgroundColor: '#000' }}>
        <CameraView ref={cameraRef} style={{ flex: 1 }} facing="back">
          <View style={styles.cameraControls}>
            <TouchableOpacity style={styles.cameraCancelBtn} onPress={() => setShowCamera(false)}>
              <Ionicons name="close" size={26} color="#fff" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.shutterBtn} onPress={takePhoto} />
            <View style={{ width: 46 }} />
          </View>
        </CameraView>
      </View>
    );
  }

  if (showSignature) {
    return (
      <View style={{ flex: 1, backgroundColor: '#fff' }}>
        <SignatureScreen
          onOK={handleSignatureOK}
          onEmpty={() => Alert.alert(t('chofer_app.error_titulo'), t('chofer_app.firma_vacia_desc'))}
          descriptionText={t('chofer_app.firma_instruccion')}
          confirmText={t('chofer_app.guardar')}
          clearText={t('chofer_app.firma_limpiar')}
          webStyle="body,html{background:#fff;} .m-signature-pad{box-shadow:none;border:none;}"
        />
        <TouchableOpacity style={styles.signatureCancelBtn} onPress={() => setShowSignature(false)}>
          <Text style={styles.secondaryButtonText}>{t('chofer_app.cancelar')}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: spacing.md }}>
      <View style={styles.card}>
        <Text style={styles.pedNum}>{entrega.PED_NUMERO || `${t('chofer_app.pedido_prefix')}${entrega.PED_ID}`}</Text>
        <Row icon="person-outline" label={t('chofer_app.cliente_label')} value={entrega.PED_CLIENTE_NOMBRE} />
        <Row icon="location-outline" label={t('chofer_app.destino_label')} value={entrega.PED_DESTINO_DIR} />
        {!!entrega.PED_CLIENTE_TELEFONO && (
          <Row icon="call-outline" label={t('chofer_app.telefono_label')} value={entrega.PED_CLIENTE_TELEFONO} />
        )}
        {isCod && <Row icon="cash-outline" label={t('chofer_app.forma_pago_label')} value={t('chofer_app.efectivo_cobrar')} />}
      </View>

      <View style={{ flexDirection: 'row', gap: 8, marginBottom: spacing.md }}>
        <TouchableOpacity style={[styles.secondaryButton, { flex: 1, marginBottom: 0 }]} onPress={handleNavigate}>
          <Ionicons name="navigate-outline" size={18} color={colors.accent} />
          <Text style={styles.secondaryButtonText}>{t('chofer_app.navegar')}</Text>
        </TouchableOpacity>
        {!!entrega.PED_CLIENTE_TELEFONO && (
          <TouchableOpacity style={[styles.secondaryButton, { flex: 1, marginBottom: 0 }]} onPress={handleCall}>
            <Ionicons name="call-outline" size={18} color={colors.accent} />
            <Text style={styles.secondaryButtonText}>{t('chofer_app.llamar')}</Text>
          </TouchableOpacity>
        )}
      </View>

      {isCod && (
        <TouchableOpacity style={styles.secondaryButton} onPress={() => setShowCodModal(true)}>
          <Ionicons name="cash-outline" size={18} color={colors.accent} />
          <Text style={styles.secondaryButtonText}>{t('chofer_app.registrar_cobro')}</Text>
        </TouchableOpacity>
      )}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>{t('chofer_app.comprobante_titulo')}</Text>
        {photo ? (
          <Image source={{ uri: photo.uri }} style={styles.photoPreview} />
        ) : signature ? (
          <Image source={{ uri: signature }} style={[styles.photoPreview, { backgroundColor: '#fff' }]} resizeMode="contain" />
        ) : (
          <Text style={styles.helperText}>{t('chofer_app.foto_comprobante_desc')}</Text>
        )}
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <TouchableOpacity style={[styles.secondaryButton, { flex: 1 }]} onPress={openCamera}>
            <Ionicons name="camera-outline" size={18} color={colors.accent} />
            <Text style={styles.secondaryButtonText}>{photo ? t('chofer_app.tomar_otra_foto') : t('chofer_app.tomar_foto')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.secondaryButton, { flex: 1 }]} onPress={() => setShowSignature(true)}>
            <Ionicons name="create-outline" size={18} color={colors.accent} />
            <Text style={styles.secondaryButtonText}>{signature ? t('chofer_app.firma_repetir') : t('chofer_app.firma_capturar')}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity style={styles.deliverButton} onPress={handleMarkDelivered} disabled={saving}>
        {saving ? <ActivityIndicator color="#fff" /> : (
          <>
            <Ionicons name="checkmark-circle-outline" size={20} color="#fff" />
            <Text style={styles.deliverButtonText}>{t('chofer_app.marcar_entregado')}</Text>
          </>
        )}
      </TouchableOpacity>

      <TouchableOpacity style={styles.failButton} onPress={handleMarkFailed}>
        <Ionicons name="close-circle-outline" size={18} color={colors.danger} />
        <Text style={styles.failButtonText}>{t('chofer_app.no_pudo_entregar')}</Text>
      </TouchableOpacity>

      <Modal visible={showCodModal} transparent animationType="slide" onRequestClose={() => setShowCodModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.sectionTitle}>{t('chofer_app.cobro_efectivo_titulo')}</Text>
            <TextInput
              style={styles.input}
              placeholder={t('chofer_app.monto_ph')}
              placeholderTextColor={colors.textMuted}
              keyboardType="decimal-pad"
              value={monto}
              onChangeText={setMonto}
            />
            <TextInput
              style={styles.input}
              placeholder={t('chofer_app.notas_ph')}
              placeholderTextColor={colors.textMuted}
              value={notas}
              onChangeText={setNotas}
            />
            <View style={{ flexDirection: 'row', gap: 8, marginTop: spacing.sm }}>
              <TouchableOpacity style={[styles.secondaryButton, { flex: 1 }]} onPress={() => setShowCodModal(false)}>
                <Text style={styles.secondaryButtonText}>{t('chofer_app.cancelar')}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.deliverButton, { flex: 1 }]} onPress={handleCollectCash} disabled={savingCod}>
                {savingCod ? <ActivityIndicator color="#fff" /> : <Text style={styles.deliverButtonText}>{t('chofer_app.guardar')}</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

function Row({ icon, label, value }) {
  return (
    <View style={styles.row}>
      <Ionicons name={icon} size={16} color={colors.textMuted} style={{ marginTop: 2 }} />
      <View style={{ flex: 1, marginLeft: 8 }}>
        <Text style={styles.rowLabel}>{label}</Text>
        <Text style={styles.rowValue}>{value || '-'}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary },
  card: { backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, marginBottom: spacing.md },
  pedNum: { color: colors.textPrimary, fontSize: 17, fontWeight: '700', marginBottom: spacing.sm },
  row: { flexDirection: 'row', marginBottom: spacing.sm },
  rowLabel: { color: colors.textMuted, fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 },
  rowValue: { color: colors.textPrimary, fontSize: 14, marginTop: 2 },
  sectionTitle: { color: colors.textPrimary, fontSize: 14, fontWeight: '600', marginBottom: spacing.sm },
  helperText: { color: colors.textMuted, fontSize: 13, marginBottom: spacing.sm },
  photoPreview: { width: '100%', height: 180, borderRadius: radius.md, marginBottom: spacing.sm, backgroundColor: '#000' },
  secondaryButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, borderWidth: 1, borderColor: colors.accent, borderRadius: radius.md, padding: 12, marginBottom: spacing.md },
  secondaryButtonText: { color: colors.accent, fontWeight: '600', fontSize: 14 },
  deliverButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: colors.success, borderRadius: radius.md, padding: 14, marginBottom: spacing.sm },
  deliverButtonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  failButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, padding: 12, marginBottom: spacing.xl },
  failButtonText: { color: colors.danger, fontWeight: '600', fontSize: 14 },
  cameraControls: { flex: 1, justifyContent: 'flex-end', alignItems: 'center', flexDirection: 'row', paddingHorizontal: spacing.lg, paddingBottom: spacing.xl },
  cameraCancelBtn: { width: 46, height: 46, borderRadius: 23, backgroundColor: 'rgba(0,0,0,0.5)', alignItems: 'center', justifyContent: 'center' },
  shutterBtn: { flex: 1, marginHorizontal: spacing.lg, width: 70, height: 70, borderRadius: 35, backgroundColor: '#fff', borderWidth: 4, borderColor: 'rgba(255,255,255,0.4)', alignSelf: 'center' },
  signatureCancelBtn: { position: 'absolute', top: 40, right: 16, padding: 10 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bgCard, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg },
  input: { backgroundColor: colors.bgPrimary, borderWidth: 1, borderColor: colors.borderPrimary, borderRadius: radius.md, padding: 12, color: colors.textPrimary, fontSize: 15, marginBottom: spacing.sm },
});
