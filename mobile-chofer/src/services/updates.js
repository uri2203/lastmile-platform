import * as Updates from 'expo-updates';

// Revisa si hay una actualizacion de JS publicada (via `eas update`), la
// descarga y reinicia la app para aplicarla. Se llama una vez al arrancar,
// asi el chofer siempre ve la ultima version sin tener que reinstalar el
// APK -- el APK solo hace falta reinstalarlo cuando cambia codigo nativo
// (nueva libreria, permisos nuevos, etc.), no para cambios normales de JS.
export async function checkAndApplyUpdate() {
  // Updates.isEnabled es false en Expo Go y en builds de desarrollo; ahi no
  // hay nada que chequear.
  if (!Updates.isEnabled || __DEV__) return false;
  try {
    const result = await Updates.checkForUpdateAsync();
    if (!result.isAvailable) return false;
    await Updates.fetchUpdateAsync();
    await Updates.reloadAsync();
    return true; // no deberia llegar aca (reloadAsync reinicia la app)
  } catch (e) {
    // Sin conexion, servidor de updates caido, etc: se sigue con la version
    // ya instalada, no se bloquea el uso de la app.
    console.warn('[updates] no se pudo revisar/aplicar actualizacion:', e.message);
    return false;
  }
}
