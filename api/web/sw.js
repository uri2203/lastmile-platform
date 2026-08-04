const CACHE_NAME = 'lastmile-v3';
const CACHE_API = 'lastmile-api-v1';
const urlsToCache = [
  '/',
  '/panel-chofer.html',
  '/panel-admin.html',
  '/panel-operacion.html',
  '/panel-cliente.html',
  '/css/design-system.css',
  '/js/auth.js',
  '/js/theme.js',
  '/js/i18n.js',
  '/js/pwa-install.js',
  '/i18n/es.json',
  '/i18n/en.json',
  '/i18n/pt.json',
  '/i18n/fr.json',
  '/i18n/de.json',
  '/i18n/zh.json',
  '/i18n/ja.json',
  '/i18n/ko.json',
  '/i18n/ar.json',
  '/i18n/hi.json',
  '/i18n/it.json',
  '/i18n/nl.json',
  '/manifest.json'
];

// ========================================
// INSTALL
// ========================================
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// ========================================
// ACTIVATE - clean old caches
// ========================================
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== CACHE_API).map(k => {
          console.log('[SW] Deleting old cache:', k);
          return caches.delete(k);
        })
      )
    ).then(() => self.clients.claim())
  );
});

// ========================================
// FETCH - Network-first for API, Cache-first for assets
// ========================================
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip non-GET and chrome-extension
  if (event.request.method !== 'GET' || url.protocol === 'chrome-extension:') return;

  // API requests: network-first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    // Don't cache auth/login/push endpoints
    if (url.pathname.includes('/auth/') || url.pathname.includes('/push/') || url.pathname.includes('/whatsapp/')) {
      return;
    }
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_API).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response.ok && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    }).catch(() => {
      // Offline fallback for HTML pages
      if (event.request.destination === 'document') {
        return caches.match('/panel-chofer.html');
      }
    })
  );
});

// ========================================
// BACKGROUND SYNC - sync pending deliveries
// ========================================
self.addEventListener('sync', event => {
  if (event.tag === 'sync-entregas') {
    event.waitUntil(syncPendingDeliveries());
  }
  if (event.tag === 'sync-location') {
    event.waitUntil(syncPendingLocations());
  }
});

// ========================================
// PERIODIC BACKGROUND SYNC - refresh data
// ========================================
self.addEventListener('periodicsync', event => {
  if (event.tag === 'refresh-pedidos') {
    event.waitUntil(refreshPedidos());
  }
});

async function refreshPedidos() {
  try {
    const clients = await self.clients.matchAll();
    clients.forEach(c => c.postMessage({ type: 'REFRESH_DATA' }));
  } catch (e) {
    console.warn('[SW] Periodic sync failed:', e);
  }
}

// ========================================
// PUSH NOTIFICATIONS - multi-language
// ========================================
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const lang = data.lang || 'es';

  const titles = {
    es: { assignment: 'Nueva asignación', delivery: 'Entrega completada', cancelled: 'Pedido cancelado', payment: 'Pago recibido', route: 'Nueva ruta optimizada' },
    en: { assignment: 'New assignment', delivery: 'Delivery completed', cancelled: 'Order cancelled', payment: 'Payment received', route: 'New optimized route' },
    pt: { assignment: 'Nova atribuição', delivery: 'Entrega concluída', cancelled: 'Pedido cancelado', payment: 'Pagamento recebido', route: 'Nova rota otimizada' },
    fr: { assignment: 'Nouvelle attribution', delivery: 'Livraison terminée', cancelled: 'Commande annulée', payment: 'Paiement reçu', route: 'Nouvelle route optimisée' },
    de: { assignment: 'Neue Zuweisung', delivery: 'Lieferung abgeschlossen', cancelled: 'Bestellung storniert', payment: 'Zahlung erhalten', route: 'Neue optimierte Route' },
    zh: { assignment: '新分配', delivery: '配送完成', cancelled: '订单取消', payment: '收到付款', route: '新优化路线' },
    ja: { assignment: '新しい割り当て', delivery: '配達完了', cancelled: '注文キャンセル', payment: '支払い受信', route: '新しい最適化ルート' },
    ko: { assignment: '새 할당', delivery: '배송 완료', cancelled: '주문 취소', payment: '결제 수신', route: '새 최적화 경로' },
    ar: { assignment: 'تعيين جديد', delivery: 'اكتملت التوصيل', cancelled: 'تم إلغاء الطلب', payment: 'تم استلام الدفع', route: 'مسار محسّن جديد' },
    hi: { assignment: 'नई सौंपी गई', delivery: 'डिलीवरी पूर्ण', cancelled: 'ऑर्डर रद्द', payment: 'भुगतान प्राप्त', route: 'नया अनुकूलित मार्ग' },
    it: { assignment: 'Nuova assegnazione', delivery: 'Consegna completata', cancelled: 'Ordine annullato', payment: 'Pagamento ricevuto', route: 'Nuovo percorso ottimizzato' },
    nl: { assignment: 'Nieuwe toewijzing', delivery: 'Levering voltooid', cancelled: 'Bestelling geannuleerd', payment: 'Betaling ontvangen', route: 'Nieuwe geoptimaliseerde route' }
  };

  const bodies = {
    es: { assignment: 'Tienes un nuevo paquete para entregar', delivery: 'La entrega se registró exitosamente', cancelled: 'El pedido fue cancelado', payment: 'Se recibió el pago del pedido', route: 'Se calculó una ruta más eficiente' },
    en: { assignment: 'You have a new package to deliver', delivery: 'Delivery was registered successfully', cancelled: 'The order has been cancelled', payment: 'Payment for the order was received', route: 'A more efficient route has been calculated' },
    pt: { assignment: 'Você tem um novo pacote para entregar', delivery: 'A entrega foi registrada com sucesso', cancelled: 'O pedido foi cancelado', payment: 'O pagamento foi recebido', route: 'Uma rota mais eficiente foi calculada' },
    fr: { assignment: 'Vous avez un nouveau colis à livrer', delivery: 'La livraison a été enregistrée', cancelled: 'La commande a été annulée', payment: 'Le paiement a été reçu', route: 'Un itinéraire plus efficace a été calculé' },
    de: { assignment: 'Sie haben ein neues Paket zu liefern', delivery: 'Die Lieferung wurde erfolgreich registriert', cancelled: 'Die Bestellung wurde storniert', payment: 'Die Zahlung wurde erhalten', route: 'Eine effizientere Route wurde berechnet' },
    zh: { assignment: '您有一个新包裹要配送', delivery: '配送已成功登记', cancelled: '订单已取消', payment: '已收到订单付款', route: '已计算出更高效的路线' },
    ja: { assignment: '新しい荷物の配達があります', delivery: '配達が正常に記録されました', cancelled: '注文がキャンセルされました', payment: '支払いを受け取りました', route: 'より効率的なルートが計算されました' },
    ko: { assignment: '새 배달 패키지가 있습니다', delivery: '배송이 성공적으로 기록되었습니다', cancelled: '주문이 취소되었습니다', payment: '결제가 수신되었습니다', route: '더 효율적인 경로가 계산되었습니다' },
    ar: { assignment: 'لديك طرد جديد للتوصيل', delivery: 'تم تسجيل التوصيل بنجاح', cancelled: 'تم إلغاء الطلب', payment: 'تم استلام الدفع', route: 'تم حساب مسار أكثر كفاءة' },
    hi: { assignment: 'आपके पास एक नया पैकेज है', delivery: 'डिलीवरी सफलतापूर्वक दर्ज की गई', cancelled: 'ऑर्डर रद्द कर दिया गया', payment: 'भुगतान प्राप्त हो गया', route: 'अधिक कुशल मार्ग की गणना की गई' },
    it: { assignment: 'Hai un nuovo pacco da consegnare', delivery: 'La consegna è stata registrata', cancelled: 'L\'ordine è stato annullato', payment: 'Il pagamento è stato ricevuto', route: 'È stato calcolato un percorso più efficiente' },
    nl: { assignment: 'U heeft een nieuw pakket te bezorgen', delivery: 'De levering is geregistreerd', cancelled: 'De bestelling is geannuleerd', payment: 'De betaling is ontvangen', route: 'Er is een efficiëntere route berekend' }
  };

  const type = data.type || 'assignment';
  const title = (titles[lang] || titles.es)[type] || data.title || 'Last Mile';
  const body = (bodies[lang] || bodies.es)[type] || data.body || '';

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/img/icon-192.svg',
      badge: '/img/icon-192.svg',
      vibrate: [200, 100, 200],
      data: data.url || '/panel-chofer.html',
      tag: data.tag || type,
      renotify: true,
      requireInteraction: type === 'assignment',
      actions: type === 'assignment' ? [
        { action: 'view', title: lang === 'en' ? 'View' : 'Ver' },
        { action: 'dismiss', title: lang === 'en' ? 'Dismiss' : 'Cerrar' }
      ] : []
    })
  );
});

// ========================================
// NOTIFICATION CLICK
// ========================================
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data || '/panel-chofer.html';

  if (event.action === 'dismiss') return;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url.includes('panel-') && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});

// ========================================
// MESSAGE HANDLER
// ========================================
self.addEventListener('message', event => {
  if (!event.data) return;

  switch (event.data.type) {
    case 'CACHE_ORDER':
      openDB().then(db => {
        const tx = db.transaction('cached_orders', 'readwrite');
        tx.objectStore('cached_orders').put(event.data.order);
      });
      break;

    case 'ADD_PENDING_DELIVERY':
      openDB().then(db => {
        const tx = db.transaction('pending_deliveries', 'readwrite');
        tx.objectStore('pending_deliveries').add(event.data.delivery);
        if ('sync' in self.registration) {
          self.registration.sync.register('sync-entregas');
        }
      });
      break;

    case 'ADD_PENDING_LOCATION':
      openDB().then(db => {
        const tx = db.transaction('pending_locations', 'readwrite');
        tx.objectStore('pending_locations').add(event.data.location);
        if ('sync' in self.registration) {
          self.registration.sync.register('sync-location');
        }
      });
      break;

    case 'GET_CACHED_ORDERS':
      openDB().then(db => {
        const tx = db.transaction('cached_orders', 'readonly');
        getAllFromStore(tx.objectStore('cached_orders')).then(orders => {
          event.source.postMessage({ type: 'CACHED_ORDERS', orders });
        });
      });
      break;

    case 'GET_PENDING_COUNT':
      openDB().then(db => {
        const tx = db.transaction('pending_deliveries', 'readonly');
        const req = tx.objectStore('pending_deliveries').count();
        req.onsuccess = () => {
          event.source.postMessage({ type: 'PENDING_COUNT', count: req.result });
        };
      });
      break;

    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
  }
});

// ========================================
// OFFLINE SYNC FUNCTIONS
// ========================================
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
      console.warn('[SW] Sync delivery failed:', delivery.id);
    }
  }
  notifyClients({ type: 'SYNC_COMPLETE' });
}

async function syncPendingLocations() {
  const db = await openDB();
  const tx = db.transaction('pending_locations', 'readonly');
  const store = tx.objectStore('pending_locations');
  const all = await getAllFromStore(store);
  for (const loc of all) {
    try {
      await fetch(loc.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': loc.token },
        body: JSON.stringify(loc.data)
      });
      const delTx = db.transaction('pending_locations', 'readwrite');
      delTx.objectStore('pending_locations').delete(loc.id);
    } catch (e) {
      break;
    }
  }
}

async function notifyClients(msg) {
  const clients = await self.clients.matchAll();
  clients.forEach(c => c.postMessage(msg));
}

// ========================================
// INDEXEDDB HELPERS
// ========================================
function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('lastmile_offline', 2);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('pending_deliveries')) {
        db.createObjectStore('pending_deliveries', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('cached_orders')) {
        db.createObjectStore('cached_orders', { keyPath: 'PED_ID' });
      }
      if (!db.objectStoreNames.contains('pending_locations')) {
        db.createObjectStore('pending_locations', { keyPath: 'id', autoIncrement: true });
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
