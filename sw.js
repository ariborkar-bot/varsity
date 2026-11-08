/* Varsity service worker: lets the app open from the home screen, and offline.
   The page is always fetched fresh when there is a connection, so updates show up right away;
   the saved copy is only used offline. League data from Supabase is never cached. */
const CACHE = 'varsity-v335';
const SHELL = ['./', 'vendor/supabase.min.js', 'manifest.webmanifest', 'logo.png', 'logos.js', 'games.js', 'fonts.css', 'icons/icon-192-v2.png', 'icons/icon-512-v2.png', 'icons/apple-touch-icon-v2.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET') return;
  const same = url.origin === self.location.origin;
  if (!same) return;                                            // v314: other sites (CDN backups, Supabase) go straight to the network; an opaque cached copy of the login library could stay broken for good
  if (same && /\.mp4$/.test(url.pathname)) return;                // sponsor video: straight to the network (range requests can't be cached)                                     // Supabase and everything else: straight to the network
  if (req.mode === 'navigate' || (same && /\/(index|basketball)\.html$/.test(url.pathname))) {
    const key = /basketball\.html$/.test(url.pathname) ? req : './';       // football lives at ./ ; basketball keeps its own copy
    e.respondWith(fetch(req, { cache: 'no-cache' }).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(key, copy)); return r; })
      .catch(() => caches.match(key).then(h => h || caches.match('./'))));
    return;
  }
  if (same && url.pathname.endsWith('/games.js')) {            // schedule data: always try the network first so new games show up right away
    e.respondWith(fetch(req, { cache: 'no-cache' }).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(req, copy)); return r; }).catch(() => caches.match(req)));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return r;
  })));
});
// v294: tapping a Varsity notification opens (or focuses) the app. v320: the right sport, and a #link (e.g. #groups) when the alert has one.
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const want = new URL((e.notification.data && e.notification.data.url) || './', self.registration.scope).href;
  const page = u => { const p = u.split('#')[0]; return /basketball\.html$/.test(p) ? 'bb' : 'fb'; };
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    for (const c of cs) if (page(c.url) === page(want) && 'focus' in c) { if (want.includes('#') && 'navigate' in c) c.navigate(want).catch(() => {}); return c.focus(); }
    return self.clients.openWindow ? self.clients.openWindow(want) : null;
  }));
});
// v311/v320: closed-app push. tools/push/send.mjs sends {title, body, url, tag}. Every push must show a notification (iOS withdraws permission for silent ones).
self.addEventListener('push', e => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Varsity', { body: d.body || '', tag: d.tag || 'varsity', icon: 'icons/icon-192-v2.png', badge: 'icons/icon-192-v2.png', data: { url: d.url || './' } }));
});
