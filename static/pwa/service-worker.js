const CACHE = 'otp-panel-v2';
self.addEventListener('install', function(e) { self.skipWaiting(); });
self.addEventListener('activate', function(e) { e.waitUntil(self.clients.claim()); });

self.addEventListener('push', function(e) {
  let data = { title: 'Dolphin SMS', body: 'پیام جدید دارید' };
  if (e.data) {
    try { data = e.data.json(); } catch(err) { data.body = e.data.text(); }
  }
  const options = {
    body: data.body,
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' }
  };
  e.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', function(e) {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window' }).then(function(clientList) {
      for (let i = 0; i < clientList.length; i++) {
        let client = clientList[i];
        if (client.url === e.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) { return clients.openWindow(e.notification.data.url); }
    })
  );
});
