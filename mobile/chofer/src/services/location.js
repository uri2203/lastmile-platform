import * as TaskManager from 'expo-task-manager';
import * as Location from 'expo-location';

const BACKGROUND_TASK_NAME = 'background-location-task';

export async function requestPermissions() {
  const { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();
  if (foregroundStatus !== 'granted') {
    return { foreground: false, background: false };
  }

  const { status: backgroundStatus } = await Location.requestBackgroundPermissionsAsync();
  return { foreground: true, background: backgroundStatus === 'granted' };
}

export async function startBackgroundLocation() {
  const { status } = await Location.getForegroundPermissionsAsync();
  if (status !== 'granted') {
    const result = await requestPermissions();
    if (!result.foreground) return false;
  }

  const isRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_TASK_NAME);
  if (isRegistered) return true;

  try {
    await Location.startLocationUpdatesAsync(BACKGROUND_TASK_NAME, {
      accuracy: Location.Accuracy.Balanced,
      distanceInterval: 50,
      deferredUpdatesInterval: 30000,
      showsBackgroundLocationIndicator: true,
      foregroundService: {
        notificationTitle: 'Last Mile Delivery',
        notificationBody: 'Rastreando ubicación para entrega',
        notificationColor: '#6366f1',
      },
    });
    return true;
  } catch (error) {
    console.error('Failed to start background location:', error);
    return false;
  }
}

export async function stopBackgroundLocation() {
  try {
    const isRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_TASK_NAME);
    if (isRegistered) {
      await Location.stopLocationUpdatesAsync(BACKGROUND_TASK_NAME);
    }
  } catch (error) {
    console.error('Failed to stop background location:', error);
  }
}

export async function getCurrentLocation() {
  try {
    const { status } = await Location.getForegroundPermissionsAsync();
    if (status !== 'granted') {
      const result = await Location.requestForegroundPermissionsAsync();
      if (result.status !== 'granted') return null;
    }

    const location = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.High,
    });

    return {
      latitude: location.coords.latitude,
      longitude: location.coords.longitude,
    };
  } catch (error) {
    console.error('Failed to get current location:', error);
    return null;
  }
}

export async function reportLocationToAPI(latitude, longitude) {
  try {
    const { post } = await import('../shared/api');
    await post('/api/gps/update', {
      latitude,
      longitude,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Failed to report location to API:', error);
  }
}

export default {
  BACKGROUND_TASK_NAME,
  requestPermissions,
  startBackgroundLocation,
  stopBackgroundLocation,
  getCurrentLocation,
  reportLocationToAPI,
};
