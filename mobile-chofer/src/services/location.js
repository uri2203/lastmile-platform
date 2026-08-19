import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { api } from '../api';
import * as SecureStore from 'expo-secure-store';

const LOCATION_TASK = 'lastmile-chofer-location-task';
const CHO_ID_KEY = 'lastmile_chofer_cho_id';

// El task de background no puede leer React state -- guarda el CHO_ID actual
// en SecureStore para que el task lo lea cuando el SO lo despierte.
export async function setTrackedChoferId(choId) {
  if (choId) await SecureStore.setItemAsync(CHO_ID_KEY, String(choId));
  else await SecureStore.deleteItemAsync(CHO_ID_KEY);
}

TaskManager.defineTask(LOCATION_TASK, async ({ data, error }) => {
  if (error) {
    console.error('[location-task] error:', error);
    return;
  }
  if (!data) return;
  const { locations } = data;
  const loc = locations?.[0];
  if (!loc) return;
  try {
    const choId = await SecureStore.getItemAsync(CHO_ID_KEY);
    if (!choId) return;
    const speedKmh = loc.coords.speed && loc.coords.speed > 0 ? loc.coords.speed * 3.6 : 0;
    await api.reportLocation(Number(choId), loc.coords.latitude, loc.coords.longitude, speedKmh);
  } catch (e) {
    // Sin conexion o token expirado: se pierde este punto, el siguiente reintenta.
    console.warn('[location-task] no se pudo reportar posicion:', e.message);
  }
});

export async function startTracking(choId) {
  const { status: fgStatus } = await Location.requestForegroundPermissionsAsync();
  if (fgStatus !== 'granted') {
    throw new Error('Se necesita permiso de ubicacion para reportar tu posicion durante las entregas.');
  }
  await Location.requestBackgroundPermissionsAsync(); // best-effort; en foreground igual funciona

  await setTrackedChoferId(choId);

  const already = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK).catch(() => false);
  if (already) return;

  await Location.startLocationUpdatesAsync(LOCATION_TASK, {
    accuracy: Location.Accuracy.Balanced,
    timeInterval: 30000, // cada 30s, igual que el resto de la plataforma (ver panel-operacion GPS)
    distanceInterval: 50, // o cada 50m
    showsBackgroundLocationIndicator: true,
    foregroundService: {
      notificationTitle: 'Last Mile Chofer',
      notificationBody: 'Reportando tu ubicacion mientras entregas pedidos',
    },
  });
}

export async function stopTracking() {
  const running = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK).catch(() => false);
  if (running) await Location.stopLocationUpdatesAsync(LOCATION_TASK);
  await setTrackedChoferId(null);
}

export async function isTracking() {
  return Location.hasStartedLocationUpdatesAsync(LOCATION_TASK).catch(() => false);
}
