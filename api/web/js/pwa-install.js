/**
 * Last Mile PWA - Install Prompt, Offline Indicator, Update Notifications
 * Include in all panels: <script src="js/pwa-install.js"></script>
 */
(function() {
  'use strict';

  // ========================================
  // INSTALL PROMPT
  // ========================================
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    showInstallBanner();
  });

  function showInstallBanner() {
    if (localStorage.getItem('lastmile_install_dismissed')) return;
    if (window.matchMedia('(display-mode: standalone)').matches) return;

    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.innerHTML = `
      <div style="position:fixed;bottom:0;left:0;right:0;z-index:10000;background:var(--surface,#1a1a2e);border-top:1px solid var(--border,#2a2a3e);padding:12px 16px;display:flex;align-items:center;gap:12px;box-shadow:0 -4px 20px rgba(0,0,0,0.5);font-family:var(--font-family,system-ui);">
        <div style="flex:1;">
          <div style="font-weight:600;font-size:14px;color:var(--text,#e0e0e0);">📱 Instalar Last Mile</div>
          <div style="font-size:12px;color:var(--text-muted,#888);">Añade a tu pantalla para acceso rápido</div>
        </div>
        <button id="pwa-install-btn" style="background:var(--primary,#6366f1);color:#fff;border:none;border-radius:8px;padding:8px 16px;font-weight:600;cursor:pointer;font-size:13px;">Instalar</button>
        <button id="pwa-install-dismiss" style="background:none;border:none;color:var(--text-muted,#888);cursor:pointer;font-size:18px;padding:4px 8px;">✕</button>
      </div>
    `;
    document.body.appendChild(banner);

    document.getElementById('pwa-install-btn').addEventListener('click', () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(choice => {
          if (choice.outcome === 'accepted') {
            console.log('[PWA] App installed');
          }
          deferredPrompt = null;
          banner.remove();
        });
      }
    });

    document.getElementById('pwa-install-dismiss').addEventListener('click', () => {
      localStorage.setItem('lastmile_install_dismissed', '1');
      banner.remove();
    });
  }

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    const b = document.getElementById('pwa-install-banner');
    if (b) b.remove();
  });

  // ========================================
  // OFFLINE INDICATOR
  // ========================================
  function createOfflineIndicator() {
    const el = document.createElement('div');
    el.id = 'offline-indicator';
    el.style.cssText = 'display:none;position:fixed;top:0;left:0;right:0;z-index:10001;background:#ef4444;color:#fff;text-align:center;padding:6px;font-size:12px;font-weight:600;font-family:var(--font-family,system-ui);';
    el.textContent = '📡 Sin conexión - Modo offline activo';
    document.body.prepend(el);
    return el;
  }

  const offlineEl = createOfflineIndicator();

  function updateOnlineStatus() {
    if (navigator.onLine) {
      offlineEl.style.display = 'none';
      document.body.classList.remove('is-offline');
    } else {
      offlineEl.style.display = 'block';
      document.body.classList.add('is-offline');
    }
  }

  window.addEventListener('online', () => {
    updateOnlineStatus();
    showReconnectingToast();
  });
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();

  function showReconnectingToast() {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:12px;right:12px;z-index:10002;background:#22c55e;color:#fff;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:500;animation:fadeIn 0.3s;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-family:var(--font-family,system-ui);';
    toast.textContent = '✅ Conexión restaurada';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // ========================================
  // SERVICE WORKER REGISTRATION + UPDATE
  // ========================================
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(reg => {
      console.log('[PWA] SW registered, scope:', reg.scope);

      // Check for updates every 60 minutes
      setInterval(() => reg.update(), 3600000);

      // Notify when new version available
      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            showUpdateBanner();
          }
        });
      });

      // Periodic background sync
      if ('periodicSync' in reg) {
        reg.periodicSync.register('refresh-pedidos', {
          minInterval: 300000 // 5 minutes
        }).catch(() => console.log('[PWA] Periodic sync not available'));
      }

      // Background sync
      if ('sync' in reg) {
        console.log('[PWA] Background sync available');
      }

      // Push notifications
      if ('pushManager' in reg) {
        console.log('[PWA] Push notifications available');
        subscribePush(reg);
      }
    }).catch(err => {
      console.warn('[PWA] SW registration failed:', err);
    });

    // Listen for SW messages
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data.type === 'SYNC_COMPLETE') {
        showToast('✅ Datos sincronizados');
      }
      if (event.data.type === 'REFRESH_DATA') {
        window.dispatchEvent(new CustomEvent('pwa-refresh'));
      }
    });
  }

  function subscribePush(reg) {
    reg.pushManager.getSubscription().then(sub => {
      if (sub) return; // Already subscribed
      fetch('/api/vapid-public-key').then(r => r.json()).then(d => {
        if (!d.publicKey) return;
        const vapidKey = urlBase64ToUint8Array(d.publicKey);
        return reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: vapidKey
        }).then(subscription => {
          const user = localStorage.getItem('user') || '';
          const empId = localStorage.getItem('empId') || '1';
          if (!user) return;
          return fetch('/api/push/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Emp-Id': empId },
            body: JSON.stringify({ user_id: user, subscription, emp_id: parseInt(empId) })
          }).then(() => console.log('[PWA] Push subscribed'));
        });
      }).catch(() => {});
    });
  }

  // ========================================
  // UPDATE BANNER
  // ========================================
  function showUpdateBanner() {
    const banner = document.createElement('div');
    banner.style.cssText = 'position:fixed;bottom:60px;left:8px;right:8px;z-index:10000;background:var(--surface,#1a1a2e);border:1px solid var(--primary,#6366f1);border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:12px;box-shadow:0 8px 30px rgba(99,102,241,0.3);font-family:var(--font-family,system-ui);';
    banner.innerHTML = `
      <div style="flex:1;">
        <div style="font-weight:600;font-size:14px;color:var(--text,#e0e0e0);">🔄 Actualización disponible</div>
        <div style="font-size:12px;color:var(--text-muted,#888);">Nueva versión de Last Mile</div>
      </div>
      <button id="pwa-update-btn" style="background:var(--primary,#6366f1);color:#fff;border:none;border-radius:8px;padding:8px 14px;font-weight:600;cursor:pointer;font-size:13px;">Actualizar</button>
      <button id="pwa-update-dismiss" style="background:none;border:none;color:var(--text-muted,#888);cursor:pointer;font-size:18px;">✕</button>
    `;
    document.body.appendChild(banner);

    document.getElementById('pwa-update-btn').addEventListener('click', () => {
      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
      }
      window.location.reload();
    });

    document.getElementById('pwa-update-dismiss').addEventListener('click', () => {
      banner.remove();
    });
  }

  // ========================================
  // OFFLINE DATA QUEUE
  // ========================================
  window.PWAQueue = {
    addPendingDelivery: function(data) {
      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'ADD_PENDING_DELIVERY',
          delivery: {
            url: '/api/entregas/' + data.entId,
            token: 'Bearer ' + (LMAuth.getToken ? LMAuth.getToken() : ''),
            data: data
          }
        });
      }
    },
    addPendingLocation: function(data) {
      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'ADD_PENDING_LOCATION',
          location: {
            url: '/api/tracking',
            token: 'Bearer ' + (LMAuth.getToken ? LMAuth.getToken() : ''),
            data: data
          }
        });
      }
    },
    getPendingCount: function() {
      return new Promise(resolve => {
        if (!navigator.serviceWorker.controller) { resolve(0); return; }
        const channel = new MessageChannel();
        channel.port1.onmessage = e => resolve(e.data.count || 0);
        navigator.serviceWorker.controller.postMessage({ type: 'GET_PENDING_COUNT' }, [channel.port2]);
      });
    }
  };

  // ========================================
  // HELPERS
  // ========================================
  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  function showToast(msg) {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:12px;right:12px;z-index:10002;background:var(--surface,#1a1a2e);color:var(--text,#e0e0e0);padding:10px 16px;border-radius:8px;font-size:13px;border:1px solid var(--border,#2a2a3e);animation:fadeIn 0.3s;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-family:var(--font-family,system-ui);';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

})();
