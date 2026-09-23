import React, { useState, useEffect } from 'react';
import { StatusBar, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import ThemeContext from './src/theme-context';
import LoadingScreen from './src/components/LoadingScreen';
import LoginScreen from './src/screens/LoginScreen';
import MainNavigator from './src/navigation';
import useAuth from './src/hooks/useAuth';
import {
  registerForPushNotifications,
} from './src/services/notifications';

const Stack = createNativeStackNavigator();

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App crashed:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Algo salió mal</Text>
          <Text style={styles.errorMessage}>{String(this.state.error?.message || this.state.error)}</Text>
          <TouchableOpacity
            style={styles.errorButton}
            onPress={() => this.setState({ hasError: false, error: null })}
          >
            <Text style={styles.errorButtonText}>Reintentar</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    padding: 24,
  },
  errorTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  errorButton: {
    backgroundColor: '#6366f1',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 10,
  },
  errorButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});

function AppContent() {
  const { isLoading, isAuthenticated } = useAuth();
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleTheme = () => setIsDarkMode((prev) => !prev);

  const theme = {
    dark: isDarkMode,
    colors: isDarkMode
      ? {
          background: '#111827',
          surface: '#1f2937',
          surfaceVariant: '#374151',
          primary: '#818cf8',
          primaryLight: '#312e81',
          onPrimary: '#111827',
          accent: '#fbbf24',
          text: '#f9fafb',
          textSecondary: '#9ca3af',
          textDisabled: '#4b5563',
          border: '#374151',
          error: '#ef4444',
          success: '#22c55e',
          warning: '#f59e0b',
          card: '#1f2937',
          cardBorder: '#374151',
        }
      : {
          background: '#f9fafb',
          surface: '#ffffff',
          surfaceVariant: '#f3f4f6',
          primary: '#6366f1',
          primaryLight: '#e0e7ff',
          onPrimary: '#ffffff',
          accent: '#f59e0b',
          text: '#111827',
          textSecondary: '#6b7280',
          textDisabled: '#d1d5db',
          border: '#e5e7eb',
          error: '#ef4444',
          success: '#22c55e',
          warning: '#f59e0b',
          card: '#ffffff',
          cardBorder: '#e5e7eb',
        },
  };

  useEffect(() => {
    if (isAuthenticated) {
      registerForPushNotifications();
    }
  }, [isAuthenticated]);

  if (isLoading) {
    return <LoadingScreen message="Iniciando..." />;
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isDarkMode }}>
      <SafeAreaProvider>
        <NavigationContainer>
          <StatusBar
            barStyle={isDarkMode ? 'light-content' : 'dark-content'}
            backgroundColor={isDarkMode ? '#111827' : '#ffffff'}
          />
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            {isAuthenticated ? (
              <Stack.Screen name="Main" component={MainNavigator} />
            ) : (
              <Stack.Screen name="Login" component={LoginScreen} />
            )}
          </Stack.Navigator>
        </NavigationContainer>
      </SafeAreaProvider>
    </ThemeContext.Provider>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
