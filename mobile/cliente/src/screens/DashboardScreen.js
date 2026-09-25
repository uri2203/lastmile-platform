import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme-context';
import useAuth from '../hooks/useAuth';
import Card from '../shared/components/Card';
import Badge from '../shared/components/Badge';
import Avatar from '../shared/components/Avatar';
import { get } from '../shared/api';
import { formatCurrency, formatRelativeTime, truncate } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

const { width } = Dimensions.get('window');
const QUICK_ACTION_SIZE = (width - spacing[4] * 2 - spacing[3] * 2) / 2;

export default function DashboardScreen({ navigation }) {
  const { theme } = useTheme();
  const { user } = useAuth();
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [recentShipments, setRecentShipments] = useState([]);
  const [stats, setStats] = useState({ total: 0, pendientes: 0, entregados: 0 });

  const fetchData = useCallback(async () => {
    try {
      const [shipmentsRes, statsRes] = await Promise.allSettled([
        get('/api/shipments', { limit: 5, sort: '-created_at' }),
        get('/api/shipments/stats'),
      ]);

      if (shipmentsRes.status === 'fulfilled') {
        const data = shipmentsRes.value;
        setRecentShipments(Array.isArray(data) ? data : data?.shipments || data?.data || []);
      }

      if (statsRes.status === 'fulfilled') {
        const s = statsRes.value;
        setStats({
          total: s?.total || s?.thisMonth || 0,
          pendientes: s?.pending || s?.pendientes || 0,
          entregados: s?.delivered || s?.entregados || 0,
        });
      }
    } catch (error) {
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  const quickActions = [
    {
      id: 'new',
      title: 'Nuevo envío',
      icon: 'add-circle',
      color: colors.primary[500],
      bgColor: colors.primary[50],
      screen: 'CreateShipment',
    },
    {
      id: 'track',
      title: 'Rastrear paquete',
      icon: 'search',
      color: colors.success[600],
      bgColor: colors.success[50],
      tab: 'Rastrear',
      screen: 'TrackingList',
    },
    {
      id: 'shipments',
      title: 'Mis envíos',
      icon: 'cube',
      color: colors.accent[600],
      bgColor: colors.accent[50],
      tab: 'Envíos',
      screen: 'MyShipments',
    },
    {
      id: 'invoices',
      title: 'Facturas',
      icon: 'receipt',
      color: '#7c3aed',
      bgColor: '#f3e8ff',
      tab: 'Envíos',
      screen: 'Invoices',
    },
  ];

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />
      }
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={[styles.greeting, { color: theme.textSecondary }]}>{getGreeting()},</Text>
          <Text style={[styles.userName, { color: theme.text }]}>{user?.nombre || 'Cliente'}</Text>
        </View>
        <Avatar name={user?.nombre || 'Cliente'} size="lg" />
      </View>

      {/* Stats */}
      <View style={styles.statsRow}>
        <Card style={[styles.statCard, { backgroundColor: theme.surface }]}>
          <Text style={[styles.statNumber, { color: theme.primary }]}>{stats.total}</Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Envíos mes</Text>
        </Card>
        <Card style={[styles.statCard, { backgroundColor: theme.surface }]}>
          <Text style={[styles.statNumber, { color: colors.warning[500] }]}>{stats.pendientes}</Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Pendientes</Text>
        </Card>
        <Card style={[styles.statCard, { backgroundColor: theme.surface }]}>
          <Text style={[styles.statNumber, { color: colors.success[500] }]}>{stats.entregados}</Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Entregados</Text>
        </Card>
      </View>

      {/* Quick Actions */}
      <Text style={[styles.sectionTitle, { color: theme.text }]}>Acciones rápidas</Text>
      <View style={styles.quickActionsGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[styles.quickAction, { backgroundColor: action.bgColor }]}
            onPress={() =>
              action.tab
                ? navigation.navigate(action.tab, { screen: action.screen })
                : navigation.navigate(action.screen)
            }
            activeOpacity={0.7}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: action.color + '20' }]}>
              <Ionicons name={action.icon} size={28} color={action.color} />
            </View>
            <Text style={[styles.quickActionTitle, { color: theme.text }]}>{action.title}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recent Shipments */}
      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Envíos recientes</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Envíos')}>
          <Text style={[styles.seeAll, { color: theme.primary }]}>Ver todos</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.primary} />
        </View>
      ) : recentShipments.length === 0 ? (
        <Card style={[styles.emptyCard, { backgroundColor: theme.surface }]}>
          <Ionicons name="cube-outline" size={48} color={theme.textDisabled} />
          <Text style={[styles.emptyTitle, { color: theme.textSecondary }]}>
            Sin envíos recientes
          </Text>
          <Text style={[styles.emptySubtitle, { color: theme.textDisabled }]}>
            Crea tu primer envío para comenzar
          </Text>
        </Card>
      ) : (
        recentShipments.map((shipment) => (
          <Card
            key={shipment.id || shipment._id}
            style={[styles.shipmentCard, { backgroundColor: theme.surface }]}
            onPress={() =>
              navigation.navigate('Rastrear', {
                screen: 'ShipmentDetail',
                params: { shipmentId: shipment.id || shipment._id },
              })
            }
          >
            <View style={styles.shipmentRow}>
              <View style={styles.shipmentInfo}>
                <Text style={[styles.trackingNumber, { color: theme.text }]}>
                  {shipment.tracking_number || shipment.folio || '—'}
                </Text>
                <Text style={[styles.shipmentRoute, { color: theme.textSecondary }]}>
                  {truncate(shipment.origin_address || shipment.origen || '', 20)} →{' '}
                  {truncate(shipment.destination_address || shipment.destino || '', 20)}
                </Text>
              </View>
              <View style={styles.shipmentRight}>
                <Badge status={shipment.status || 'PENDIENTE'} size="sm" />
                <Text style={[styles.shipmentTime, { color: theme.textDisabled }]}>
                  {formatRelativeTime(shipment.created_at)}
                </Text>
              </View>
            </View>
          </Card>
        ))
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[10],
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing[6],
  },
  greeting: {
    fontSize: typography.fontSize.base,
    fontWeight: '400',
  },
  userName: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: '700',
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing[3],
    marginBottom: spacing[6],
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing[4],
    paddingHorizontal: spacing[2],
  },
  statNumber: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: '800',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: '500',
  },
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: '700',
    marginBottom: spacing[3],
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing[3],
    marginTop: spacing[2],
  },
  seeAll: {
    fontSize: typography.fontSize.sm,
    fontWeight: '600',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing[3],
    marginBottom: spacing[6],
  },
  quickAction: {
    width: QUICK_ACTION_SIZE,
    borderRadius: borderRadius.lg,
    padding: spacing[4],
    alignItems: 'center',
    ...shadows.sm,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing[2],
  },
  quickActionTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: '600',
    textAlign: 'center',
  },
  loadingContainer: {
    paddingVertical: spacing[8],
    alignItems: 'center',
  },
  emptyCard: {
    alignItems: 'center',
    paddingVertical: spacing[8],
  },
  emptyTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: '600',
    marginTop: spacing[3],
  },
  emptySubtitle: {
    fontSize: typography.fontSize.sm,
    marginTop: spacing[1],
  },
  shipmentCard: {
    marginBottom: spacing[3],
  },
  shipmentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  shipmentInfo: {
    flex: 1,
    marginRight: spacing[3],
  },
  trackingNumber: {
    fontSize: typography.fontSize.base,
    fontWeight: '700',
    marginBottom: 4,
  },
  shipmentRoute: {
    fontSize: typography.fontSize.sm,
  },
  shipmentRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  shipmentTime: {
    fontSize: typography.fontSize.xs,
    marginTop: 4,
  },
});
