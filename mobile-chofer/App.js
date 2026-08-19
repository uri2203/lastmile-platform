import React from 'react';
import { View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { colors } from './src/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { I18nProvider } from './src/i18n';
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
