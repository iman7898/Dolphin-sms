self.addEventListener('install', function(e) {
    self.skipWaiting(); // مجبور کردن مرورگر به فعالسازی سریع
});

self.addEventListener('activate', function(e) {
    e.waitUntil(self.clients.claim());
});

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
