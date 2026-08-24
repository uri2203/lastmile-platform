import * as Updates from 'expo-updates';

const STARTUP_TIMEOUT_MS = 8000;

function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)),
  ]);
}

// Revisa si hay una actualizacion de JS publicada (via `eas update`), la
// descarga y reinicia la app para aplicarla. Se llama una vez al arrancar,
// asi el chofer siempre ve la ultima version sin tener que reinstalar el
// APK -- el APK solo hace falta reinstalarlo cuando cambia codigo nativo
// (nueva libreria, permisos nuevos, etc.), no para cambios normales de JS.
//
// Con timeout: si la red anda lenta o no hay conexion, no bloquea el arranque
// de la app mas de STARTUP_TIMEOUT_MS -- se sigue con la version ya instalada
// y se puede reintentar mas tarde a mano desde Perfil (checkForUpdateManual).
export async function checkAndApplyUpdate() {
  if (!Updates.isEnabled || __DEV__) return false;
  try {
    const result = await withTimeout(Updates.checkForUpdateAsync(), STARTUP_TIMEOUT_MS);
    if (!result.isAvailable) return false;
    await withTimeout(Updates.fetchUpdateAsync(), STARTUP_TIMEOUT_MS);
    await Updates.reloadAsync();
    return true; // no deberia llegar aca (reloadAsync reinicia la app)
  } catch (e) {
    console.warn('[updates] no se pudo revisar/aplicar actualizacion:', e.message);
    return false;
  }
}

// Version para el boton manual en Perfil: sin timeout corto (el usuario ya
// eligio esperar), y devuelve un resultado descriptivo para mostrar feedback
// en pantalla en vez de solo loguear a consola.
//
// Siempre termina en reloadAsync(), haya o no una actualizacion nueva para
// bajar. Motivo: el chequeo automatico nativo (CHECK_ON_LAUNCH=ALWAYS) puede
// descargar una version mas nueva en segundo plano SIN aplicarla -- recien
// se activa en el proximo arranque en frio. Eso hacia que este boton dijera
// "ya estas al dia" (cierto sobre lo descargado) mientras la app seguia
// corriendo en memoria la version vieja, y el chofer terminaba teniendo que
// desinstalar/reinstalar para verla. Forzar el reload aca lo resuelve sin
// salir de la app.
export async function checkForUpdateManual() {
  if (!Updates.isEnabled || __DEV__) {
    return { status: 'disabled' };
  }
  try {
    const result = await Updates.checkForUpdateAsync();
    if (result.isAvailable) {
      await Updates.fetchUpdateAsync();
    }
    await Updates.reloadAsync();
    return { status: 'updated' }; // no deberia llegar aca (reloadAsync reinicia la app)
  } catch (e) {
    return { status: 'error', message: e.message };
  }
}

export function getCurrentUpdateInfo() {
  return {
    updateId: Updates.updateId,
    createdAt: Updates.createdAt,
    channel: Updates.channel,
    runtimeVersion: Updates.runtimeVersion,
  };
}
