import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { colors } from './src/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { I18nProvider } from './src/i18n';
import { checkAndApplyUpdate } from './src/services/updates';
import LoginScreen from './src/screens/LoginScreen';
import RootNavigator from './src/navigation';

function Root() {
  const { loading, user } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bgPrimary, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return user ? <RootNavigator /> : <LoginScreen />;
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
    return (
      <SafeAreaProvider>
        <View style={{ flex: 1, backgroundColor: colors.bgPrimary, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={colors.accent} size="large" />
          <Text style={{ color: colors.textMuted, marginTop: 12, fontSize: 13 }}>Buscando actualizaciones...</Text>
        </View>
      </SafeAreaProvider>
    );
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
