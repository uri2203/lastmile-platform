import React, { useCallback, useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SplashScreen from 'expo-splash-screen';
import { colors } from './src/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { I18nProvider } from './src/i18n';
import { checkAndApplyUpdate } from './src/services/updates';
import LoginScreen from './src/screens/LoginScreen';
import RootNavigator from './src/navigation';

// Mantiene la splash nativa (logo LM sobre fondo oscuro) visible mientras se
// revisa si hay una actualizacion OTA y se resuelve la sesion guardada, en
// vez de mostrar un loader generico encima -- se ve como una sola carga
// continua en vez de dos pantallas distintas parpadeando.
SplashScreen.preventAutoHideAsync().catch(() => {});

function Root() {
  const { loading, user } = useAuth();
  const onLayout = useCallback(() => {
    if (!loading) SplashScreen.hideAsync().catch(() => {});
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

export default function App() {
  const [checkingUpdate, setCheckingUpdate] = useState(true);

  useEffect(() => {
    (async () => {
      // Si hay actualizacion, checkAndApplyUpdate() reinicia la app sola y
      // este componente nunca vuelve a renderizar. Si no hay, seguimos.
      await checkAndApplyUpdate();
      setCheckingUpdate(false);
    })();
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
