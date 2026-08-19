import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { BASE_URL, getToken } from '../api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/**
 * Pide permiso, obtiene el push token de Expo y lo registra en el backend
 * via /api/notif/dispositivos (endpoint generico ya existente, plataforma='EXPO').
 * Devuelve el token, o null si el usuario no dio permiso.
 */
export async function registerForPushNotifications(usuId, choId) {
  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;
  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    return null;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
    });
  }

  const tokenResponse = await Notifications.getExpoPushTokenAsync();
  const token = tokenResponse.data;

  try {
    const authToken = await getToken();
    await fetch(`${BASE_URL}/api/notif/dispositivos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
      body: JSON.stringify({ usrId: usuId, choId, token, plataforma: 'EXPO' }),
    });
  } catch (e) {
    console.warn('[notifications] no se pudo registrar el push token:', e.message);
  }

  return token;
}
