import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
  Image,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme-context';
import Card from '../shared/components/Card';
import Button from '../shared/components/Button';
import Badge from '../shared/components/Badge';
import { get, put, post } from '../shared/api';
import { formatCurrency, formatPhone, formatDateTime } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

const TIMELINE_STEPS = [
  { key: 'created', label: 'Creada', icon: 'document-text-outline' },
  { key: 'assigned', label: 'Asignada', icon: 'person-outline' },
  { key: 'picked_up', label: 'Recogida', icon: 'cube-outline' },
  { key: 'in_transit', label: 'En Tránsito', icon: 'navigate-outline' },
  { key: 'delivered', label: 'Entregada', icon: 'checkmark-circle-outline' },
];

export default function DeliveryDetailScreen({ route, navigation }) {
  const { deliveryId } = route.params;
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [delivery, setDelivery] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [showCodModal, setShowCodModal] = useState(false);
  const [codAmount, setCodAmount] = useState('');
  const [codLoading, setCodLoading] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportNotes, setReportNotes] = useState('');
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    fetchDelivery();
  }, [deliveryId]);

  const fetchDelivery = async () => {
    try {
      const data = await get(`/api/deliveries/${deliveryId}`);
      setDelivery(data);
      if (data?.evidence_photos) {
        setPhotos(data.evidence_photos);
      }
    } catch (error) {
      console.error('Error fetching delivery:', error);
      Alert.alert('Error', 'No se pudo cargar la entrega');
    } finally {
      setLoading(false);
    }
  };

  const handleStartRoute = async () => {
    Alert.alert(
      'Iniciar Ruta',
      '¿Deseas iniciar la ruta de entrega? Se activará el rastreo GPS.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Iniciar',
          onPress: async () => {
            setUpdating(true);
            try {
              await put(`/api/deliveries/${deliveryId}/status`, { status: 'EN_RUTA' });
              await fetchDelivery();
              Alert.alert('Éxito', 'Ruta iniciada correctamente');
            } catch (error) {
              Alert.alert('Error', 'No se pudo iniciar la ruta');
            } finally {
              setUpdating(false);
            }
          },
        },
      ]
    );
  };

  const handleCallClient = () => {
    const phone = delivery?.telefono || delivery?.phone || delivery?.cliente_phone;
    if (phone) {
      Linking.openURL(`tel:${phone}`);
    } else {
      Alert.alert('Sin teléfono', 'No hay número de teléfono registrado');
    }
  };

  const handleOpenMaps = () => {
    const lat = delivery?.destino_lat || delivery?.lat;
    const lng = delivery?.destino_lng || delivery?.lng;
    const address = delivery?.direccion || delivery?.address || '';
    if (lat && lng) {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      Linking.openURL(url);
    } else if (address) {
      const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
      Linking.openURL(url);
    }
  };

  const handleCaptureEvidence = async () => {
    try {
      const { ImagePicker } = await import('expo-image-picker');
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
        allowsEditing: false,
      });

      if (!result.canceled && result.assets?.[0]) {
        const photoUri = result.assets[0].uri;
        setPhotos((prev) => [...prev, { uri: photoUri, timestamp: new Date().toISOString() }]);
        Alert.alert('Evidencia', 'Foto capturada correctamente');
      }
    } catch (error) {
      console.error('Camera error:', error);
      Alert.alert('Error', 'No se pudo acceder a la cámara');
    }
  };

  const handleCompleteDelivery = () => {
    const requiresCod = delivery?.metodo_pago === 'COD' || delivery?.payment_method === 'COD';
    if (requiresCod) {
      setShowCodModal(true);
    } else {
      confirmComplete();
    }
  };

  const confirmComplete = async (codData = null) => {
    setUpdating(true);
    try {
      const payload = {
        status: 'ENTREGADO',
        evidence_photos: photos.map((p) => p.uri),
      };
      if (codData) {
        payload.cod_amount = codData.amount;
        payload.cod_collected = true;
      }
      await put(`/api/deliveries/${deliveryId}/status`, payload);
      await fetchDelivery();
      setShowCodModal(false);
      Alert.alert('Éxito', 'Entrega completada correctamente');
    } catch (error) {
      Alert.alert('Error', 'No se pudo completar la entrega');
    } finally {
      setUpdating(false);
    }
  };

  const handleConfirmCod = () => {
    const amount = parseFloat(codAmount);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert('Monto inválido', 'Ingresa un monto válido');
      return;
    }
    setCodLoading(true);
    setTimeout(() => {
      confirmComplete({ amount });
      setCodLoading(false);
    }, 500);
  };

  const handleReportProblem = () => {
    setShowReportModal(true);
  };

  const submitReport = async () => {
    if (!reportNotes.trim()) {
      Alert.alert('Nota requerida', 'Describe el problema');
      return;
    }
    setReportLoading(true);
    try {
      await post(`/api/deliveries/${deliveryId}/report`, {
        notes: reportNotes,
        status: 'FALLIDO',
      });
      await fetchDelivery();
      setShowReportModal(false);
      setReportNotes('');
      Alert.alert('Reporte enviado', 'El problema ha sido reportado');
    } catch (error) {
      Alert.alert('Error', 'No se pudo enviar el reporte');
    } finally {
      setReportLoading(false);
    }
  };

  const getTimelineIndex = () => {
    const status = delivery?.status;
    const map = { PENDIENTE: 0, ASIGNADO: 1, EN_RUTA: 3, ENTREGADO: 4 };
    return map[status] ?? 0;
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
    );
  }

  if (!delivery) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <Text style={{ color: theme.text }}>Entrega no encontrada</Text>
      </View>
    );
  }

  const currentStep = getTimelineIndex();

  return (
    <View style={[styles.container, { backgroundColor: theme.background, paddingTop: insets.top }]}>
      <View style={[styles.topBar, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={[styles.topBarTitle, { color: theme.text }]}>Detalle de Entrega</Text>
        <Badge status={delivery.status} size="sm" />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={[styles.mapContainer, { backgroundColor: theme.surfaceVariant }]}>
          <View style={styles.mapPlaceholder}>
            <Ionicons name="location" size={48} color={theme.primary} />
            <Text style={[styles.mapPlaceholderText, { color: theme.textSecondary }]}>
              {delivery.direccion || delivery.address || 'Ubicación de entrega'}
            </Text>
          </View>
          <TouchableOpacity style={styles.mapOverlay} onPress={handleOpenMaps}>
            <Ionicons name="open-outline" size={16} color={theme.primary} />
            <Text style={[styles.mapOverlayText, { color: theme.primary }]}>Abrir en Maps</Text>
          </TouchableOpacity>
        </View>

        <Card style={[styles.infoCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}>
          <View style={styles.infoHeader}>
            <View>
              <Text style={[styles.deliveryLabel, { color: theme.textSecondary }]}>Entrega #{delivery.id || delivery._id}</Text>
              <Text style={[styles.clientName, { color: theme.text }]}>
                {delivery.cliente_nombre || delivery.client_name || 'Cliente'}
              </Text>
            </View>
            <Text style={[styles.amount, { color: colors.success[600] }]}>
              {formatCurrency(delivery.monto || delivery.amount || 0)}
            </Text>
          </View>

          <View style={styles.infoDetails}>
            <InfoRow icon="call-outline" label="Teléfono" value={formatPhone(delivery.telefono || delivery.phone || '')} theme={theme} onPress={handleCallClient} />
            <InfoRow icon="location-outline" label="Dirección" value={delivery.direccion || delivery.address || 'Sin dirección'} theme={theme} />
            <InfoRow icon="cash-outline" label="Pago" value={delivery.metodo_pago || delivery.payment_method || 'Efectivo'} theme={theme} />
            <InfoRow icon="time-outline" label="Hora" value={formatDateTime(delivery.created_at || delivery.fecha)} theme={theme} />
          </View>
        </Card>

        <Card style={[styles.timelineCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Estado de la entrega</Text>
          <View style={styles.timeline}>
            {TIMELINE_STEPS.map((step, index) => {
              const isCompleted = index <= currentStep;
              const isCurrent = index === currentStep;
              return (
                <View key={step.key} style={styles.timelineStep}>
                  <View style={styles.timelineLeft}>
                    <View
                      style={[
                        styles.timelineDot,
                        {
                          backgroundColor: isCompleted ? theme.primary : theme.surfaceVariant,
                          borderColor: isCurrent ? theme.primary : 'transparent',
                          borderWidth: isCurrent ? 3 : 0,
                        },
                      ]}
                    >
                      <Ionicons
                        name={step.icon}
                        size={14}
                        color={isCompleted ? '#ffffff' : theme.textDisabled}
                      />
                    </View>
                    {index < TIMELINE_STEPS.length - 1 && (
                      <View
                        style={[
                          styles.timelineLine,
                          { backgroundColor: index < currentStep ? theme.primary : theme.border },
                        ]}
                      />
                    )}
                  </View>
                  <Text
                    style={[
                      styles.timelineLabel,
                      { color: isCompleted ? theme.text : theme.textDisabled },
                    ]}
                  >
                    {step.label}
                  </Text>
                </View>
              );
            })}
          </View>
        </Card>

        {photos.length > 0 && (
          <Card style={[styles.photosCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Evidencia ({photos.length})</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {photos.map((photo, index) => (
                <Image key={index} source={{ uri: photo.uri || photo }} style={styles.photoThumb} />
              ))}
            </ScrollView>
          </Card>
        )}

        <View style={styles.actionsGrid}>
          {delivery.status !== 'ENTREGADO' && delivery.status !== 'CANCELADO' && (
            <>
              <ActionButton
                icon="navigate"
                label="Iniciar Ruta"
                color="#2563eb"
                onPress={handleStartRoute}
                disabled={delivery.status === 'EN_RUTA'}
                theme={theme}
              />
              <ActionButton
                icon="call"
                label="Llamar"
                color={colors.success[500]}
                onPress={handleCallClient}
                theme={theme}
              />
              <ActionButton
                icon="map"
                label="Maps"
                color={colors.accent[500]}
                onPress={handleOpenMaps}
                theme={theme}
              />
              <ActionButton
                icon="camera"
                label="Evidencia"
                color={colors.primary[500]}
                onPress={handleCaptureEvidence}
                theme={theme}
              />
              <ActionButton
                icon="checkmark-done"
                label="Entregado"
                color={colors.success[600]}
                onPress={handleCompleteDelivery}
                theme={theme}
              />
              <ActionButton
                icon="alert"
                label="Reportar"
                color={colors.error[500]}
                onPress={handleReportProblem}
                theme={theme}
              />
            </>
          )}
        </View>
      </ScrollView>

      <Modal visible={showCodModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.surface }]}>
            <Text style={[styles.modalTitle, { color: theme.text }]}>Cobro contra entrega (COD)</Text>
            <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
              Monto a cobrar: {formatCurrency(delivery.monto || delivery.amount || 0)}
            </Text>
            <TextInput
              style={[styles.modalInput, { color: theme.text, borderColor: theme.border }]}
              placeholder="0.00"
              placeholderTextColor={theme.textDisabled}
              keyboardType="decimal-pad"
              value={codAmount}
              onChangeText={setCodAmount}
              autoFocus
            />
            <View style={styles.modalActions}>
              <Button
                title="Cancelar"
                variant="ghost"
                onPress={() => setShowCodModal(false)}
                style={styles.modalBtn}
              />
              <Button
                title="Confirmar Cobro"
                onPress={handleConfirmCod}
                loading={codLoading}
                style={styles.modalBtn}
              />
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={showReportModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.surface }]}>
            <Text style={[styles.modalTitle, { color: theme.text }]}>Reportar Problema</Text>
            <TextInput
              style={[styles.modalInput, styles.modalTextArea, { color: theme.text, borderColor: theme.border }]}
              placeholder="Describe el problema..."
              placeholderTextColor={theme.textDisabled}
              multiline
              numberOfLines={4}
              value={reportNotes}
              onChangeText={setReportNotes}
              textAlignVertical="top"
            />
            <View style={styles.modalActions}>
              <Button
                title="Cancelar"
                variant="ghost"
                onPress={() => setShowReportModal(false)}
                style={styles.modalBtn}
              />
              <Button
                title="Enviar Reporte"
                variant="danger"
                onPress={submitReport}
                loading={reportLoading}
                style={styles.modalBtn}
              />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function InfoRow({ icon, label, value, theme, onPress }) {
  return (
    <TouchableOpacity style={styles.infoRow} onPress={onPress} disabled={!onPress}>
      <Ionicons name={icon} size={18} color={theme.textSecondary} />
      <View style={styles.infoRowContent}>
        <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>{label}</Text>
        <Text style={[styles.infoValue, { color: theme.text }]} numberOfLines={1}>{value}</Text>
      </View>
      {onPress && <Ionicons name="chevron-forward" size={16} color={theme.textDisabled} />}
    </TouchableOpacity>
  );
}

function ActionButton({ icon, label, color, onPress, disabled, theme }) {
  return (
    <TouchableOpacity
      style={[styles.actionBtn, { backgroundColor: theme.surfaceVariant }, disabled && { opacity: 0.5 }]}
      onPress={onPress}
      disabled={disabled}
    >
      <View style={[styles.actionIcon, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon} size={22} color={color} />
      </View>
      <Text style={[styles.actionLabel, { color: theme.text }]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[3],
    borderBottomWidth: 1,
  },
  backBtn: { padding: spacing[2] },
  topBarTitle: { fontSize: typography.fontSize.lg, fontWeight: '700', flex: 1, textAlign: 'center' },
  scrollContent: { paddingBottom: 40 },
  mapContainer: { height: 200, margin: spacing[4], borderRadius: borderRadius.lg, overflow: 'hidden' },
  mapPlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing[4] },
  mapPlaceholderText: { fontSize: typography.fontSize.sm, textAlign: 'center', marginTop: spacing[2] },
  mapOverlay: {
    position: 'absolute',
    bottom: spacing[3],
    right: spacing[3],
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    paddingHorizontal: spacing[3],
    paddingVertical: spacing[2],
    borderRadius: borderRadius.md,
    ...shadows.sm,
  },
  mapOverlayText: { fontSize: typography.fontSize.sm, fontWeight: '600', marginLeft: spacing[1] },
  infoCard: { marginHorizontal: spacing[4], marginBottom: spacing[3] },
  infoHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing[4] },
  deliveryLabel: { fontSize: typography.fontSize.xs, marginBottom: 2 },
  clientName: { fontSize: typography.fontSize.xl, fontWeight: '700' },
  amount: { fontSize: typography.fontSize.xl, fontWeight: '800' },
  infoDetails: {},
  infoRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing[3], borderBottomWidth: 1, borderBottomColor: colors.neutral[100] },
  infoRowContent: { flex: 1, marginLeft: spacing[3] },
  infoLabel: { fontSize: typography.fontSize.xs },
  infoValue: { fontSize: typography.fontSize.base, fontWeight: '500', marginTop: 2 },
  timelineCard: { marginHorizontal: spacing[4], marginBottom: spacing[3] },
  sectionTitle: { fontSize: typography.fontSize.lg, fontWeight: '700', marginBottom: spacing[4] },
  timeline: {},
  timelineStep: { flexDirection: 'row', alignItems: 'flex-start', minHeight: 48 },
  timelineLeft: { alignItems: 'center', width: 32, marginRight: spacing[3] },
  timelineDot: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  timelineLine: { width: 2, flex: 1, minHeight: 16, marginTop: 4 },
  timelineLabel: { fontSize: typography.fontSize.base, fontWeight: '500', paddingTop: 7 },
  photosCard: { marginHorizontal: spacing[4], marginBottom: spacing[3] },
  photoThumb: { width: 100, height: 100, borderRadius: borderRadius.md, marginRight: spacing[2] },
  actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: spacing[4], justifyContent: 'space-between' },
  actionBtn: { width: '31%', alignItems: 'center', paddingVertical: spacing[4], borderRadius: borderRadius.lg, marginBottom: spacing[3] },
  actionIcon: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: spacing[2] },
  actionLabel: { fontSize: typography.fontSize.xs, fontWeight: '600' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { borderTopLeftRadius: borderRadius.xl, borderTopRightRadius: borderRadius.xl, padding: spacing[6], paddingBottom: 40 },
  modalTitle: { fontSize: typography.fontSize.xl, fontWeight: '700', marginBottom: spacing[2] },
  modalSubtitle: { fontSize: typography.fontSize.base, marginBottom: spacing[4] },
  modalInput: { borderWidth: 1.5, borderRadius: borderRadius.md, padding: spacing[3], fontSize: typography.fontSize.lg, marginBottom: spacing[4] },
  modalTextArea: { height: 120 },
  modalActions: { flexDirection: 'row', justifyContent: 'space-between' },
  modalBtn: { flex: 1, marginHorizontal: spacing[2] },
});
