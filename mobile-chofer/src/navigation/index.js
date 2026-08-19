import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';

import DeliveriesScreen from '../screens/DeliveriesScreen';
import DeliveryDetailScreen from '../screens/DeliveryDetailScreen';
import HistoryScreen from '../screens/HistoryScreen';
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
  return (
    <DeliveriesStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.bgSecondary },
        headerTitleStyle: { color: colors.textPrimary },
        headerTintColor: colors.accent,
      }}
    >
      <DeliveriesStack.Screen name="MisEntregas" component={DeliveriesScreen} options={{ title: 'Mis Entregas' }} />
      <DeliveriesStack.Screen name="DeliveryDetail" component={DeliveryDetailScreen} options={{ title: 'Detalle de Entrega' }} />
    </DeliveriesStack.Navigator>
  );
}

export default function RootNavigator() {
  return (
    <NavigationContainer theme={navTheme}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: { backgroundColor: colors.bgSecondary, borderTopColor: colors.borderPrimary },
          tabBarActiveTintColor: colors.accent,
          tabBarInactiveTintColor: colors.textMuted,
          tabBarIcon: ({ color, size }) => {
            const icons = { Entregas: 'cube', Historial: 'time', Perfil: 'person' };
            return <Ionicons name={icons[route.name] || 'ellipse'} size={size} color={color} />;
          },
        })}
      >
        <Tab.Screen name="Entregas" component={DeliveriesStackScreen} />
        <Tab.Screen name="Historial" component={HistoryScreen} />
        <Tab.Screen name="Perfil" component={ProfileScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
