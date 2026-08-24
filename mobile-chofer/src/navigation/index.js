import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';
import { useI18n } from '../i18n';

import DeliveriesScreen from '../screens/DeliveriesScreen';
import DeliveryDetailScreen from '../screens/DeliveryDetailScreen';
import HistoryScreen from '../screens/HistoryScreen';
import PerformanceScreen from '../screens/PerformanceScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Tab = createBottomTabNavigator();
const DeliveriesStack = createNativeStackNavigator();

const navTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: colors.bgPrimary,
    card: colors.bgSecondary,
    text: colors.textPrimary,
    border: colors.borderPrimary,
    primary: colors.accent,
  },
};

function DeliveriesStackScreen() {
  const { t } = useI18n();
  return (
    <DeliveriesStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.bgSecondary },
        headerTitleStyle: { color: colors.textPrimary },
        headerTintColor: colors.accent,
      }}
    >
      <DeliveriesStack.Screen name="MisEntregas" component={DeliveriesScreen} options={{ title: t('chofer_app.mis_entregas_titulo') }} />
      <DeliveriesStack.Screen name="DeliveryDetail" component={DeliveryDetailScreen} options={{ title: t('chofer_app.detalle_entrega_titulo') }} />
    </DeliveriesStack.Navigator>
  );
}

export default function RootNavigator() {
  const { t } = useI18n();
  const TAB_LABELS = {
    Entregas: t('chofer_app.nav_entregas'),
    Historial: t('chofer_app.nav_historial'),
    Rendimiento: t('chofer_app.nav_rendimiento'),
    Perfil: t('chofer_app.nav_perfil'),
  };
  return (
    <NavigationContainer theme={navTheme}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarLabel: TAB_LABELS[route.name] || route.name,
          tabBarStyle: { backgroundColor: colors.bgSecondary, borderTopColor: colors.borderPrimary },
          tabBarActiveTintColor: colors.accent,
          tabBarInactiveTintColor: colors.textMuted,
          tabBarIcon: ({ color, size }) => {
            const icons = { Entregas: 'cube', Historial: 'time', Rendimiento: 'stats-chart', Perfil: 'person' };
            return <Ionicons name={icons[route.name] || 'ellipse'} size={size} color={color} />;
          },
        })}
      >
        <Tab.Screen name="Entregas" component={DeliveriesStackScreen} />
        <Tab.Screen name="Historial" component={HistoryScreen} />
        <Tab.Screen name="Rendimiento" component={PerformanceScreen} />
        <Tab.Screen name="Perfil" component={ProfileScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
