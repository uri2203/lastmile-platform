import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import { api } from '../api';

function StatCard({ icon, label, value, color }) {
  return (
    <View style={styles.statCard}>
      <View style={[styles.statIcon, { backgroundColor: `${color}22` }]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export default function PerformanceScreen() {
  const { choferProfile } = useAuth();
  const { t } = useI18n();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!choferProfile) return;
    try {
      const res = await api.getRendimiento();
      // El backend ya filtra a "solo mi fila" cuando el rol es chofer, pero
      // por las dudas se busca por CHO_ID en vez de asumir data[0].
      const own = (res.data || []).find(d => d.CHO_ID === choferProfile.CHO_ID) || res.data?.[0] || null;
      setData(own);
    } catch (e) {
      console.warn('Error cargando rendimiento:', e.message);
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

  if (!data) {
    return (
      <View style={styles.center}>
        <Ionicons name="stats-chart-outline" size={48} color={colors.textMuted} />
        <Text style={styles.emptyTitle}>{t('chofer_app.sin_rendimiento_titulo')}</Text>
        <Text style={styles.emptyText}>{t('chofer_app.sin_rendimiento_desc')}</Text>
      </View>
    );
  }

  const tasaExito = Math.round(data.TASA_EXITO || 0);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ padding: spacing.md }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); }} tintColor={colors.accent} />}
    >
      <View style={styles.heroCard}>
        <Text style={styles.heroValue}>{tasaExito}%</Text>
        <Text style={styles.heroLabel}>{t('chofer_app.tasa_exito')}</Text>
      </View>

      <View style={styles.grid}>
        <StatCard
          icon="checkmark-done-outline"
          label={t('chofer_app.entregas_realizadas')}
          value={data.ENTREGAS_REALIZADAS ?? 0}
          color={colors.success}
        />
        <StatCard
          icon="albums-outline"
          label={t('chofer_app.total_asignaciones')}
          value={data.TOTAL_ASIGNACIONES ?? 0}
          color={colors.accent}
        />
        <StatCard
          icon="time-outline"
          label={t('chofer_app.promedio_horas')}
          value={data.PROMEDIO_HORAS ? `${Number(data.PROMEDIO_HORAS).toFixed(1)}h` : '-'}
          color={colors.warning}
        />
        <StatCard
          icon="speedometer-outline"
          label={t('chofer_app.velocidad_promedio')}
          value={data.VELOCIDAD_PROMEDIO ? `${Number(data.VELOCIDAD_PROMEDIO).toFixed(0)} km/h` : '-'}
          color={colors.info}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgPrimary },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, backgroundColor: colors.bgPrimary },
  emptyTitle: { color: colors.textPrimary, fontSize: 16, fontWeight: '600', marginTop: spacing.md, textAlign: 'center' },
  emptyText: { color: colors.textMuted, fontSize: 13, marginTop: spacing.xs, textAlign: 'center' },
  heroCard: { backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.xl, alignItems: 'center', marginBottom: spacing.md },
  heroValue: { color: colors.accent, fontSize: 42, fontWeight: '800' },
  heroLabel: { color: colors.textMuted, fontSize: 13, marginTop: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, justifyContent: 'space-between' },
  statCard: { width: '48%', backgroundColor: colors.bgCard, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.borderPrimary, padding: spacing.md, marginBottom: spacing.sm },
  statIcon: { width: 36, height: 36, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  statValue: { color: colors.textPrimary, fontSize: 20, fontWeight: '700' },
  statLabel: { color: colors.textMuted, fontSize: 11, marginTop: 2 },
});
