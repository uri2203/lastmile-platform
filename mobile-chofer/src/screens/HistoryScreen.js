import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import { api } from '../api';

export default function HistoryScreen() {
  const { choferProfile } = useAuth();
  const { t } = useI18n();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!choferProfile) return;
    try {
      const res = await api.getMyDeliveries(choferProfile.CHO_ID);
      const done = (res.data || []).filter(e => e.ENT_ESTADO === 'ENTREGADO' || e.ENT_ESTADO === 'NO_ENTREGADO');
      setItems(done);
    } catch (e) {
      console.warn('Error cargando historial:', e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [choferProfile]);

  useEffect(() => { load(); }, [load]);

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
        data={items}
        keyExtractor={(item) => String(item.ENT_ID)}
        contentContainerStyle={{ padding: spacing.md }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); }} tintColor={colors.accent} />}
        ListEmptyComponent={
          <View style={styles.center}>
            <Ionicons name="time-outline" size={48} color={colors.textMuted} />
            <Text style={styles.emptyTitle}>{t('chofer_app.sin_historial_todavia')}</Text>
          </View>
        }
        renderItem={({ item }) => {
          const ok = item.ENT_ESTADO === 'ENTREGADO';
          return (
            <View style={styles.row}>
              <View style={[styles.icon, { backgroundColor: ok ? colors.successBg : colors.dangerBg }]}>
                <Ionicons name={ok ? 'checkmark' : 'close'} size={16} color={ok ? colors.success : colors.danger} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowTitle}>{item.PED_NUMERO || `${t('chofer_app.pedido_prefix')}${item.PED_ID}`}</Text>
                <Text style={styles.rowSub} numberOfLines={1}>{item.PED_DESTINO_DIR}</Text>
              </View>
            </View>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyTitle: { color: colors.textPrimary, fontSize: 15, marginTop: spacing.md },
  row: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, marginBottom: spacing.sm },
  icon: { width: 32, height: 32, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm },
  rowTitle: { color: colors.textPrimary, fontWeight: '600', fontSize: 14 },
  rowSub: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
});
