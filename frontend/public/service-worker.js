/* eslint-disable no-restricted-globals */

// Import Workbox from CDN
importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');

// Check if Workbox loaded successfully
if (workbox) {
    console.log('Workbox loaded successfully');

    // Skip waiting and claim clients immediately
    workbox.core.skipWaiting();
    workbox.core.clientsClaim();

    // ===== APP SHELL CACHING =====
    // Precache the app shell (index.html) - use cache-first with network fallback
    workbox.routing.registerRoute(
        ({ request }) => request.mode === 'navigate',
        new workbox.strategies.NetworkFirst({
            cacheName: 'pages-cache',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
            ],
        })
    );

    // ===== STATIC ASSETS (CSS, JS, Workers) =====
    // Cache static resources with StaleWhileRevalidate
    workbox.routing.registerRoute(
        ({ request }) =>
            request.destination === 'style' ||
            request.destination === 'script' ||
            request.destination === 'worker',
        new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'static-resources',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
            ],
        })
    );

    // ===== IMAGES =====
    // Cache images with Cache First strategy
    workbox.routing.registerRoute(
        ({ request }) => request.destination === 'image',
        new workbox.strategies.CacheFirst({
            cacheName: 'images-cache',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 60,
                    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
                }),
            ],
        })
    );

    // ===== GOOGLE FONTS =====
    // Cache font stylesheets with StaleWhileRevalidate
    workbox.routing.registerRoute(
        ({ url }) => url.origin === 'https://fonts.googleapis.com',
        new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'google-fonts-stylesheets',
        })
    );

    // Cache font files with Cache First (long-lived)
    workbox.routing.registerRoute(
        ({ url }) => url.origin === 'https://fonts.gstatic.com',
        new workbox.strategies.CacheFirst({
            cacheName: 'google-fonts-webfonts',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 30,
                    maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
                }),
            ],
        })
    );

    // ===== API REQUESTS =====
    // Cache API calls with Network First (fresh data preferred, fallback to cache)
    workbox.routing.registerRoute(
        ({ url }) => url.pathname.startsWith('/api/'),
        new workbox.strategies.NetworkFirst({
            cacheName: 'api-cache',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200],
                }),
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 50,
                    maxAgeSeconds: 5 * 60, // 5 minutes
                }),
            ],
        })
    );

    // ===== ICONS & MANIFEST =====
    // Cache manifest and icons
    workbox.routing.registerRoute(
        ({ url }) =>
            url.pathname.includes('/manifest.json') ||
            url.pathname.includes('/icons/'),
        new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'manifest-icons-cache',
        })
    );

} else {
    console.log('Workbox failed to load');
}

// Listen for skip waiting message
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
