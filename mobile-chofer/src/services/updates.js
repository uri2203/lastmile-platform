import * as Updates from 'expo-updates';

// El CHECK contra el CDN de Expo es rapido -- si la red esta muerta, no
// queremos colgar el arranque mas de esto. La DESCARGA en cambio puede tardar
// mas (los assets de fuentes pesan >1.5MB) y NO se le pone un timeout corto:
// abortarla a los 8s era justo lo que hacia que la actualizacion no se
// aplicara al primer arranque y quedara pendiente para el segundo.
const CHECK_TIMEOUT_MS = 8000;
const FETCH_TIMEOUT_MS = 60000;

function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)),
  ]);
}

// Revisa si hay una actualizacion de JS publicada (via `eas update`), la
// descarga completa y reinicia la app para aplicarla EN ESTE arranque -- asi
// el chofer siempre ve la ultima version sin tener que reinstalar el APK ni
// arrancar dos veces. El APK solo hace falta reinstalarlo cuando cambia
// codigo nativo (nueva libreria, permisos), no para cambios de JS.
export async function checkAndApplyUpdate() {
  if (!Updates.isEnabled || __DEV__) return false;
  try {
    const result = await withTimeout(Updates.checkForUpdateAsync(), CHECK_TIMEOUT_MS);
    if (!result.isAvailable) return false;
    // Timeout largo en la descarga: si se corta a la mitad se cae al catch y
    // la app sigue con la version actual, pero cuando hay red decente termina
    // y reloadAsync aplica la nueva version sin necesidad de un segundo arranque.
    await withTimeout(Updates.fetchUpdateAsync(), FETCH_TIMEOUT_MS);
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
