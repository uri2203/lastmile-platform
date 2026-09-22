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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../App';
import Card from '../../shared/components/Card';
import Avatar from '../../shared/components/Avatar';
import Button from '../../shared/components/Button';
import { get } from '../../shared/api';
import { colors, typography, spacing, borderRadius, shadows } from '../../shared/theme';
import useAuth from '../hooks/useAuth';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme, isDarkMode } = useTheme();
  const insets = useSafeAreaInsets();

  const [stats, setStats] = useState({
    today: 0,
    week: 0,
    month: 0,
    rating: 0,
  });
  const [gpsEnabled, setGpsEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await get('/api/chofer/stats');
      setStats({
        today: data?.today || 0,
        week: data?.week || 0,
        month: data?.month || 0,
        rating: data?.rating || 0,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert('Cerrar Sesión', '¿Estás seguro que deseas cerrar sesión?', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Cerrar Sesión', style: 'destructive', onPress: logout },
    ]);
  };

  const handleMenuPress = (title) => {
    Alert.alert(title, 'Función próximamente disponible');
  };

  const menuItems = [
    { icon: 'document-text-outline', label: 'Mis documentos', key: 'documents' },
    { icon: 'wallet-outline', label: 'Historial de pagos', key: 'payments' },
    { icon: 'chatbubble-ellipses-outline', label: 'Soporte', key: 'support' },
    { icon: 'information-circle-outline', label: 'Acerca de', key: 'about' },
  ];

  return (
    <View style={[styles.container, { backgroundColor: theme.background, paddingTop: insets.top }]}>
      <View style={[styles.header, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Perfil</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.profileSection}>
          <View style={styles.avatarContainer}>
            <Avatar name={user?.nombre || 'Chofer'} size="lg" online={gpsEnabled} />
            <TouchableOpacity style={[styles.cameraBtn, { backgroundColor: theme.primary }]}>
              <Ionicons name="camera" size={16} color="#ffffff" />
            </TouchableOpacity>
          </View>
          <Text style={[styles.userName, { color: theme.text }]}>{user?.nombre || 'Chofer'}</Text>
          <Text style={[styles.userEmail, { color: theme.textSecondary }]}>{user?.email || 'correo@ejemplo.com'}</Text>
          {user?.telefono && (
            <Text style={[styles.userPhone, { color: theme.textSecondary }]}>{user.telefono}</Text>
          )}
        </View>

        <View style={[styles.statsGrid, { backgroundColor: theme.surface, borderColor: theme.cardBorder }]}>
          <ProfileStat icon="cube-outline" label="Hoy" value={stats.today} color={theme.primary} theme={theme} />
          <ProfileStat icon="calendar-outline" label="Semana" value={stats.week} color={colors.accent[500]} theme={theme} />
          <ProfileStat icon="bar-chart-outline" label="Mes" value={stats.month} color={colors.success[500]} theme={theme} />
          <ProfileStat icon="star-outline" label="Rating" value={stats.rating.toFixed(1)} color={colors.accent[400]} theme={theme} />
        </View>

        <Card style={[styles.settingsCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Configuración</Text>

          <View style={[styles.settingRow, { borderBottomColor: theme.border }]}>
            <View style={styles.settingLeft}>
              <Ionicons name="navigate" size={20} color={theme.primary} />
              <Text style={[styles.settingLabel, { color: theme.text }]}>Rastreo GPS</Text>
            </View>
            <Switch
              value={gpsEnabled}
              onValueChange={setGpsEnabled}
              trackColor={{ false: theme.border, true: theme.primary + '60' }}
              thumbColor={gpsEnabled ? theme.primary : theme.textDisabled}
            />
          </View>

          <View style={[styles.settingRow, { borderBottomColor: theme.border }]}>
            <View style={styles.settingLeft}>
              <Ionicons name="notifications" size={20} color={colors.accent[500]} />
              <Text style={[styles.settingLabel, { color: theme.text }]}>Notificaciones</Text>
            </View>
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: theme.border, true: colors.accent[500] + '60' }}
              thumbColor={notificationsEnabled ? colors.accent[500] : theme.textDisabled}
            />
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingLeft}>
              <Ionicons name="moon" size={20} color={colors.primary[400]} />
              <Text style={[styles.settingLabel, { color: theme.text }]}>Modo oscuro</Text>
            </View>
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{ false: theme.border, true: colors.primary[400] + '60' }}
              thumbColor={isDarkMode ? colors.primary[400] : theme.textDisabled}
            />
          </View>
        </Card>

        <Card style={[styles.menuCard, { backgroundColor: theme.card, borderColor: theme.cardBorder }]}>
          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={item.key}
              style={[
                styles.menuRow,
                index < menuItems.length - 1 && { borderBottomColor: theme.border, borderBottomWidth: 1 },
              ]}
              onPress={() => handleMenuPress(item.label)}
            >
              <View style={styles.menuLeft}>
                <Ionicons name={item.icon} size={22} color={theme.textSecondary} />
                <Text style={[styles.menuLabel, { color: theme.text }]}>{item.label}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={theme.textDisabled} />
            </TouchableOpacity>
          ))}
        </Card>

        <Button
          title="Cerrar Sesión"
          onPress={handleLogout}
          variant="danger"
          size="lg"
          icon={<Ionicons name="log-out-outline" size={20} color="#ffffff" />}
          style={styles.logoutBtn}
        />

        <Text style={[styles.versionText, { color: theme.textDisabled }]}>
          Last Mile Chofer v2.0.0
        </Text>
      </ScrollView>
    </View>
  );
}

function ProfileStat({ icon, label, value, color, theme }) {
  return (
    <View style={styles.profileStatItem}>
      <View style={[styles.profileStatIcon, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={[styles.profileStatValue, { color: theme.text }]}>{value}</Text>
      <Text style={[styles.profileStatLabel, { color: theme.textSecondary }]}>{label}</Text>
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
  scrollContent: { paddingBottom: 40 },
  profileSection: { alignItems: 'center', paddingVertical: spacing[8] },
  avatarContainer: { position: 'relative', marginBottom: spacing[4] },
  cameraBtn: {
    position: 'absolute',
    bottom: 0,
    right: -4,
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#ffffff',
  },
  userName: { fontSize: typography.fontSize['2xl'], fontWeight: '700', marginBottom: spacing[1] },
  userEmail: { fontSize: typography.fontSize.base, marginBottom: 2 },
  userPhone: { fontSize: typography.fontSize.sm },
  statsGrid: {
    flexDirection: 'row',
    marginHorizontal: spacing[4],
    marginBottom: spacing[4],
    borderRadius: borderRadius.lg,
    paddingVertical: spacing[4],
    borderWidth: 1,
    ...shadows.sm,
  },
  profileStatItem: { flex: 1, alignItems: 'center' },
  profileStatIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginBottom: spacing[2] },
  profileStatValue: { fontSize: typography.fontSize.lg, fontWeight: '700' },
  profileStatLabel: { fontSize: typography.fontSize.xs, marginTop: 2 },
  settingsCard: { marginHorizontal: spacing[4], marginBottom: spacing[4] },
  sectionTitle: { fontSize: typography.fontSize.lg, fontWeight: '700', marginBottom: spacing[4] },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing[3],
    borderBottomWidth: 1,
  },
  settingLeft: { flexDirection: 'row', alignItems: 'center' },
  settingLabel: { fontSize: typography.fontSize.base, fontWeight: '500', marginLeft: spacing[3] },
  menuCard: { marginHorizontal: spacing[4], marginBottom: spacing[4] },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing[4],
  },
  menuLeft: { flexDirection: 'row', alignItems: 'center' },
  menuLabel: { fontSize: typography.fontSize.base, fontWeight: '500', marginLeft: spacing[3] },
  logoutBtn: { marginHorizontal: spacing[4], marginBottom: spacing[4] },
  versionText: { textAlign: 'center', fontSize: typography.fontSize.xs },
});
