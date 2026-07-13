/**
 * Last Mile - Core App Module
 * Placeholder for shared app functionality
 */

const App = {
  init() {
    console.log('[App] Initialized');
  }
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => App.init());
} else {
  App.init();
}
