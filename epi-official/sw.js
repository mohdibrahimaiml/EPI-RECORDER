// EPI Verifier service worker — enables fully offline .epi verification at /verify/.
// All precached dependencies are locally vendored; no third-party CDN required.
const CACHE_NAME = 'epi-verifier-v9';
const ASSETS = [
    './',
    './verify/',
    './verify/index.html',
    './cases/',
    './manifest.json',
    './js/epi-verify-core.js?v=37',
    './js/jszip.min.js?v=32',
    './css/meridian.css?v=2',
    './assets/logo.svg'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            // addAll fails atomically if ANY asset 404s — cache individually
            // so one stale path can't break the whole install.
            return Promise.allSettled(
                ASSETS.map((url) => cache.add(new Request(url, { cache: 'reload' })))
            );
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    // Never intercept API calls or cross-origin requests.
    const url = new URL(event.request.url);
    if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;

    const accept = event.request.headers.get('accept') || '';
    // Network-first for HTML: always fresh layout when online, cached offline fallback.
    if (accept.includes('text/html')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
    } else {
        // Cache-first for static assets.
        event.respondWith(
            caches.match(event.request).then((cachedResponse) => {
                return cachedResponse || fetch(event.request).then((response) => {
                    if (response.ok && url.origin === self.location.origin) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    }
                    return response;
                });
            })
        );
    }
});
