import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme-context';
import Card from '../shared/components/Card';
import Badge from '../shared/components/Badge';
import EmptyState from '../shared/components/EmptyState';
import { get } from '../shared/api';
import { formatCurrency, formatDate } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

const FILTERS = [
  { id: 'all', label: 'Todas' },
  { id: 'pending', label: 'Pendientes' },
  { id: 'paid', label: 'Pagadas' },
  { id: 'cancelled', label: 'Canceladas' },
];

export default function InvoicesScreen({ navigation }) {
  const { theme } = useTheme();
  const [invoices, setInvoices] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');
  const [monthlyTotal, setMonthlyTotal] = useState(0);

  const fetchInvoices = useCallback(async () => {
    try {
      const data = await get('/api/invoices');
      const list = Array.isArray(data) ? data : data?.invoices || data?.data || [];
      setInvoices(list);
      applyFilter(list, activeFilter);

      const now = new Date();
      const thisMonth = list.filter((inv) => {
        const d = new Date(inv.created_at || inv.date);
        return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
      });
      const total = thisMonth.reduce((sum, inv) => sum + (inv.total || inv.amount || 0), 0);
      setMonthlyTotal(total);
    } catch (error) {
      console.error('Invoices fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchInvoices();
    setRefreshing(false);
  }, [fetchInvoices]);

  const applyFilter = (list, filter) => {
    switch (filter) {
      case 'pending':
        setFiltered(list.filter((i) => i.status === 'pending' || i.status === 'PENDING'));
        break;
      case 'paid':
        setFiltered(list.filter((i) => i.status === 'paid' || i.status === 'PAID'));
        break;
      case 'cancelled':
        setFiltered(list.filter((i) => i.status === 'cancelled' || i.status === 'CANCELLED'));
        break;
      default:
        setFiltered(list);
    }
  };

  const handleFilterChange = (filterId) => {
    setActiveFilter(filterId);
    applyFilter(invoices, filterId);
  };

  const handleDownloadPDF = (invoice) => {
    const url = invoice.pdf_url || invoice.download_url;
    if (url) {
      Linking.openURL(url);
    } else {
      Alert.alert('PDF no disponible', 'El PDF de esta factura aún no está disponible.');
    }
  };

  const handleSendEmail = (invoice) => {
    Alert.alert(
      'Enviar por email',
      `Se enviará la factura ${invoice.folio || invoice.number || invoice.id} al correo registrado.`,
      [{ text: 'Entendido' }]
    );
  };

  const getInvoiceStatus = (status) => {
    const map = {
      pending: { label: 'Pendiente', color: colors.warning[600], bgColor: colors.warning[50] },
      PENDING: { label: 'Pendiente', color: colors.warning[600], bgColor: colors.warning[50] },
      paid: { label: 'Pagada', color: colors.success[600], bgColor: colors.success[50] },
      PAID: { label: 'Pagada', color: colors.success[600], bgColor: colors.success[50] },
      cancelled: { label: 'Cancelada', color: colors.error[500], bgColor: colors.error[50] },
      CANCELLED: { label: 'Cancelada', color: colors.error[500], bgColor: colors.error[50] },
    };
    return map[status] || { label: status || '—', color: colors.neutral[500], bgColor: colors.neutral[100] };
  };

  const renderItem = ({ item }) => {
    const statusInfo = getInvoiceStatus(item.status);
    return (
      <Card style={[styles.invoiceCard, { backgroundColor: theme.surface }]}>
        <View style={styles.invoiceHeader}>
          <View>
            <Text style={[styles.invoiceNumber, { color: theme.text }]}>
              {item.folio || item.number || `#${item.id}`}
            </Text>
            <Text style={[styles.invoiceDate, { color: theme.textSecondary }]}>
              {formatDate(item.created_at || item.date)}
            </Text>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: statusInfo.bgColor }]}>
            <Text style={[styles.statusText, { color: statusInfo.color }]}>{statusInfo.label}</Text>
          </View>
        </View>

        <Text style={[styles.invoiceAmount, { color: theme.text }]}>
          {formatCurrency(item.total || item.amount || 0)}
        </Text>

        <View style={styles.invoiceActions}>
          <TouchableOpacity
            style={[styles.invoiceAction, { backgroundColor: theme.surfaceVariant }]}
            onPress={() => handleDownloadPDF(item)}
          >
            <Ionicons name="document-outline" size={18} color={theme.primary} />
            <Text style={[styles.invoiceActionText, { color: theme.primary }]}>PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.invoiceAction, { backgroundColor: theme.surfaceVariant }]}
            onPress={() => handleSendEmail(item)}
          >
            <Ionicons name="mail-outline" size={18} color={theme.primary} />
            <Text style={[styles.invoiceActionText, { color: theme.primary }]}>Email</Text>
          </TouchableOpacity>
        </View>
      </Card>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Facturas</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          Total este mes: {formatCurrency(monthlyTotal)}
        </Text>
      </View>

      {/* Filters */}
      <View style={styles.filterContainer}>
        {FILTERS.map((filter) => (
          <TouchableOpacity
            key={filter.id}
            style={[
              styles.filterChip,
              {
                backgroundColor: activeFilter === filter.id ? theme.primary : theme.surface,
                borderColor: activeFilter === filter.id ? theme.primary : theme.border,
              },
            ]}
            onPress={() => handleFilterChange(filter.id)}
          >
            <Text
              style={[
                styles.filterText,
                {
                  color: activeFilter === filter.id ? '#fff' : theme.textSecondary,
                },
              ]}
            >
              {filter.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
        </View>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Ionicons name="receipt-outline" size={64} color={theme.textDisabled} />}
          title="Sin facturas"
          subtitle="Tus facturas aparecerán aquí"
        />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => (item.id || Math.random()).toString()}
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
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: spacing[4],
    gap: spacing[2],
    marginBottom: spacing[4],
  },
  filterChip: {
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[2],
    borderRadius: borderRadius.full,
    borderWidth: 1,
  },
  filterText: {
    fontSize: typography.fontSize.sm,
    fontWeight: '600',
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
  invoiceCard: {
    marginBottom: spacing[3],
  },
  invoiceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing[2],
  },
  invoiceNumber: {
    fontSize: typography.fontSize.base,
    fontWeight: '700',
  },
  invoiceDate: {
    fontSize: typography.fontSize.xs,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: spacing[3],
    paddingVertical: spacing[1],
    borderRadius: borderRadius.full,
  },
  statusText: {
    fontSize: typography.fontSize.xs,
    fontWeight: '600',
  },
  invoiceAmount: {
    fontSize: typography.fontSize.xl,
    fontWeight: '800',
    marginBottom: spacing[3],
  },
  invoiceActions: {
    flexDirection: 'row',
    gap: spacing[3],
  },
  invoiceAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
    paddingHorizontal: spacing[3],
    paddingVertical: spacing[2],
    borderRadius: borderRadius.md,
  },
  invoiceActionText: {
    fontSize: typography.fontSize.sm,
    fontWeight: '600',
  },
});
