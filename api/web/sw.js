/**
 * Last Mile Chofer PWA - Service Worker
 * Permite funcionar offline y cachear datos
 */

const CACHE_NAME = 'lastmile-v1';
const urlsToCache = [
  '/panel-chofer.html',
  '/css/style.css',
  '/js/app.js',
  '/manifest.json'
];

// Install - cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

// Activate - clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch - network first, fallback to cache
self.addEventListener('fetch', event => {
  // API calls always go to network
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache successful API responses for offline
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => {
          // Return cached API data if offline
          return caches.match(event.request);
        })
    );
    return;
  }

  // Static assets: network first, then cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Background sync for pending deliveries
self.addEventListener('sync', event => {
  if (event.tag === 'sync-entregas') {
    event.waitUntil(syncPendingDeliveries());
  }
});

async function syncPendingDeliveries() {
  // Get pending from IndexedDB and sync when online
  console.log('Syncing pending deliveries...');
}

// Push notifications for new assignments
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Nueva asignación';
  const body = data.body || 'Tienes un nuevo paquete para entregar';
  
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/img/icon-192.png',
      badge: '/img/icon-192.png',
      vibrate: [200, 100, 200],
      data: data.url || '/panel-chofer.html',
      actions: [
        { action: 'entregar', title: 'Entregar' },
        { action: 'fallido', title: 'Fallido' }
      ]
    })
  );
});

// Notification click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data || '/panel-chofer.html')
  );
});
