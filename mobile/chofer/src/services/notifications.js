import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { post } from '../../../shared/api';
import { TOKEN_KEY } from '../../../shared/auth';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

let notificationListener = null;
let responseListener = null;

export async function requestNotificationPermissions() {
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return false;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('deliveries', {
      name: 'Entregas',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#6366f1',
    });
  }

  return true;
}

export async function registerForPushNotifications() {
  try {
    const hasPermission = await requestNotificationPermissions();
    if (!hasPermission) return null;

    const tokenData = await Notifications.getExpoPushTokenAsync();
    const pushToken = tokenData.data;

    const storedToken = await SecureStore.getItemAsync(TOKEN_KEY);
    if (storedToken) {
      try {
        await post('/api/push/register', {
          push_token: pushToken,
          platform: Platform.OS,
        });
      } catch (error) {
        console.error('Failed to register push token:', error);
      }
    }

    return pushToken;
  } catch (error) {
    console.error('Error registering for push notifications:', error);
    return null;
  }
}

export function setupNotificationListeners(navigation) {
  notificationListener = Notifications.addNotificationReceivedListener((notification) => {
    console.log('Notification received:', notification);
  });

  responseListener = Notifications.addNotificationResponseReceivedListener((response) => {
    const data = response.notification.request.content.data;
    if (data?.deliveryId && navigation) {
      navigation.navigate('Entregas', {
        screen: 'DeliveryDetail',
        params: { deliveryId: data.deliveryId },
      });
    }
  });

  return () => {
    if (notificationListener) {
      Notifications.removeNotificationSubscription(notificationListener);
    }
    if (responseListener) {
      Notifications.removeNotificationSubscription(responseListener);
    }
  };
}

export async function sendLocalNotification(title, body, data = {}) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      data,
      sound: true,
      priority: Notifications.AndroidNotificationPriority.HIGH,
    },
    trigger: null,
  });
}

export async function clearAllNotifications() {
  await Notifications.dismissAllNotificationsAsync();
  await Notifications.cancelAllScheduledNotificationsAsync();
}

export default {
  requestNotificationPermissions,
  registerForPushNotifications,
  setupNotificationListeners,
  sendLocalNotification,
  clearAllNotifications,
};
