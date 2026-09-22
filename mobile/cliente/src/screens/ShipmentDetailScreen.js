import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, Polyline } from 'react-native-maps';
import { useTheme } from '../theme-context';
import Card from '../shared/components/Card';
import Badge from '../shared/components/Badge';
import Button from '../shared/components/Button';
import { get, del } from '../shared/api';
import { formatCurrency, formatDateTime, formatPhone } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

const { height } = Dimensions.get('window');
const MAP_HEIGHT = height * 0.3;

const TIMELINE_STEPS = [
  { key: 'PENDIENTE', label: 'Orden creada', icon: 'document-text' },
  { key: 'ASIGNADO', label: 'Recogido', icon: 'cube' },
  { key: 'EN_RUTA', label: 'En tránsito', icon: 'car' },
  { key: 'EN_RUTA', label: 'Fuera para entrega', icon: 'bicycle' },
  { key: 'ENTREGADO', label: 'Entregado', icon: 'checkmark-circle' },
];

function getStepIndex(status) {
  const map = { PENDIENTE: 0, ASIGNADO: 1, EN_RUTA: 2, ENTREGADO: 4, CANCELADO: -1, FALLIDO: -1 };
  return map[status] ?? 0;
}

export default function ShipmentDetailScreen({ route, navigation }) {
  const { theme } = useTheme();
  const { shipmentId } = route.params || {};
  const [shipment, setShipment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    fetchShipment();
  }, [shipmentId]);

  const fetchShipment = async () => {
    try {
      setLoading(true);
      const data = await get(`/api/shipments/${shipmentId}`);
      setShipment(data);
    } catch (error) {
      Alert.alert('Error', 'No se pudo cargar el envío');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  const handleCallDriver = () => {
    if (shipment?.driver_phone) {
      Linking.openURL(`tel:${shipment.driver_phone}`);
    } else {
      Alert.alert('Sin chofer', 'Aún no se ha asignado un chofer a este envío.');
    }
  };

  const handleCancel = () => {
    Alert.alert(
      'Cancelar envío',
      '¿Estás seguro de que deseas cancelar este envío? Esta acción no se puede deshacer.',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Sí, cancelar',
          style: 'destructive',
          onPress: async () => {
            setCancelling(true);
            try {
              await del(`/api/shipments/${shipmentId}`);
              Alert.alert('Cancelado', 'El envío ha sido cancelado.', [
                { text: 'OK', onPress: () => navigation.goBack() },
              ]);
            } catch (error) {
              Alert.alert('Error', error?.message || 'No se pudo cancelar el envío');
            } finally {
              setCancelling(false);
            }
          },
        },
      ]
    );
  };

  const handleShareTracking = () => {
    const tracking = shipment?.tracking_number || shipment?.folio || shipmentId;
    const url = `https://lastmile-platform.onrender.com/tracking/${tracking}`;
    Alert.alert(
      'Compartir tracking',
      `Número de rastreo: ${tracking}\n\n${url}`,
      [{ text: 'Cerrar' }]
    );
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
    );
  }

  if (!shipment) return null;

  const currentStep = getStepIndex(shipment.status);
  const origin = shipment.origin_address || shipment.origen || '—';
  const destination = shipment.destination_address || shipment.destino || '—';

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Map */}
        <View style={styles.mapContainer}>
          <MapView
            style={styles.map}
            initialRegion={{
              latitude: shipment.origin_lat || 19.4326,
              longitude: shipment.origin_lng || -99.1332,
              latitudeDelta: 0.05,
              longitudeDelta: 0.05,
            }}
            scrollEnabled={false}
          >
            <Marker
              coordinate={{
                latitude: shipment.origin_lat || 19.4326,
                longitude: shipment.origin_lng || -99.1332,
              }}
              title="Origen"
              pinColor={colors.primary[500]}
            />
            <Marker
              coordinate={{
                latitude: shipment.dest_lat || 19.45,
                longitude: shipment.dest_lng || -99.15,
              }}
              title="Destino"
              pinColor={colors.success[500]}
            />
            {shipment.driver_lat && shipment.driver_lng && (
              <Marker
                coordinate={{
                  latitude: shipment.driver_lat,
                  longitude: shipment.driver_lng,
                }}
                title="Chofer"
              >
                <View style={styles.driverMarker}>
                  <Ionicons name="car" size={16} color="#fff" />
                </View>
              </Marker>
            )}
          </MapView>

          {/* Back button overlay */}
          <TouchableOpacity
            style={styles.backOverlay}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color={theme.text} />
          </TouchableOpacity>
        </View>

        <View style={styles.content}>
          {/* Status Card */}
          <Card style={[styles.statusCard, { backgroundColor: theme.surface }]}>
            <View style={styles.statusHeader}>
              <View>
                <Text style={[styles.trackingLabel, { color: theme.textSecondary }]}>
                  Tracking
                </Text>
                <Text style={[styles.trackingNumber, { color: theme.text }]}>
                  {shipment.tracking_number || shipment.folio || '—'}
                </Text>
              </View>
              <Badge status={shipment.status || 'PENDIENTE'} />
            </View>

            <View style={styles.routeContainer}>
              <View style={styles.routePoint}>
                <View style={[styles.routeDot, { backgroundColor: colors.primary[500] }]} />
                <View style={styles.routeTextContainer}>
                  <Text style={[styles.routeLabel, { color: theme.textSecondary }]}>Origen</Text>
                  <Text style={[styles.routeAddress, { color: theme.text }]} numberOfLines={2}>
                    {origin}
                  </Text>
                </View>
              </View>
              <View style={styles.routeLineContainer}>
                <View style={[styles.routeLine, { backgroundColor: theme.border }]} />
                <Ionicons name="airplane" size={16} color={theme.primary} />
                <View style={[styles.routeLine, { backgroundColor: theme.border }]} />
              </View>
              <View style={styles.routePoint}>
                <View style={[styles.routeDot, { backgroundColor: colors.success[500] }]} />
                <View style={styles.routeTextContainer}>
                  <Text style={[styles.routeLabel, { color: theme.textSecondary }]}>Destino</Text>
                  <Text style={[styles.routeAddress, { color: theme.text }]} numberOfLines={2}>
                    {destination}
                  </Text>
                </View>
              </View>
            </View>
          </Card>

          {/* Timeline */}
          <Card style={[styles.timelineCard, { backgroundColor: theme.surface }]}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>Progreso</Text>
            {TIMELINE_STEPS.map((step, index) => {
              const isCompleted = index <= currentStep;
              const isCurrent = index === currentStep;
              const isLast = index === TIMELINE_STEPS.length - 1;

              return (
                <View key={index} style={styles.timelineStep}>
                  <View style={styles.timelineLeft}>
                    <View
                      style={[
                        styles.timelineIcon,
                        {
                          backgroundColor: isCompleted ? colors.primary[500] : colors.neutral[200],
                          borderColor: isCurrent ? colors.primary[300] : 'transparent',
                        },
                      ]}
                    >
                      {isCompleted ? (
                        <Ionicons
                          name={step.icon}
                          size={16}
                          color="#fff"
                        />
                      ) : (
                        <View style={styles.timelineEmptyDot} />
                      )}
                    </View>
                    {!isLast && (
                      <View
                        style={[
                          styles.timelineConnector,
                          {
                            backgroundColor:
                              index < currentStep ? colors.primary[500] : colors.neutral[200],
                          },
                        ]}
                      />
                    )}
                  </View>
                  <View style={styles.timelineContent}>
                    <Text
                      style={[
                        styles.timelineLabel,
                        {
                          color: isCompleted ? theme.text : theme.textDisabled,
                          fontWeight: isCurrent ? '700' : '500',
                        },
                      ]}
                    >
                      {step.label}
                    </Text>
                    {isCurrent && (
                      <Text style={[styles.timelineCurrent, { color: theme.primary }]}>
                        Estado actual
                      </Text>
                    )}
                  </View>
                </View>
              );
            })}
          </Card>

          {/* Driver Info */}
          {shipment.driver_name && (
            <Card style={[styles.driverCard, { backgroundColor: theme.surface }]}>
              <Text style={[styles.cardTitle, { color: theme.text }]}>Tu chofer</Text>
              <View style={styles.driverInfo}>
                <View style={[styles.driverAvatar, { backgroundColor: colors.primary[100] }]}>
                  <Ionicons name="person" size={24} color={colors.primary[500]} />
                </View>
                <View style={styles.driverDetails}>
                  <Text style={[styles.driverName, { color: theme.text }]}>
                    {shipment.driver_name}
                  </Text>
                  {shipment.driver_phone && (
                    <Text style={[styles.driverPhone, { color: theme.textSecondary }]}>
                      {formatPhone(shipment.driver_phone)}
                    </Text>
                  )}
                </View>
                <TouchableOpacity style={styles.callButton} onPress={handleCallDriver}>
                  <Ionicons name="call" size={20} color="#fff" />
                </TouchableOpacity>
              </View>
            </Card>
          )}

          {/* Shipment Info */}
          <Card style={[styles.infoCard, { backgroundColor: theme.surface }]}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>Detalles</Text>
            {shipment.description && (
              <View style={styles.infoRow}>
                <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Contenido</Text>
                <Text style={[styles.infoValue, { color: theme.text }]}>{shipment.description}</Text>
              </View>
            )}
            {shipment.weight_kg && (
              <View style={styles.infoRow}>
                <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Peso</Text>
                <Text style={[styles.infoValue, { color: theme.text }]}>{shipment.weight_kg} kg</Text>
              </View>
            )}
            {shipment.service_type && (
              <View style={styles.infoRow}>
                <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Servicio</Text>
                <Text style={[styles.infoValue, { color: theme.text }]}>
                  {shipment.service_type.charAt(0).toUpperCase() + shipment.service_type.slice(1)}
                </Text>
              </View>
            )}
            {shipment.declared_value > 0 && (
              <View style={styles.infoRow}>
                <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Valor declarado</Text>
                <Text style={[styles.infoValue, { color: theme.text }]}>
                  {formatCurrency(shipment.declared_value)}
                </Text>
              </View>
            )}
            {shipment.created_at && (
              <View style={styles.infoRow}>
                <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Creado</Text>
                <Text style={[styles.infoValue, { color: theme.text }]}>
                  {formatDateTime(shipment.created_at)}
                </Text>
              </View>
            )}
          </Card>

          {/* Actions */}
          <View style={styles.actions}>
            <Button
              title="Llamar chofer"
              onPress={handleCallDriver}
              variant="secondary"
              icon={<Ionicons name="call-outline" size={18} color={colors.primary[500]} />}
              style={styles.actionButton}
            />
            <Button
              title="Compartir"
              onPress={handleShareTracking}
              variant="secondary"
              icon={<Ionicons name="share-outline" size={18} color={colors.primary[500]} />}
              style={styles.actionButton}
            />
          </View>

          {shipment.status !== 'ENTREGADO' && shipment.status !== 'CANCELADO' && (
            <Button
              title="Cancelar envío"
              onPress={handleCancel}
              variant="danger"
              loading={cancelling}
              disabled={cancelling}
              style={styles.cancelButton}
            />
          )}

          <View style={{ height: 40 }} />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mapContainer: {
    height: MAP_HEIGHT,
    position: 'relative',
  },
  map: {
    flex: 1,
  },
  backOverlay: {
    position: 'absolute',
    top: spacing[10],
    left: spacing[4],
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.md,
  },
  driverMarker: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#fff',
    ...shadows.md,
  },
  content: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[4],
  },
  statusCard: {
    marginBottom: spacing[4],
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing[4],
  },
  trackingLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  trackingNumber: {
    fontSize: typography.fontSize.xl,
    fontWeight: '800',
    marginTop: 2,
  },
  routeContainer: {
    gap: spacing[2],
  },
  routePoint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing[3],
  },
  routeDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginTop: 5,
  },
  routeTextContainer: {
    flex: 1,
  },
  routeLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  routeAddress: {
    fontSize: typography.fontSize.base,
    fontWeight: '500',
    marginTop: 2,
  },
  routeLineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 4,
    gap: spacing[2],
  },
  routeLine: {
    flex: 1,
    height: 2,
  },
  timelineCard: {
    marginBottom: spacing[4],
  },
  cardTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: '700',
    marginBottom: spacing[4],
  },
  timelineStep: {
    flexDirection: 'row',
    marginBottom: 0,
  },
  timelineLeft: {
    alignItems: 'center',
    width: 32,
  },
  timelineIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
  },
  timelineEmptyDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.neutral[300],
  },
  timelineConnector: {
    width: 2,
    flex: 1,
    minHeight: 24,
  },
  timelineContent: {
    flex: 1,
    paddingBottom: spacing[4],
    paddingLeft: spacing[3],
  },
  timelineLabel: {
    fontSize: typography.fontSize.base,
  },
  timelineCurrent: {
    fontSize: typography.fontSize.xs,
    fontWeight: '600',
    marginTop: 2,
  },
  driverCard: {
    marginBottom: spacing[4],
  },
  driverInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[3],
  },
  driverAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  driverDetails: {
    flex: 1,
  },
  driverName: {
    fontSize: typography.fontSize.base,
    fontWeight: '600',
  },
  driverPhone: {
    fontSize: typography.fontSize.sm,
    marginTop: 2,
  },
  callButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.success[500],
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.sm,
  },
  infoCard: {
    marginBottom: spacing[4],
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: spacing[2],
    borderBottomWidth: 1,
    borderBottomColor: colors.neutral[100],
  },
  infoLabel: {
    fontSize: typography.fontSize.sm,
    flex: 1,
  },
  infoValue: {
    fontSize: typography.fontSize.sm,
    fontWeight: '500',
    flex: 1.5,
    textAlign: 'right',
  },
  actions: {
    flexDirection: 'row',
    gap: spacing[3],
    marginBottom: spacing[3],
  },
  actionButton: {
    flex: 1,
  },
  cancelButton: {
    width: '100%',
  },
});
