import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme-context';
import useAuth from '../hooks/useAuth';
import Card from '../shared/components/Card';
import Avatar from '../shared/components/Avatar';
import { get } from '../shared/api';
import { formatCurrency } from '../shared/formatters';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

export default function ProfileScreen({ navigation }) {
  const { theme, toggleTheme, isDarkMode } = useTheme();
  const { user, logout } = useAuth();
  const [stats, setStats] = useState({ totalShipments: 0, totalSpent: 0 });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await get('/api/shipments/stats');
      setStats({
        totalShipments: data?.total || data?.totalShipments || 0,
        totalSpent: data?.totalSpent || data?.totalSpent || 0,
      });
    } catch (error) {
      console.error('Stats fetch error:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert('Cerrar sesión', '¿Estás seguro de que deseas cerrar sesión?', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Cerrar sesión', style: 'destructive', onPress: logout },
    ]);
  };

  const menuItems = [
    {
      id: 'tax',
      label: 'Datos fiscales',
      icon: 'document-text',
      color: colors.primary[500],
    },
    {
      id: 'addresses',
      label: 'Direcciones guardadas',
      icon: 'location',
      color: colors.success[500],
    },
    {
      id: 'payments',
      label: 'Métodos de pago',
      icon: 'card',
      color: '#7c3aed',
    },
    {
      id: 'notifications',
      label: 'Notificaciones',
      icon: 'notifications',
      color: colors.accent[500],
    },
    {
      id: 'support',
      label: 'Soporte',
      icon: 'help-circle',
      color: colors.error[500],
    },
    {
      id: 'about',
      label: 'Acerca de',
      icon: 'information-circle',
      color: colors.neutral[500],
    },
  ];

  const handleMenuPress = (id) => {
    switch (id) {
      case 'support':
        Alert.alert('Soporte', 'Contacta soporte en: soporte@lastmile-platform.onrender.com');
        break;
      case 'about':
        Alert.alert(
          'Last Mile',
          'Versión 2.0.0\n\nTu plataforma de delivery de confianza.\n\n© 2026 Last Mile Platform'
        );
        break;
      default:
        Alert.alert('Próximamente', 'Esta funcionalidad estará disponible pronto.');
    }
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* Profile Header */}
      <View style={[styles.profileHeader, { backgroundColor: theme.primary }]}>
        <Avatar name={user?.nombre || 'Cliente'} size="lg" />
        <Text style={styles.profileName}>{user?.nombre || 'Cliente'}</Text>
        {user?.empresa && (
          <Text style={styles.profileCompany}>{user.empresa}</Text>
        )}
      </View>

      {/* Account Info */}
      <Card style={[styles.infoCard, { backgroundColor: theme.surface, marginTop: -20 }]}>
        <View style={styles.infoRow}>
          <Ionicons name="mail-outline" size={18} color={theme.textSecondary} />
          <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Email</Text>
          <Text style={[styles.infoValue, { color: theme.text }]}>
            {user?.email || '—'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Ionicons name="call-outline" size={18} color={theme.textSecondary} />
          <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Teléfono</Text>
          <Text style={[styles.infoValue, { color: theme.text }]}>
            {user?.phone || user?.telefono || '—'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Ionicons name="card-outline" size={18} color={theme.textSecondary} />
          <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>RFC</Text>
          <Text style={[styles.infoValue, { color: theme.text }]}>
            {user?.rfc || '—'}
          </Text>
        </View>
      </Card>

      {/* Stats */}
      <View style={styles.statsRow}>
        <Card style={[styles.statCard, { backgroundColor: theme.surface }]}>
          <Text style={[styles.statNumber, { color: theme.primary }]}>
            {stats.totalShipments}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
            Envíos totales
          </Text>
        </Card>
        <Card style={[styles.statCard, { backgroundColor: theme.surface }]}>
          <Text style={[styles.statNumber, { color: colors.success[500] }]}>
            {formatCurrency(stats.totalSpent)}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
            Total gastado
          </Text>
        </Card>
      </View>

      {/* Dark Mode Toggle */}
      <Card style={[styles.settingCard, { backgroundColor: theme.surface }]}>
        <View style={styles.settingRow}>
          <View style={styles.settingLeft}>
            <Ionicons
              name={isDarkMode ? 'moon' : 'sunny'}
              size={20}
              color={theme.primary}
            />
            <Text style={[styles.settingLabel, { color: theme.text }]}>Modo oscuro</Text>
          </View>
          <Switch
            value={isDarkMode}
            onValueChange={toggleTheme}
            trackColor={{ false: colors.neutral[300], true: colors.primary[300] }}
            thumbColor={isDarkMode ? colors.primary[500] : '#f4f3f4'}
          />
        </View>
      </Card>

      {/* Menu */}
      <Card style={[styles.menuCard, { backgroundColor: theme.surface }]}>
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={item.id}
            style={[
              styles.menuItem,
              index < menuItems.length - 1 && {
                borderBottomWidth: 1,
                borderBottomColor: theme.border,
              },
            ]}
            onPress={() => handleMenuPress(item.id)}
          >
            <View style={[styles.menuIcon, { backgroundColor: item.color + '15' }]}>
              <Ionicons name={item.icon} size={20} color={item.color} />
            </View>
            <Text style={[styles.menuLabel, { color: theme.text }]}>{item.label}</Text>
            <Ionicons name="chevron-forward" size={18} color={theme.textDisabled} />
          </TouchableOpacity>
        ))}
      </Card>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={20} color={colors.error[500]} />
        <Text style={styles.logoutText}>Cerrar sesión</Text>
      </TouchableOpacity>

      {/* Version */}
      <Text style={[styles.version, { color: theme.textDisabled }]}>
        Last Mile v2.0.0
      </Text>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: spacing[10],
  },
  profileHeader: {
    alignItems: 'center',
    paddingTop: spacing[12],
    paddingBottom: spacing[8],
    borderBottomLeftRadius: borderRadius.xl,
    borderBottomRightRadius: borderRadius.xl,
  },
  profileName: {
    fontSize: typography.fontSize.xl,
    fontWeight: '700',
    color: '#fff',
    marginTop: spacing[3],
  },
  profileCompany: {
    fontSize: typography.fontSize.sm,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 2,
  },
  infoCard: {
    marginHorizontal: spacing[4],
    ...shadows.md,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing[3],
    gap: spacing[3],
  },
  infoLabel: {
    fontSize: typography.fontSize.sm,
    width: 70,
  },
  infoValue: {
    fontSize: typography.fontSize.sm,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing[4],
    gap: spacing[3],
    marginTop: spacing[4],
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing[4],
  },
  statNumber: {
    fontSize: typography.fontSize.xl,
    fontWeight: '800',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: typography.fontSize.xs,
  },
  settingCard: {
    marginHorizontal: spacing[4],
    marginTop: spacing[4],
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[3],
  },
  settingLabel: {
    fontSize: typography.fontSize.base,
    fontWeight: '500',
  },
  menuCard: {
    marginHorizontal: spacing[4],
    marginTop: spacing[4],
    padding: 0,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[4],
    gap: spacing[3],
  },
  menuIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuLabel: {
    fontSize: typography.fontSize.base,
    fontWeight: '500',
    flex: 1,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[2],
    marginHorizontal: spacing[4],
    marginTop: spacing[6],
    paddingVertical: spacing[4],
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.error[200],
    backgroundColor: colors.error[50],
  },
  logoutText: {
    fontSize: typography.fontSize.base,
    fontWeight: '600',
    color: colors.error[500],
  },
  version: {
    textAlign: 'center',
    fontSize: typography.fontSize.xs,
    marginTop: spacing[4],
  },
});
