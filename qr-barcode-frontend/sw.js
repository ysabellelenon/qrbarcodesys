console.log('Service Worker Scope:', self.registration.scope);

const CACHE_NAME = 'qr-barcode-cache-v4';
const DEBUG = true;

function log(...args) {
    if (DEBUG) {
        console.log('[ServiceWorker]', ...args);
    }
}

const URLS_TO_CACHE = {
    // Core pages
    pages: [
        '/login',
        '/engineering',
        '/item-masterlist',
        '/register-item',
        '/create-item',
        '/assembly-login',
        '/assembly',
        '/offline.html'
    ],
    
    // Static assets
    assets: [
        '/static/css/bootstrap.min.css',
        '/static/css/styles.css',
        '/static/js/main.js',
        '/static/img/jae-logo.jpg'
    ],
    
    // Fonts
    fonts: [
        '/static/fonts/Poppins-Regular.ttf',
        '/static/fonts/Poppins-SemiBold.ttf'
    ],
    
    // Icons
    icons: [
        '/static/icons/icon-144x144.png',
        '/static/icons/icon-192x192.png'
    ],

    // API endpoints (remove if not needed for initial cache)
    api: []
};

// Add a function to validate URLs before caching
function isValidUrl(url) {
    try {
        return url && url.startsWith('/');
    } catch (e) {
        return false;
    }
}

// Filter valid URLs
const urlsToCache = [
    ...URLS_TO_CACHE.pages,
    ...URLS_TO_CACHE.assets,
    ...URLS_TO_CACHE.fonts,
    ...URLS_TO_CACHE.icons,
    ...URLS_TO_CACHE.api
].filter(isValidUrl);

// Pre-cache resources during installation
self.addEventListener('install', event => {
    log('Installing Service Worker...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                log('Pre-caching resources...');
                // Cache each URL individually to handle failures gracefully
                return Promise.allSettled(
                    urlsToCache.map(url => 
                        cache.add(url)
                            .catch(error => {
                                log(`Failed to cache: ${url}`, error);
                                // Continue with installation even if some resources fail to cache
                                return Promise.resolve();
                            })
                    )
                ).then(() => {
                    log('Pre-cache completed (some resources might have failed)');
                    return self.skipWaiting();
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

// Cache strategies
const CACHE_STRATEGIES = {
    // Network first, fall back to cache
    NETWORK_FIRST: async (request) => {
        try {
            const response = await fetch(request);
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
            return response;
        } catch (error) {
            const cachedResponse = await caches.match(request);
            return cachedResponse || caches.match('/offline.html');
        }
    },

    // Cache first, fall back to network
    CACHE_FIRST: async (request) => {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) return cachedResponse;
        
        try {
            const response = await fetch(request);
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
            return response;
        } catch (error) {
            return new Response('Resource not available offline');
        }
    },

    // Stale while revalidate
    STALE_WHILE_REVALIDATE: async (request) => {
        const cachedResponse = await caches.match(request);
        
        const fetchPromise = fetch(request).then(async (response) => {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
            return response;
        });

        return cachedResponse || fetchPromise;
    }
};

// Updated fetch event handler
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Don't cache POST requests
    if (event.request.method === 'POST') {
        // Special handling for logout
        if (event.request.url.includes('/logout')) {
            event.respondWith(
                fetch(event.request.clone())
                    .catch(err => {
                        log('Logout request failed - requires internet connection');
                        return new Response(JSON.stringify({
                            error: 'Logout requires an internet connection for security purposes.',
                            requiresOnline: true
                        }), {
                            status: 503,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    })
            );
            return;
        }
        
        // Other POST requests handling...
        event.respondWith(
            fetch(event.request.clone())
                .catch(err => {
                    log('POST request failed, falling back to offline handling');
                    return new Response(JSON.stringify({
                        error: 'You are offline. The action will be queued for later.',
                        offline: true
                    }), {
                        headers: { 'Content-Type': 'application/json' }
                    });
                })
        );
        return;
    }

    // Choose caching strategy based on URL pattern
    if (url.pathname.startsWith('/api/')) {
        // API requests: Network first
        event.respondWith(CACHE_STRATEGIES.NETWORK_FIRST(event.request));
    } else if (url.pathname.startsWith('/static/')) {
        // Static assets: Cache first
        event.respondWith(CACHE_STRATEGIES.CACHE_FIRST(event.request));
    } else if (URLS_TO_CACHE.pages.includes(url.pathname)) {
        // HTML pages: Network first
        event.respondWith(CACHE_STRATEGIES.NETWORK_FIRST(event.request));
    } else {
        // Everything else: Stale while revalidate
        event.respondWith(CACHE_STRATEGIES.STALE_WHILE_REVALIDATE(event.request));
    }
});

// Handle messages from clients
self.addEventListener('message', event => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
});

// Add periodic cache update
self.addEventListener('sync', event => {
    if (event.tag === 'update-cache') {
        event.waitUntil(updateCache());
    }
});

async function updateCache() {
    const cache = await caches.open(CACHE_NAME);
    
    // Update static resources
    for (const url of urlsToCache) {
        try {
            const response = await fetch(url);
            await cache.put(url, response);
        } catch (error) {
            console.error(`Failed to update cache for ${url}:`, error);
        }
    }
}

// Add cache version management
self.addEventListener('activate', event => {
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            // Clean up old cache versions
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName.startsWith('qr-barcode-cache-') && cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
        ])
    );
}); 