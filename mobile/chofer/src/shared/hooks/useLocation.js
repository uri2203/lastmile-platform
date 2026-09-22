/**
 * @module hooks/useLocation
 * @description Location hook using expo-location for foreground and background tracking.
 * Reports location to the API at configurable intervals.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { post } from '../api';

const BACKGROUND_TASK_NAME = 'LASTMILE_LOCATION_TASK';
const REPORT_INTERVAL_MS = 30000;

/**
 * Defines the background location task.
 * Must be defined at module scope, outside the hook.
 */
TaskManager.defineTask(BACKGROUND_TASK_NAME, async ({ data, error }) => {
  if (error) {
    console.error('Background location task error:', error);
    return;
  }
  if (data?.locations?.length > 0) {
    const location = data.locations[0];
    try {
      await post('/api/location/report', {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        accuracy: location.coords.accuracy,
        timestamp: new Date(location.timestamp).toISOString(),
      });
    } catch (err) {
      console.error('Failed to report background location:', err);
    }
  }
});

/**
 * Location hook.
 * @returns {{
 *   location: { latitude: number, longitude: number } | null,
 *   errorMsg: string | null,
 *   isTracking: boolean,
 *   startTracking: () => Promise<void>,
 *   stopTracking: () => Promise<void>
 * }}
 */
export default function useLocation() {
  const [location, setLocation] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const intervalRef = useRef(null);
  const subscriptionRef = useRef(null);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  /**
   * Cleans up intervals and subscriptions.
   */
  function cleanup() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (subscriptionRef.current) {
      subscriptionRef.current.remove();
      subscriptionRef.current = null;
    }
  }

  /**
   * Reports current location to the API.
   * @param {Location.LocationObject} loc - Location object.
   */
  async function reportLocation(loc) {
    try {
      await post('/api/location/report', {
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
        accuracy: loc.coords.accuracy,
        timestamp: new Date(loc.timestamp).toISOString(),
      });
    } catch (err) {
      console.error('Failed to report location:', err);
    }
  }

  /**
   * Requests permissions and starts foreground + background location tracking.
   */
  const startTracking = useCallback(async () => {
    try {
      setErrorMsg(null);

      const { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();
      if (foregroundStatus !== 'granted') {
        setErrorMsg('Se requiere permiso de ubicación para rastreo.');
        return;
      }

      const { status: backgroundStatus } = await Location.requestBackgroundPermissionsAsync();
      if (backgroundStatus !== 'granted') {
        console.warn('Background location permission denied. Using foreground only.');
      }

      // Get initial position
      const initialLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      setLocation({
        latitude: initialLocation.coords.latitude,
        longitude: initialLocation.coords.longitude,
      });
      await reportLocation(initialLocation);

      // Start foreground watcher
      subscriptionRef.current = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.High,
          distanceInterval: 50,
          timeInterval: 10000,
        },
        async (loc) => {
          setLocation({
            latitude: loc.coords.latitude,
            longitude: loc.coords.longitude,
          });
        }
      );

      // Start background task if permissions granted
      if (backgroundStatus === 'granted') {
        const isTaskRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_TASK_NAME);
        if (!isTaskRegistered) {
          await Location.startLocationUpdatesAsync(BACKGROUND_TASK_NAME, {
            accuracy: Location.Accuracy.Balanced,
            distanceInterval: 100,
            deferredUpdatesInterval: REPORT_INTERVAL_MS,
            showsBackgroundLocationIndicator: true,
            foregroundService: {
              notificationTitle: 'Last Mile Delivery',
              notificationBody: 'Rastreando ubicación para entrega',
              notificationColor: '#6366f1',
            },
          });
        }
      }

      // Report to API every 30 seconds
      intervalRef.current = setInterval(async () => {
        try {
          const currentLoc = await Location.getCurrentPositionAsync({
            accuracy: Location.Accuracy.High,
          });
          setLocation({
            latitude: currentLoc.coords.latitude,
            longitude: currentLoc.coords.longitude,
          });
          await reportLocation(currentLoc);
        } catch (err) {
          console.error('Periodic location report failed:', err);
        }
      }, REPORT_INTERVAL_MS);

      setIsTracking(true);
    } catch (error) {
      setErrorMsg(error.message || 'Error al iniciar rastreo de ubicación');
      console.error('startTracking error:', error);
    }
  }, []);

  /**
   * Stops all location tracking.
   */
  const stopTracking = useCallback(async () => {
    try {
      cleanup();

      if (subscriptionRef.current) {
        subscriptionRef.current.remove();
        subscriptionRef.current = null;
      }

      const isTaskRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_TASK_NAME);
      if (isTaskRegistered) {
        await Location.stopLocationUpdatesAsync(BACKGROUND_TASK_NAME);
      }

      setIsTracking(false);
    } catch (error) {
      console.error('stopTracking error:', error);
    }
  }, []);

  return {
    location,
    errorMsg,
    isTracking,
    startTracking,
    stopTracking,
  };
}
