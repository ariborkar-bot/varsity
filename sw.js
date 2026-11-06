/* Varsity service worker: lets the app open from the home screen, and offline.
   The page is always fetched fresh when there is a connection, so updates show up right away;
   the saved copy is only used offline. League data from Supabase is never cached. */
const CACHE = 'varsity-v229';
const SHELL = ['./', 'manifest.webmanifest', 'logo.png', 'logos.js', 'games.js', 'fonts.css', 'icons/icon-192-v2.png', 'icons/icon-512-v2.png', 'icons/apple-touch-icon-v2.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET') return;
  const same = url.origin === self.location.origin, lib = url.hostname === 'cdn.jsdelivr.net';
  if (!same && !lib) return;
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
    if (r.ok || r.type === 'opaque') { const copy = r.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return r;
  })));
});
