import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n, translateError } from '../i18n';
import { api } from '../api';
import { flushQueue } from '../services/offlineQueue';

function hasCoords(item) {
  return typeof item.PED_LATITUD === 'number' && typeof item.PED_LONGITUD === 'number'
    && item.PED_LATITUD !== 0 && item.PED_LONGITUD !== 0;
}

export default function DeliveriesScreen({ navigation }) {
  const { choferProfile, profileError, reloadProfile } = useAuth();
  const { t } = useI18n();
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [routeStarted, setRouteStarted] = useState(false);
  const [etaByPedId, setEtaByPedId] = useState({});

  const ESTADO_LABEL = {
    PENDIENTE: t('chofer_app.estado_pendiente'),
    EN_RUTA: t('chofer_app.estado_en_ruta'),
    ENTREGADO: t('chofer_app.estado_entregado'),
    NO_ENTREGADO: t('chofer_app.estado_no_entregado'),
  };

  const ESTADO_COLOR = {
    PENDIENTE: colors.warning,
    EN_RUTA: colors.info,
    ENTREGADO: colors.success,
    NO_ENTREGADO: colors.danger,
  };

  const load = useCallback(async () => {
    if (!choferProfile) return;
    try {
      // Reintenta primero lo que haya quedado pendiente por falta de red
      // (marcar entregado/fallido offline) antes de traer la lista fresca,
      // asi el chofer ve el resultado ya aplicado si el reintento funciono.
      await flushQueue().catch(() => {});
      const res = await api.getMyDeliveries(choferProfile.CHO_ID);
      const pendientes = (res.data || []).filter(e => e.ENT_ESTADO !== 'ENTREGADO' && e.ENT_ESTADO !== 'NO_ENTREGADO');
      setDeliveries(pendientes);
    } catch (e) {
      console.warn('Error cargando entregas:', e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [choferProfile]);

  useEffect(() => {
    load();
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    setRouteStarted(false);
    setEtaByPedId({});
    await reloadProfile();
    await load();
  }

  async function handleIniciarRuta() {
    const withCoords = deliveries.filter(hasCoords);
    if (withCoords.length === 0) {
      Alert.alert(t('chofer_app.sin_coordenadas_titulo'), t('chofer_app.sin_coordenadas_desc'));
      return;
    }
    setOptimizing(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(t('chofer_app.error_titulo'), t('chofer_app.location_permission_denied'));
        return;
      }
      const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const origin = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      const payload = withCoords.map(d => ({
        id: d.PED_ID,
        lat: d.PED_LATITUD,
        lng: d.PED_LONGITUD,
        priority: (d.PED_PRIORIDAD || 'normal').toLowerCase(),
      }));

      const res = await api.optimizeRoute(origin, payload);
      const route = res.result?.route || [];
      if (route.length === 0) throw new Error('empty route');

      const etaMap = {};
      route.forEach(stop => { etaMap[stop.id] = stop.cumulative_eta; });
      setEtaByPedId(etaMap);

      const withoutCoords = deliveries.filter(d => !hasCoords(d));
      const ordered = route
        .map(stop => deliveries.find(d => d.PED_ID === stop.id))
        .filter(Boolean)
        .concat(withoutCoords);
      setDeliveries(ordered);

      const firstPedId = route[0].id;
      try {
        await api.updatePedidoEstado(firstPedId, 'EN_RUTA');
      } catch (e) {
        // No bloquea el resto del flujo: la ruta ya se optimizo y se muestra,
        // aunque el aviso al cliente de "en camino" haya fallado.
        console.warn('No se pudo marcar EN_RUTA:', e.message);
      }
      setRouteStarted(true);
    } catch (e) {
      Alert.alert(t('chofer_app.error_titulo'), translateError(t, e));
    } finally {
      setOptimizing(false);
    }
  }

  if (profileError) {
    return (
      <View style={styles.center}>
        <Ionicons name="alert-circle-outline" size={48} color={colors.warning} />
        <Text style={styles.emptyTitle}>{t('chofer_app.sin_perfil_titulo')}</Text>
        <Text style={styles.emptyText}>{t('chofer_app.sin_perfil_desc')}</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {deliveries.length > 0 && (
        <TouchableOpacity
          style={[styles.routeButton, routeStarted && styles.routeButtonActive]}
          onPress={handleIniciarRuta}
          disabled={optimizing}
        >
          {optimizing ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Ionicons name={routeStarted ? 'navigate' : 'navigate-outline'} size={18} color="#fff" />
          )}
          <Text style={styles.routeButtonText}>
            {optimizing ? t('chofer_app.optimizando_ruta') : routeStarted ? t('chofer_app.ruta_iniciada') : t('chofer_app.iniciar_ruta')}
          </Text>
        </TouchableOpacity>
      )}
      <FlatList
        data={deliveries}
        keyExtractor={(item) => String(item.ENT_ID)}
        contentContainerStyle={{ padding: spacing.md }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
        ListEmptyComponent={
          <View style={styles.center}>
            <Ionicons name="cube-outline" size={48} color={colors.textMuted} />
            <Text style={styles.emptyTitle}>{t('chofer_app.sin_entregas_titulo')}</Text>
            <Text style={styles.emptyText}>{t('chofer_app.sin_entregas_desc')}</Text>
          </View>
        }
        renderItem={({ item, index }) => (
          <TouchableOpacity
            style={[styles.card, { borderLeftColor: ESTADO_COLOR[item.ENT_ESTADO] || colors.borderPrimary }]}
            onPress={() => navigation.navigate('DeliveryDetail', { entrega: item })}
          >
            <View style={styles.cardHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 }}>
                {routeStarted && hasCoords(item) && (
                  <View style={styles.stopBadge}>
                    <Text style={styles.stopBadgeText}>{index + 1}</Text>
                  </View>
                )}
                <Text style={styles.cardNumber}>{item.PED_NUMERO || `${t('chofer_app.pedido_prefix')}${item.PED_ID}`}</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: `${ESTADO_COLOR[item.ENT_ESTADO] || colors.textMuted}22` }]}>
                <Text style={[styles.badgeText, { color: ESTADO_COLOR[item.ENT_ESTADO] || colors.textMuted }]}>
                  {ESTADO_LABEL[item.ENT_ESTADO] || item.ENT_ESTADO}
                </Text>
              </View>
            </View>
            <Text style={styles.cardClient}>{item.PED_CLIENTE_NOMBRE}</Text>
            <Text style={styles.cardAddress} numberOfLines={2}>{item.PED_DESTINO_DIR}</Text>
            {routeStarted && etaByPedId[item.PED_ID] != null && (
              <View style={styles.etaRow}>
                <Ionicons name="time-outline" size={13} color={colors.accent} />
                <Text style={styles.etaText}>{etaByPedId[item.PED_ID]} {t('chofer_app.eta_min')}</Text>
              </View>
            )}
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyTitle: { color: colors.textPrimary, fontSize: 16, fontWeight: '600', marginTop: spacing.md, textAlign: 'center' },
  emptyText: { color: colors.textMuted, fontSize: 13, marginTop: spacing.xs, textAlign: 'center' },
  routeButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: colors.accent, marginHorizontal: spacing.md, marginTop: spacing.md, borderRadius: radius.md, padding: 12 },
  routeButtonActive: { backgroundColor: colors.success },
  routeButtonText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  card: { backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, borderLeftWidth: 3, padding: spacing.md, marginBottom: spacing.sm },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  cardNumber: { color: colors.textPrimary, fontWeight: '700', fontSize: 15 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.full },
  badgeText: { fontSize: 11, fontWeight: '600' },
  cardClient: { color: colors.textSecondary, fontSize: 13, marginBottom: 2 },
  cardAddress: { color: colors.textMuted, fontSize: 12 },
  stopBadge: { width: 20, height: 20, borderRadius: 10, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center' },
  stopBadgeText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  etaRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: spacing.sm },
  etaText: { color: colors.accent, fontSize: 12, fontWeight: '600' },
});
