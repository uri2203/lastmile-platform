import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing, shadow } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import { api } from '../api';

function money(n) {
  const v = Number(n || 0);
  return `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function CashScreen() {
  const { choferProfile } = useAuth();
  const { t } = useI18n();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!choferProfile) return;
    try {
      const res = await api.getCashSummary(choferProfile.CHO_ID);
      setData(res.data);
    } catch (e) {
      console.warn('Error cargando caja:', e.message);
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

  const holdings = data?.holdings || [];
  const totalHolding = data?.total_holding || 0;
  const countCod = data?.count_delivered_cod || 0;

  return (
    <View style={styles.container}>
      <FlatList
        data={holdings}
        keyExtractor={(item) => String(item.HOLDING_ID || item.PED_ID)}
        contentContainerStyle={{ padding: spacing.md }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); }} tintColor={colors.accent} />}
        ListHeaderComponent={
          <View>
            <View style={styles.heroCard}>
              <View style={styles.heroBlob} />
              <View style={styles.heroIconCircle}>
                <Ionicons name="wallet" size={22} color={colors.success} />
              </View>
              <Text style={styles.heroLabel}>{t('chofer_app.efectivo_en_mano')}</Text>
              <Text style={styles.heroValue}>{money(totalHolding)}</Text>
              <Text style={styles.heroSub}>{t('chofer_app.por_depositar')}</Text>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{countCod}</Text>
                <Text style={styles.statLabel}>{t('chofer_app.cobros_cod')}</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{holdings.length}</Text>
                <Text style={styles.statLabel}>{t('chofer_app.sin_depositar')}</Text>
              </View>
            </View>

            <Text style={styles.sectionTitle}>{t('chofer_app.detalle_cobros')}</Text>
          </View>
        }
        ListEmptyComponent={
          <View style={styles.center}>
            <View style={styles.emptyIconCircle}>
              <Ionicons name="cash-outline" size={40} color={colors.success} />
            </View>
            <Text style={styles.emptyTitle}>{t('chofer_app.sin_cobros_titulo')}</Text>
            <Text style={styles.emptyText}>{t('chofer_app.sin_cobros_desc')}</Text>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={styles.rowIcon}>
              <Ionicons name="cash" size={18} color={colors.success} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowTitle} numberOfLines={1}>{item.PED_NUMERO || `${t('chofer_app.pedido_prefix')}${item.PED_ID}`}</Text>
              <Text style={styles.rowSub} numberOfLines={1}>{item.PED_CLIENTE_NOMBRE || '-'}</Text>
            </View>
            <Text style={styles.rowAmount}>{money(item.CASH_MONTO)}</Text>
          </View>
        )}
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
  heroCard: { backgroundColor: colors.bgCard, borderRadius: radius.xl, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.xl, alignItems: 'center', marginBottom: spacing.md, overflow: 'hidden', ...shadow.card },
  heroBlob: { position: 'absolute', top: -70, right: -70, width: 180, height: 180, borderRadius: 90, backgroundColor: colors.success, opacity: 0.12 },
  heroIconCircle: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.successBg, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  heroLabel: { color: colors.textMuted, fontSize: 13 },
  heroValue: { color: colors.success, fontSize: 40, fontWeight: '800', marginTop: 2 },
  heroSub: { color: colors.textMuted, fontSize: 12, marginTop: 4 },
  statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  statBox: { flex: 1, backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, alignItems: 'center', ...shadow.soft },
  statValue: { color: colors.textPrimary, fontSize: 22, fontWeight: '800' },
  statLabel: { color: colors.textMuted, fontSize: 11, marginTop: 2, textAlign: 'center' },
  sectionTitle: { color: colors.textPrimary, fontSize: 14, fontWeight: '700', marginBottom: spacing.sm },
  row: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, marginBottom: spacing.sm, ...shadow.soft },
  rowIcon: { width: 38, height: 38, borderRadius: radius.md, backgroundColor: colors.successBg, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm },
  rowTitle: { color: colors.textPrimary, fontWeight: '700', fontSize: 14 },
  rowSub: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
  rowAmount: { color: colors.success, fontWeight: '800', fontSize: 15 },
});
