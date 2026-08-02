const CACHE_NAME = 'lastmile-v2';
const urlsToCache = [
  'panel-chofer.html',
  'css/design-system.css',
  'js/auth.js',
  'js/theme.js',
  'js/i18n.js',
  'i18n/es.json',
  'i18n/en.json',
  'i18n/pt.json',
  'manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      });
    }).catch(() => {
      if (event.request.destination === 'document') {
        const url = new URL(event.request.url);
        const fallbackPath = url.pathname.split('/').pop() || 'panel-chofer.html';
        return caches.match(fallbackPath).catch(() => caches.match('panel-chofer.html'));
      }
    })
  );
});

self.addEventListener('sync', event => {
  if (event.tag === 'sync-entregas') {
    event.waitUntil(syncPendingDeliveries());
  }
});

async function syncPendingDeliveries() {
  const db = await openDB();
  const tx = db.transaction('pending_deliveries', 'readonly');
  const store = tx.objectStore('pending_deliveries');
  const all = await getAllFromStore(store);
  for (const delivery of all) {
    try {
      const resp = await fetch(delivery.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': delivery.token },
        body: JSON.stringify(delivery.data)
      });
      if (resp.ok) {
        const delTx = db.transaction('pending_deliveries', 'readwrite');
        delTx.objectStore('pending_deliveries').delete(delivery.id);
      }
    } catch (e) {
      console.warn('[SW] Sync failed for', delivery.id, e);
    }
  }
  const clients = await self.clients.matchAll();
  clients.forEach(c => c.postMessage({ type: 'SYNC_COMPLETE' }));
}

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('lastmile_offline', 1);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('pending_deliveries')) {
        db.createObjectStore('pending_deliveries', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('cached_orders')) {
        db.createObjectStore('cached_orders', { keyPath: 'PED_ID' });
      }
    };
    req.onsuccess = e => resolve(e.target.result);
    req.onerror = e => reject(e.target.error);
  });
}

function getAllFromStore(store) {
  return new Promise((resolve, reject) => {
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const lang = data.lang || 'es';
  const titles = {
    es: { assignment: 'Nueva asignacion', delivery: 'Entrega completada', cancelled: 'Pedido cancelado' },
    en: { assignment: 'New assignment', delivery: 'Delivery completed', cancelled: 'Order cancelled' },
    pt: { assignment: 'Nova atribuicao', delivery: 'Entrega concluida', cancelled: 'Pedido cancelado' }
  };
  const bodies = {
    es: { assignment: 'Tienes un nuevo paquete para entregar', delivery: 'La entrega se registro exitosamente', cancelled: 'El pedido fue cancelado' },
    en: { assignment: 'You have a new package to deliver', delivery: 'Delivery was registered successfully', cancelled: 'The order has been cancelled' },
    pt: { assignment: 'Voce tem um novo pacote para entregar', delivery: 'A entrega foi registrada com sucesso', cancelled: 'O pedido foi cancelado' }
  };
  const type = data.type || 'assignment';
  const title = (titles[lang] || titles.es)[type] || data.title || titles.es.assignment;
  const body = (bodies[lang] || bodies.es)[type] || data.body || bodies.es.assignment;

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/img/icon-192.png',
      badge: '/img/icon-192.png',
      vibrate: [200, 100, 200],
      data: data.url || '/panel-chofer.html',
      tag: data.tag || 'default',
      renotify: true,
      actions: type === 'assignment' ? [
        { action: 'view', title: lang === 'pt' ? 'Ver' : lang === 'en' ? 'View' : 'Ver' }
      ] : []
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data || '/panel-chofer.html';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url.includes('panel-chofer') && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'CACHE_ORDER') {
    openDB().then(db => {
      const tx = db.transaction('cached_orders', 'readwrite');
      tx.objectStore('cached_orders').put(event.data.order);
    });
  }
  if (event.data && event.data.type === 'ADD_PENDING_DELIVERY') {
    openDB().then(db => {
      const tx = db.transaction('pending_deliveries', 'readwrite');
      tx.objectStore('pending_deliveries').add(event.data.delivery);
      if ('sync' in self.registration) {
        self.registration.sync.register('sync-entregas');
      }
    });
  }
  if (event.data && event.data.type === 'GET_CACHED_ORDERS') {
    openDB().then(db => {
      const tx = db.transaction('cached_orders', 'readonly');
      getAllFromStore(tx.objectStore('cached_orders')).then(orders => {
        event.source.postMessage({ type: 'CACHED_ORDERS', orders });
      });
    });
  }
});
