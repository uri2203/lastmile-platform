import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../api';

const QUEUE_KEY = 'lastmile_chofer_offline_queue';

async function getQueue() {
  try {
    const raw = await AsyncStorage.getItem(QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

async function setQueue(queue) {
  try {
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
  } catch (e) {
    // no-op: si falla guardar la cola no hay mucho que hacer, el intento
    // original ya se le informo al chofer como "guardado offline".
  }
}

// Se llama cuando markDelivered/markFailed/reportLocation fallan por falta
// de red -- guarda la accion para reintentarla mas tarde en vez de perderla.
export async function enqueue(action) {
  const queue = await getQueue();
  queue.push({ ...action, queuedAt: Date.now() });
  await setQueue(queue);
}

export async function getQueueLength() {
  return (await getQueue()).length;
}

const HANDLERS = {
  markDelivered: (item) => api.markDelivered(item.entId, item.evidencia),
  markFailed: (item) => api.markFailed(item.entId, item.motivo),
  reportLocation: (item) => api.reportLocation(item.choId, item.latitud, item.longitud, item.velocidad),
};

// Reintenta todo lo pendiente. Se llama al abrir la app / entrar a la
// pantalla de entregas / reconectar. No lanza errores: si un item sigue
// sin poder mandarse, se queda en la cola para el proximo intento.
export async function flushQueue() {
  const queue = await getQueue();
  if (queue.length === 0) return { sent: 0, remaining: 0 };

  const remaining = [];
  let sent = 0;
  for (const item of queue) {
    const handler = HANDLERS[item.type];
    if (!handler) continue; // tipo desconocido (version vieja de la cola): se descarta
    try {
      await handler(item);
      sent++;
    } catch (e) {
      if (e.code === 'NETWORK') {
        remaining.push(item); // sigue sin red, reintentar despues
      }
      // otros errores (ej. ya no existe la entrega) se descartan: reintentar
      // por siempre algo que el servidor rechaza no tiene sentido.
    }
  }
  await setQueue(remaining);
  return { sent, remaining: remaining.length };
}
