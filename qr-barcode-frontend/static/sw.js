console.log('Service Worker Scope:', self.registration.scope);

const CACHE_NAME = 'qr-barcode-cache-v4';
const DEBUG = true; // Enable logging

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

// Install event - Cache all required resources
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  // Force waiting service worker to become active
  event.waitUntil(
    Promise.all([
      self.skipWaiting(), // Force activation
      caches.open(CACHE_NAME).then(cache => {
        console.log('Caching resources...');
        return cache.addAll(urlsToCache).then(() => {
          console.log('Resources cached successfully');
        });
      })
    ])
  );
});

// Activate event - Clean up old caches and take control
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      clients.claim(), // Take control of all pages immediately
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
    ])
  );
});

// Fetch event - Serve from cache first, then network
self.addEventListener('fetch', event => {
  log('Fetch event for:', event.request.url);
  
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          log('Found in cache:', event.request.url);
          return cachedResponse;
        }
        
        log('Not in cache, fetching:', event.request.url);
        return fetch(event.request)
          .then(response => {
            // Check if valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              log('Invalid response, not caching:', event.request.url);
              return response;
            }
            
            // Clone and cache
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                log('Caching new resource:', event.request.url);
                cache.put(event.request, responseToCache);
              });
              
            return response;
          })
          .catch(error => {
            log('Fetch failed:', error);
            // Handle offline scenario
            if (event.request.mode === 'navigate') {
              return caches.match('/offline.html');
            }
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