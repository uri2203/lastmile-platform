import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

const ESTADO_LABEL = {
  PENDIENTE: 'Pendiente',
  EN_RUTA: 'En ruta',
  ENTREGADO: 'Entregado',
  NO_ENTREGADO: 'No entregado',
};

const ESTADO_COLOR = {
  PENDIENTE: colors.warning,
  EN_RUTA: colors.info,
  ENTREGADO: colors.success,
  NO_ENTREGADO: colors.danger,
};

export default function DeliveriesScreen({ navigation }) {
  const { choferProfile, profileError, reloadProfile } = useAuth();
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!choferProfile) return;
    try {
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
    await reloadProfile();
    await load();
  }

  if (profileError) {
    return (
      <View style={styles.center}>
        <Ionicons name="alert-circle-outline" size={48} color={colors.warning} />
        <Text style={styles.emptyTitle}>Sin perfil de chofer vinculado</Text>
        <Text style={styles.emptyText}>
          Tu cuenta no tiene un perfil de chofer asociado todavia. Pedile a tu administrador que te vincule
          desde el panel de choferes.
        </Text>
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
      <FlatList
        data={deliveries}
        keyExtractor={(item) => String(item.ENT_ID)}
        contentContainerStyle={{ padding: spacing.md }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
        ListEmptyComponent={
          <View style={styles.center}>
            <Ionicons name="cube-outline" size={48} color={colors.textMuted} />
            <Text style={styles.emptyTitle}>No tienes entregas asignadas</Text>
            <Text style={styles.emptyText}>Cuando te asignen un pedido, va a aparecer aca.</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.card, { borderLeftColor: ESTADO_COLOR[item.ENT_ESTADO] || colors.borderPrimary }]}
            onPress={() => navigation.navigate('DeliveryDetail', { entrega: item })}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.cardNumber}>{item.PED_NUMERO || `Pedido #${item.PED_ID}`}</Text>
              <View style={[styles.badge, { backgroundColor: `${ESTADO_COLOR[item.ENT_ESTADO] || colors.textMuted}22` }]}>
                <Text style={[styles.badgeText, { color: ESTADO_COLOR[item.ENT_ESTADO] || colors.textMuted }]}>
                  {ESTADO_LABEL[item.ENT_ESTADO] || item.ENT_ESTADO}
                </Text>
              </View>
            </View>
            <Text style={styles.cardClient}>{item.PED_CLIENTE_NOMBRE}</Text>
            <Text style={styles.cardAddress} numberOfLines={2}>{item.PED_DESTINO_DIR}</Text>
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
  card: { backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, borderLeftWidth: 3, padding: spacing.md, marginBottom: spacing.sm },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  cardNumber: { color: colors.textPrimary, fontWeight: '700', fontSize: 15 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.full },
  badgeText: { fontSize: 11, fontWeight: '600' },
  cardClient: { color: colors.textSecondary, fontSize: 13, marginBottom: 2 },
  cardAddress: { color: colors.textMuted, fontSize: 12 },
});
