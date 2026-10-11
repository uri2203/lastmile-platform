/**
 * @module shared/session
 * @description Tiny session event bus. Lets low-level modules (api.js) notify the
 * auth layer (useAuth) that the stored tokens were invalidated, so every screen
 * reacts immediately without an app restart.
 */

const listeners = new Set();

export function onSessionExpired(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function emitSessionExpired() {
  listeners.forEach((listener) => {
    try {
      listener();
    } catch (error) {
      console.error('session expired listener error:', error);
    }
  });
}

export default { onSessionExpired, emitSessionExpired };
