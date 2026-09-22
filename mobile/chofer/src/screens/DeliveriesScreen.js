import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../App';
import Card from '../../shared/components/Card';
import Avatar from '../../shared/components/Avatar';
import Badge from '../../shared/components/Badge';
import EmptyState from '../../shared/components/EmptyState';
import { get } from '../../shared/api';
import { formatCurrency, formatRelativeTime, formatPhone } from '../../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../../shared/theme';
import useAuth from '../hooks/useAuth';

const FILTER_TABS = [
  { key: 'ALL', label: 'Todas' },
  { key: 'PENDIENTE', label: 'Pendientes' },
  { key: 'EN_RUTA', label: 'En Ruta' },
  { key: 'ENTREGADO', label: 'Entregadas' },
];

const STATUS_ICONS = {
  PENDIENTE: 'time-outline',
  ASIGNADO: 'person-outline',
  EN_RUTA: 'navigate-outline',
  ENTREGADO: 'checkmark-circle-outline',
  CANCELADO: 'close-circle-outline',
  FALLIDO: 'alert-circle-outline',
};

export default function DeliveriesScreen({ navigation }) {
  const { user } = useAuth();
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [gpsEnabled, setGpsEnabled] = useState(true);

  const fetchDeliveries = useCallback(async () => {
    try {
      const data = await get('/api/deliveries', { status: activeFilter === 'ALL' ? undefined : activeFilter });
      setDeliveries(Array.isArray(data) ? data : data?.deliveries || []);
    } catch (error) {
      console.error('Error fetching deliveries:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    fetchDeliveries();
  }, [fetchDeliveries]);

  useEffect(() => {
    const interval = setInterval(fetchDeliveries, 60000);
    return () => clearInterval(interval);
  }, [fetchDeliveries]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchDeliveries();
  }, [fetchDeliveries]);

  const filteredDeliveries =
    activeFilter === 'ALL'
      ? deliveries
      : deliveries.filter((d) => d.status === activeFilter);

  const todayStats = deliveries.reduce(
    (acc, d) => {
      const isToday = new Date(d.created_at || d.fecha).toDateString() === new Date().toDateString();
      if (isToday) {
        acc.deliveries += 1;
        if (d.status === 'ENTREGADO') {
          acc.collected += Number(d.monto || d.amount || 0);
        }
      }
      return acc;
    },
    { deliveries: 0, collected: 0 }
  );

  const renderDeliveryCard = ({ item }) => (
    <Card
      style={[styles.deliveryCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}
      onPress={() => navigation.navigate('DeliveryDetail', { deliveryId: item.id || item._id })}
    >
      <View style={styles.cardHeader}>
        <View style={styles.cardHeaderLeft}>
          <View style={[styles.statusIcon, { backgroundColor: getStatusColor(item.status) + '15' }]}>
            <Ionicons
              name={STATUS_ICONS[item.status] || 'help-circle-outline'}
              size={20}
              color={getStatusColor(item.status)}
            />
          </View>
          <View style={styles.cardHeaderText}>
            <Text style={[styles.clientName, { color: theme.text }]}>
              {item.cliente_nombre || item.client_name || 'Cliente'}
            </Text>
            <Text style={[styles.deliveryId, { color: theme.textSecondary }]}>
              #{item.id || item._id || '---'}
            </Text>
          </View>
        </View>
        <Badge status={item.status} size="sm" />
      </View>

      <View style={styles.cardBody}>
        <View style={styles.infoRow}>
          <Ionicons name="location-outline" size={16} color={theme.textSecondary} />
          <Text style={[styles.infoText, { color: theme.textSecondary }]} numberOfLines={1}>
            {item.direccion || item.address || 'Sin dirección'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Ionicons name="cash-outline" size={16} color={colors.success[500]} />
          <Text style={[styles.amountText, { color: colors.success[600] }]}>
            {formatCurrency(item.monto || item.amount || 0)}
          </Text>
        </View>
      </View>

      <View style={[styles.cardFooter, { borderTopColor: theme.border }]}>
        <Ionicons name="time-outline" size={14} color={theme.textSecondary} />
        <Text style={[styles.timeText, { color: theme.textSecondary }]}>
          {formatRelativeTime(item.created_at || item.fecha)}
        </Text>
      </View>
    </Card>
  );

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Cargando entregas...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background, paddingTop: insets.top }]}>
      <View style={[styles.header, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
        <View style={styles.headerLeft}>
          <Avatar name={user?.nombre || 'Chofer'} size="md" online={gpsEnabled} />
          <View style={styles.headerInfo}>
            <Text style={[styles.headerName, { color: theme.text }]}>
              {user?.nombre || 'Chofer'}
            </Text>
            <View style={styles.statusRow}>
              <View style={[styles.statusDot, { backgroundColor: gpsEnabled ? colors.success[500] : colors.neutral[400] }]} />
              <Text style={[styles.statusText, { color: theme.textSecondary }]}>
                {gpsEnabled ? 'En línea' : 'Sin conexión'}
              </Text>
            </View>
          </View>
        </View>
        <TouchableOpacity
          style={[styles.refreshBtn, { backgroundColor: theme.surfaceVariant }]}
          onPress={fetchDeliveries}
        >
          <Ionicons name="refresh" size={20} color={theme.primary} />
        </TouchableOpacity>
      </View>

      <View style={[styles.statsBar, { backgroundColor: theme.primary }]}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{todayStats.deliveries}</Text>
          <Text style={styles.statLabel}>Hoy: entregas</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatCurrency(todayStats.collected)}</Text>
          <Text style={styles.statLabel}>Cobrado</Text>
        </View>
      </View>

      <View style={[styles.filterBar, { backgroundColor: theme.surface }]}>
        {FILTER_TABS.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.filterTab,
              activeFilter === tab.key && { backgroundColor: theme.primary },
            ]}
            onPress={() => setActiveFilter(tab.key)}
          >
            <Text
              style={[
                styles.filterTabText,
                { color: activeFilter === tab.key ? '#ffffff' : theme.textSecondary },
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filteredDeliveries}
        keyExtractor={(item) => String(item.id || item._id)}
        renderItem={renderDeliveryCard}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />
        }
        ListEmptyComponent={
          <EmptyState
            icon={<Ionicons name="car-outline" size={64} color={theme.textDisabled} />}
            title="Sin entregas"
            subtitle="No hay entregas en esta categoría"
          />
        }
      />

      <TouchableOpacity
        style={[styles.fab, { backgroundColor: gpsEnabled ? colors.success[500] : colors.neutral[400], bottom: insets.bottom + 20 }]}
        onPress={() => setGpsEnabled(!gpsEnabled)}
      >
        <Ionicons name={gpsEnabled ? 'locate' : 'locate-outline'} size={24} color="#ffffff" />
      </TouchableOpacity>
    </View>
  );
}

function getStatusColor(status) {
  const map = {
    PENDIENTE: colors.accent[500],
    ASIGNADO: colors.primary[500],
    EN_RUTA: '#2563eb',
    ENTREGADO: colors.success[500],
    CANCELADO: colors.error[500],
    FALLIDO: colors.error[700],
  };
  return map[status] || colors.neutral[500];
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
  loadingText: {
    marginTop: spacing[3],
    fontSize: typography.fontSize.base,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[3],
    borderBottomWidth: 1,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerInfo: {
    marginLeft: spacing[3],
  },
  headerName: {
    fontSize: typography.fontSize.lg,
    fontWeight: '700',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing[1],
  },
  statusText: {
    fontSize: typography.fontSize.xs,
    fontWeight: '500',
  },
  refreshBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing[3],
    paddingHorizontal: spacing[4],
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: typography.fontSize.lg,
    fontWeight: '700',
    color: '#ffffff',
  },
  statLabel: {
    fontSize: typography.fontSize.xs,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 30,
    backgroundColor: 'rgba(255,255,255,0.3)',
    marginHorizontal: spacing[4],
  },
  filterBar: {
    flexDirection: 'row',
    paddingHorizontal: spacing[3],
    paddingVertical: spacing[2],
  },
  filterTab: {
    flex: 1,
    paddingVertical: spacing[2],
    borderRadius: borderRadius.md,
    marginHorizontal: 3,
    alignItems: 'center',
  },
  filterTabText: {
    fontSize: typography.fontSize.sm,
    fontWeight: '600',
  },
  listContent: {
    padding: spacing[4],
    paddingBottom: 100,
  },
  deliveryCard: {
    marginBottom: spacing[3],
    borderRadius: borderRadius.lg,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing[3],
  },
  cardHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing[3],
  },
  cardHeaderText: {
    flex: 1,
  },
  clientName: {
    fontSize: typography.fontSize.base,
    fontWeight: '600',
  },
  deliveryId: {
    fontSize: typography.fontSize.xs,
    marginTop: 2,
  },
  cardBody: {
    marginBottom: spacing[3],
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing[2],
  },
  infoText: {
    fontSize: typography.fontSize.sm,
    marginLeft: spacing[2],
    flex: 1,
  },
  amountText: {
    fontSize: typography.fontSize.base,
    fontWeight: '700',
    marginLeft: spacing[2],
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.neutral[100],
    paddingTop: spacing[3],
  },
  timeText: {
    fontSize: typography.fontSize.xs,
    marginLeft: spacing[2],
  },
  fab: {
    position: 'absolute',
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.lg,
  },
});
