import React, { useCallback, useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SplashScreen from 'expo-splash-screen';
import { colors } from './src/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { I18nProvider } from './src/i18n';
import { checkAndApplyUpdate } from './src/services/updates';
import ErrorBoundary from './src/ErrorBoundary';
import LoginScreen from './src/screens/LoginScreen';
import RootNavigator from './src/navigation';

// Mantiene la splash nativa (logo LM sobre fondo oscuro) visible mientras se
// revisa si hay una actualizacion OTA y se resuelve la sesion guardada, en
// vez de mostrar un loader generico encima -- se ve como una sola carga
// continua en vez de dos pantallas distintas parpadeando.
// Envuelto en try/catch: si el modulo nativo fallara al arrancar, esto NO
// debe poder tumbar la carga de toda la app (una pantalla en blanco
// permanente es peor que quedarse con la splash por defecto del SO).
try {
  SplashScreen.preventAutoHideAsync();
} catch (e) {
  console.warn('[splash] preventAutoHideAsync fallo:', e?.message);
}

function safeHideSplash() {
  try {
    SplashScreen.hideAsync().catch(() => {});
  } catch (e) {
    // no-op: si esto falla la app sigue funcionando igual, solo queda la
    // splash nativa un instante de mas.
  }
}

function Root() {
  const { loading, user } = useAuth();
  const onLayout = useCallback(() => {
    if (!loading) safeHideSplash();
  }, [loading]);

  if (loading) {
    return <View style={{ flex: 1, backgroundColor: colors.bgPrimary }} />;
  }

  return (
    <View style={{ flex: 1 }} onLayout={onLayout}>
      {user ? <RootNavigator /> : <LoginScreen />}
    </View>
  );
}

function AppInner() {
  const [checkingUpdate, setCheckingUpdate] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Si hay actualizacion, checkAndApplyUpdate() reinicia la app sola y
      // este componente nunca vuelve a renderizar. Si no hay (o algo sale
      // mal), checkAndApplyUpdate() ya atrapa sus propios errores y con
      // timeout, asi que esto siempre resuelve.
      try {
        await checkAndApplyUpdate();
      } catch (e) {
        console.warn('[startup] checkAndApplyUpdate fallo:', e?.message);
      }
      if (!cancelled) setCheckingUpdate(false);
    })();
    return () => { cancelled = true; };
  }, []);

  if (checkingUpdate) {
    return <View style={{ flex: 1, backgroundColor: colors.bgPrimary }} />;
  }

  return (
    <SafeAreaProvider>
      <I18nProvider>
        <AuthProvider>
          <Root />
        </AuthProvider>
      </I18nProvider>
    </SafeAreaProvider>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppInner />
    </ErrorBoundary>
  );
}
