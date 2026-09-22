import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme-context';
import Card from '../shared/components/Card';
import Badge from '../shared/components/Badge';
import EmptyState from '../shared/components/EmptyState';
import { get } from '../shared/api';
import { formatCurrency, formatDate, formatRelativeTime } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

const DATE_FILTERS = [
  { key: 'today', label: 'Hoy' },
  { key: 'week', label: 'Semana' },
  { key: 'month', label: 'Mes' },
  { key: 'all', label: 'Todo' },
];

export default function HistoryScreen({ navigation }) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dateFilter, setDateFilter] = useState('today');

  const fetchHistory = useCallback(async () => {
    try {
      const params = {};
      if (dateFilter !== 'all') {
        params.period = dateFilter;
      }
      const data = await get('/api/deliveries/history', params);
      setDeliveries(Array.isArray(data) ? data : data?.deliveries || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [dateFilter]);

  useEffect(() => {
    setLoading(true);
    fetchHistory();
  }, [fetchHistory]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchHistory();
  }, [fetchHistory]);

  const stats = deliveries.reduce(
    (acc, d) => {
      acc.total += 1;
      if (d.status === 'ENTREGADO') {
        acc.delivered += 1;
        acc.collected += Number(d.monto || d.amount || 0);
      } else if (d.status === 'FALLIDO' || d.status === 'CANCELADO') {
        acc.failed += 1;
      }
      return acc;
    },
    { total: 0, delivered: 0, failed: 0, collected: 0 }
  );

  const successRate = stats.total > 0 ? Math.round((stats.delivered / stats.total) * 100) : 0;

  const renderItem = ({ item }) => (
    <Card
      style={[styles.historyCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}
      onPress={() => navigation.navigate('DeliveryDetail', { deliveryId: item.id || item._id })}
    >
      <View style={styles.cardHeader}>
        <View style={styles.cardHeaderLeft}>
          <Text style={[styles.clientName, { color: theme.text }]}>
            {item.cliente_nombre || item.client_name || 'Cliente'}
          </Text>
          <Text style={[styles.dateText, { color: theme.textSecondary }]}>
            {formatDate(item.created_at || item.fecha)}
          </Text>
        </View>
        <Badge status={item.status} size="sm" />
      </View>

      <View style={styles.cardBody}>
        <View style={styles.infoRow}>
          <Ionicons name="location-outline" size={16} color={theme.textSecondary} />
          <Text style={[styles.addressText, { color: theme.textSecondary }]} numberOfLines={1}>
            {item.direccion || item.address || 'Sin dirección'}
          </Text>
        </View>
        <View style={styles.amountRow}>
          <Ionicons name="cash-outline" size={16} color={colors.success[500]} />
          <Text style={[styles.amountText, { color: colors.success[600] }]}>
            {formatCurrency(item.monto || item.amount || 0)}
          </Text>
        </View>
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background, paddingTop: insets.top }]}>
      <View style={[styles.header, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Historial</Text>
      </View>

      <View style={[styles.statsRow, { backgroundColor: theme.surface }]}>
        <StatItem label="Total" value={stats.total} color={theme.primary} theme={theme} />
        <StatItem label="Entregadas" value={stats.delivered} color={colors.success[500]} theme={theme} />
        <StatItem label="Cobrado" value={formatCurrency(stats.collected)} color={colors.accent[500]} theme={theme} small />
        <StatItem label="Éxito" value={`${successRate}%`} color={colors.success[600]} theme={theme} />
      </View>

      <View style={[styles.filterBar, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
        {DATE_FILTERS.map((f) => (
          <TouchableOpacity
            key={f.key}
            style={[styles.filterTab, dateFilter === f.key && { backgroundColor: theme.primary }]}
            onPress={() => setDateFilter(f.key)}
          >
            <Text style={[styles.filterText, { color: dateFilter === f.key ? '#ffffff' : theme.textSecondary }]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={deliveries}
        keyExtractor={(item) => String(item.id || item._id)}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
        ListEmptyComponent={
          <EmptyState
            icon={<Ionicons name="time-outline" size={64} color={theme.textDisabled} />}
            title="Sin historial"
            subtitle="No hay entregas en este período"
          />
        }
      />
    </View>
  );
}

function StatItem({ label, value, color, theme, small }) {
  return (
    <View style={styles.statItem}>
      <Text style={[styles.statValue, { color, fontSize: small ? typography.fontSize.base : typography.fontSize.xl }]}>
        {value}
      </Text>
      <Text style={[styles.statLabel, { color: theme.textSecondary }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[3],
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: typography.fontSize.xl, fontWeight: '700' },
  statsRow: {
    flexDirection: 'row',
    paddingVertical: spacing[4],
    paddingHorizontal: spacing[3],
    borderBottomWidth: 1,
    borderBottomColor: colors.neutral[100],
  },
  statItem: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: typography.fontSize.xl, fontWeight: '700' },
  statLabel: { fontSize: typography.fontSize.xs, marginTop: 2, fontWeight: '500' },
  filterBar: {
    flexDirection: 'row',
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[2],
    borderBottomWidth: 1,
  },
  filterTab: { flex: 1, paddingVertical: spacing[2], borderRadius: borderRadius.md, marginHorizontal: 3, alignItems: 'center' },
  filterText: { fontSize: typography.fontSize.sm, fontWeight: '600' },
  listContent: { padding: spacing[4], paddingBottom: 40 },
  historyCard: { marginBottom: spacing[3] },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing[3] },
  cardHeaderLeft: { flex: 1, marginRight: spacing[3] },
  clientName: { fontSize: typography.fontSize.base, fontWeight: '600' },
  dateText: { fontSize: typography.fontSize.xs, marginTop: 2 },
  cardBody: {},
  infoRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing[2] },
  addressText: { fontSize: typography.fontSize.sm, marginLeft: spacing[2], flex: 1 },
  amountRow: { flexDirection: 'row', alignItems: 'center' },
  amountText: { fontSize: typography.fontSize.base, fontWeight: '700', marginLeft: spacing[2] },
});
