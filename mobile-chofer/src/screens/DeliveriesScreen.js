import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { colors, radius, spacing, shadow } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n, translateError } from '../i18n';
import { api } from '../api';
import { flushQueue } from '../services/offlineQueue';

function hasCoords(item) {
  return typeof item.PED_LATITUD === 'number' && typeof item.PED_LONGITUD === 'number'
    && item.PED_LATITUD !== 0 && item.PED_LONGITUD !== 0;
}

const ESTADO_ICON = {
  PENDIENTE: 'time-outline',
  EN_RUTA: 'navigate',
  ENTREGADO: 'checkmark-circle',
  NO_ENTREGADO: 'close-circle',
};

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

  const nombre = choferProfile?.CHO_NOMBRE || '';
  const totalStops = deliveries.length;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.greeting}>{t('chofer.section_entregas_hoy')}</Text>
          {!!nombre && <Text style={styles.greetingName}>{nombre}</Text>}
        </View>
        <View style={styles.headerBadge}>
          <Ionicons name="cube" size={16} color={colors.accent} />
          <Text style={styles.headerBadgeText}>{totalStops}</Text>
        </View>
      </View>

      {deliveries.length > 0 && (
        <TouchableOpacity
          style={[styles.routeButton, routeStarted && styles.routeButtonActive]}
          onPress={handleIniciarRuta}
          disabled={optimizing}
          activeOpacity={0.85}
        >
          {optimizing ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <View style={styles.routeButtonIcon}>
              <Ionicons name={routeStarted ? 'navigate' : 'navigate-outline'} size={16} color="#fff" />
            </View>
          )}
          <Text style={styles.routeButtonText}>
            {optimizing ? t('chofer_app.optimizando_ruta') : routeStarted ? t('chofer_app.ruta_iniciada') : t('chofer_app.iniciar_ruta')}
          </Text>
          {!optimizing && <Ionicons name="chevron-forward" size={16} color="rgba(255,255,255,0.7)" />}
        </TouchableOpacity>
      )}
      <FlatList
        data={deliveries}
        keyExtractor={(item) => String(item.ENT_ID)}
        contentContainerStyle={{ padding: spacing.md, paddingTop: spacing.sm }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
        ListEmptyComponent={
          <View style={styles.center}>
            <View style={styles.emptyIconCircle}>
              <Ionicons name="cube-outline" size={40} color={colors.accent} />
            </View>
            <Text style={styles.emptyTitle}>{t('chofer_app.sin_entregas_titulo')}</Text>
            <Text style={styles.emptyText}>{t('chofer_app.sin_entregas_desc')}</Text>
          </View>
        }
        renderItem={({ item, index }) => {
          const estadoColor = ESTADO_COLOR[item.ENT_ESTADO] || colors.textMuted;
          const initial = (item.PED_CLIENTE_NOMBRE || '?').trim().charAt(0).toUpperCase();
          return (
            <TouchableOpacity
              style={styles.card}
              onPress={() => navigation.navigate('DeliveryDetail', { entrega: item })}
              activeOpacity={0.8}
            >
              <View style={[styles.cardAccent, { backgroundColor: estadoColor }]} />
              <View style={styles.cardAvatar}>
                <Text style={styles.cardAvatarText}>{initial}</Text>
                {routeStarted && hasCoords(item) && (
                  <View style={styles.stopBadge}>
                    <Text style={styles.stopBadgeText}>{index + 1}</Text>
                  </View>
                )}
              </View>
              <View style={{ flex: 1 }}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardNumber} numberOfLines={1}>{item.PED_NUMERO || `${t('chofer_app.pedido_prefix')}${item.PED_ID}`}</Text>
                  <View style={[styles.badge, { backgroundColor: `${estadoColor}22` }]}>
                    <Ionicons name={ESTADO_ICON[item.ENT_ESTADO] || 'ellipse-outline'} size={11} color={estadoColor} />
                    <Text style={[styles.badgeText, { color: estadoColor }]}>
                      {ESTADO_LABEL[item.ENT_ESTADO] || item.ENT_ESTADO}
                    </Text>
                  </View>
                </View>
                <Text style={styles.cardClient} numberOfLines={1}>{item.PED_CLIENTE_NOMBRE}</Text>
                <View style={styles.cardAddressRow}>
                  <Ionicons name="location-outline" size={12} color={colors.textMuted} />
                  <Text style={styles.cardAddress} numberOfLines={1}>{item.PED_DESTINO_DIR}</Text>
                </View>
                {routeStarted && etaByPedId[item.PED_ID] != null && (
                  <View style={styles.etaRow}>
                    <Ionicons name="time-outline" size={12} color={colors.accent} />
                    <Text style={styles.etaText}>{etaByPedId[item.PED_ID]} {t('chofer_app.eta_min')}</Text>
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyIconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.successBg, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  emptyTitle: { color: colors.textPrimary, fontSize: 16, fontWeight: '700', marginTop: spacing.xs, textAlign: 'center' },
  emptyText: { color: colors.textMuted, fontSize: 13, marginTop: spacing.xs, textAlign: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.sm },
  greeting: { color: colors.textPrimary, fontSize: 20, fontWeight: '800' },
  greetingName: { color: colors.textMuted, fontSize: 13, marginTop: 2 },
  headerBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.borderPrimary, borderRadius: radius.full, paddingHorizontal: 12, paddingVertical: 6 },
  headerBadgeText: { color: colors.textPrimary, fontWeight: '700', fontSize: 13 },
  routeButton: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: colors.accent, marginHorizontal: spacing.md, marginBottom: spacing.xs, borderRadius: radius.lg, padding: 14, ...shadow.glow },
  routeButtonActive: { backgroundColor: colors.success, shadowColor: colors.success },
  routeButtonIcon: { width: 28, height: 28, borderRadius: 14, backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center' },
  routeButtonText: { color: '#fff', fontWeight: '700', fontSize: 14, flex: 1 },
  card: { flexDirection: 'row', backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, marginBottom: spacing.sm, overflow: 'hidden', ...shadow.soft },
  cardAccent: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4 },
  cardAvatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.accentDeep, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm },
  cardAvatarText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4, gap: 8 },
  cardNumber: { color: colors.textPrimary, fontWeight: '700', fontSize: 15, flex: 1 },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: radius.full },
  badgeText: { fontSize: 10, fontWeight: '700', textTransform: 'uppercase' },
  cardClient: { color: colors.textSecondary, fontSize: 13, marginBottom: 3, fontWeight: '600' },
  cardAddressRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  cardAddress: { color: colors.textMuted, fontSize: 12, flex: 1 },
  stopBadge: { position: 'absolute', bottom: -4, right: -4, width: 18, height: 18, borderRadius: 9, backgroundColor: colors.warning, alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: colors.bgCard },
  stopBadgeText: { color: '#1a1a24', fontSize: 10, fontWeight: '800' },
  etaRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: spacing.xs },
  etaText: { color: colors.accent, fontSize: 12, fontWeight: '700' },
});
