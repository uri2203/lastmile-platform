import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing, shadow } from '../theme';
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

  const okCount = items.filter(i => i.ENT_ESTADO === 'ENTREGADO').length;

  return (
    <View style={styles.container}>
      {items.length > 0 && (
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{t('chofer.section_historial')}</Text>
          <View style={styles.headerStats}>
            <View style={[styles.headerPill, { backgroundColor: colors.successBg }]}>
              <Ionicons name="checkmark-circle" size={13} color={colors.success} />
              <Text style={[styles.headerPillText, { color: colors.success }]}>{okCount}</Text>
            </View>
            <View style={[styles.headerPill, { backgroundColor: colors.dangerBg }]}>
              <Ionicons name="close-circle" size={13} color={colors.danger} />
              <Text style={[styles.headerPillText, { color: colors.danger }]}>{items.length - okCount}</Text>
            </View>
          </View>
        </View>
      )}
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.ENT_ID)}
        contentContainerStyle={{ padding: spacing.md, paddingTop: items.length > 0 ? spacing.sm : spacing.md }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); }} tintColor={colors.accent} />}
        ListEmptyComponent={
          <View style={styles.center}>
            <View style={styles.emptyIconCircle}>
              <Ionicons name="time-outline" size={40} color={colors.accent} />
            </View>
            <Text style={styles.emptyTitle}>{t('chofer_app.sin_historial_todavia')}</Text>
          </View>
        }
        renderItem={({ item }) => {
          const ok = item.ENT_ESTADO === 'ENTREGADO';
          return (
            <View style={styles.row}>
              <View style={[styles.icon, { backgroundColor: ok ? colors.successBg : colors.dangerBg }]}>
                <Ionicons name={ok ? 'checkmark' : 'close'} size={18} color={ok ? colors.success : colors.danger} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowTitle}>{item.PED_NUMERO || `${t('chofer_app.pedido_prefix')}${item.PED_ID}`}</Text>
                <Text style={styles.rowSub} numberOfLines={1}>{item.PED_DESTINO_DIR}</Text>
              </View>
              <View style={[styles.statusDot, { backgroundColor: ok ? colors.success : colors.danger }]} />
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
  emptyIconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.accentDeep + '33', alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  emptyTitle: { color: colors.textPrimary, fontSize: 15, fontWeight: '600', marginTop: spacing.xs },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.md, paddingTop: spacing.md },
  headerTitle: { color: colors.textPrimary, fontSize: 20, fontWeight: '800' },
  headerStats: { flexDirection: 'row', gap: 6 },
  headerPill: { flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: radius.full, paddingHorizontal: 10, paddingVertical: 5 },
  headerPillText: { fontSize: 12, fontWeight: '700' },
  row: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, marginBottom: spacing.sm, ...shadow.soft },
  icon: { width: 38, height: 38, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm },
  rowTitle: { color: colors.textPrimary, fontWeight: '700', fontSize: 14 },
  rowSub: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
});
