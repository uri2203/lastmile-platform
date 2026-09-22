import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme-context';
import Card from '../shared/components/Card';
import Badge from '../shared/components/Badge';
import EmptyState from '../shared/components/EmptyState';
import { get } from '../shared/api';
import { formatRelativeTime, truncate } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

export default function MyShipmentsScreen({ navigation }) {
  const { theme } = useTheme();
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchShipments = useCallback(async () => {
    try {
      const data = await get('/api/shipments', { sort: '-created_at' });
      const list = Array.isArray(data) ? data : data?.shipments || data?.data || [];
      setShipments(list);
    } catch (error) {
      console.error('Shipments fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchShipments();
  }, [fetchShipments]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchShipments();
    setRefreshing(false);
  }, [fetchShipments]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'PENDIENTE': return 'time-outline';
      case 'ASIGNADO': return 'person-outline';
      case 'EN_RUTA': return 'car-outline';
      case 'ENTREGADO': return 'checkmark-circle-outline';
      case 'CANCELADO': return 'close-circle-outline';
      default: return 'help-circle-outline';
    }
  };

  const renderItem = ({ item }) => (
    <Card
      style={[styles.shipmentCard, { backgroundColor: theme.surface }]}
      onPress={() => navigation.navigate('ShipmentDetail', { shipmentId: item.id || item._id })}
    >
      <View style={styles.cardHeader}>
        <View style={styles.trackingRow}>
          <Ionicons name={getStatusIcon(item.status)} size={20} color={theme.primary} />
          <Text style={[styles.trackingNumber, { color: theme.text }]}>
            {item.tracking_number || item.folio || '—'}
          </Text>
        </View>
        <Badge status={item.status || 'PENDIENTE'} size="sm" />
      </View>

      <View style={styles.routeContainer}>
        <View style={styles.routePoint}>
          <View style={[styles.routeDot, { backgroundColor: colors.primary[500] }]} />
          <Text style={[styles.routeText, { color: theme.text }]} numberOfLines={1}>
            {truncate(item.origin_address || item.origen || 'Origen', 30)}
          </Text>
        </View>
        <View style={styles.routeLine} />
        <View style={styles.routePoint}>
          <View style={[styles.routeDot, { backgroundColor: colors.success[500] }]} />
          <Text style={[styles.routeText, { color: theme.text }]} numberOfLines={1}>
            {truncate(item.destination_address || item.destino || 'Destino', 30)}
          </Text>
        </View>
      </View>

      <View style={styles.cardFooter}>
        <Text style={[styles.lastUpdate, { color: theme.textDisabled }]}>
          {formatRelativeTime(item.updated_at || item.created_at)}
        </Text>
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Mis envíos</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          {shipments.length} envío{shipments.length !== 1 ? 's' : ''}
        </Text>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
        </View>
      ) : shipments.length === 0 ? (
        <EmptyState
          icon={<Ionicons name="cube-outline" size={64} color={theme.textDisabled} />}
          title="Sin envíos"
          subtitle="Crea tu primer envío para comenzar"
          actionLabel="Nuevo envío"
          onAction={() => navigation.navigate('Inicio')}
        />
      ) : (
        <FlatList
          data={shipments}
          keyExtractor={(item) => (item.id || item._id || Math.random()).toString()}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[10],
    paddingBottom: spacing[3],
  },
  headerTitle: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: '700',
  },
  headerSubtitle: {
    fontSize: typography.fontSize.sm,
    marginTop: 2,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listContent: {
    paddingHorizontal: spacing[4],
    paddingBottom: spacing[10],
  },
  shipmentCard: {
    marginBottom: spacing[3],
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing[3],
  },
  trackingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
  },
  trackingNumber: {
    fontSize: typography.fontSize.base,
    fontWeight: '700',
  },
  routeContainer: {
    marginBottom: spacing[3],
  },
  routePoint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
  },
  routeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  routeText: {
    fontSize: typography.fontSize.sm,
    flex: 1,
  },
  routeLine: {
    width: 2,
    height: 16,
    backgroundColor: colors.neutral[200],
    marginLeft: 3,
    marginVertical: 2,
  },
  cardFooter: {
    alignItems: 'flex-end',
  },
  lastUpdate: {
    fontSize: typography.fontSize.xs,
  },
});
