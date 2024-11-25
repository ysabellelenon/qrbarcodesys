console.log('Service Worker Scope:', self.registration.scope);

const CACHE_NAME = 'qr-barcode-cache-v4';
const DEBUG = true;

function log(...args) {
    if (DEBUG) {
        console.log('[ServiceWorker]', ...args);
    }
}

const urlsToCache = [
    '/',
    '/login',
    '/static/css/styles.css',
    '/static/manifest.json',
    '/static/img/jae-logo.jpg',
    '/static/fonts/Poppins-Regular.ttf',
    '/static/fonts/Poppins-SemiBold.ttf',
    '/static/icons/icon-48x48.png',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Pre-cache resources during installation
self.addEventListener('install', event => {
    log('Installing Service Worker...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                log('Pre-caching resources...');
                return cache.addAll(urlsToCache)
                    .then(() => self.skipWaiting())
                    .catch(error => {
                        log('Pre-cache failed:', error);
                        throw error;
                    });
            })
    );
});

// Clean up old caches
self.addEventListener('activate', event => {
    log('Activating Service Worker...');
    
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName.startsWith('qr-barcode-cache-') && cacheName !== CACHE_NAME) {
                            log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
        ])
    );
});

// Network first, falling back to cache strategy
self.addEventListener('fetch', event => {
    log('Fetch event for:', event.request.url);
    
    event.respondWith(
        fetch(event.request.clone())
            .then(response => {
                // Check if we received a valid response
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }

                // Clone the response
                const responseToCache = response.clone();

                // Cache the response for future use
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(event.request, responseToCache);
                        log('Updated cache for:', event.request.url);
                    });

                return response;
            })
            .catch(err => {
                log('Fetch failed, falling back to cache:', err);
                return caches.match(event.request)
                    .then(cachedResponse => {
                        if (cachedResponse) {
                            log('Serving from cache:', event.request.url);
                            return cachedResponse;
                        }

                        // If the request is for a page, return the offline page
                        if (event.request.mode === 'navigate') {
                            return caches.match('/offline.html');
                        }

                        // Return a simple offline response for other resources
                        return new Response('Offline content not available');
                    });
            })
    );
});

// Handle messages from clients
self.addEventListener('message', event => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
}); 