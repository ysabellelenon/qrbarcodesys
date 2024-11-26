// IndexedDB Configuration
const DB_CONFIG = {
    name: 'QRBarcodeDB',
    version: 1,
    stores: {
        users: { keyPath: 'username' },
        sessions: { keyPath: 'id', autoIncrement: true },
        items: { keyPath: 'id', autoIncrement: true },
        offlineQueue: { keyPath: 'id', autoIncrement: true }
    }
};

// Database Helper Functions
async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_CONFIG.name, DB_CONFIG.version);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create stores based on configuration
            Object.entries(DB_CONFIG.stores).forEach(([storeName, config]) => {
                if (!db.objectStoreNames.contains(storeName)) {
                    db.createObjectStore(storeName, config);
                }
            });
        };
    });
}

// User Data Management
async function getUserFromDB(username) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readonly');
        const store = transaction.objectStore('users');
        const request = store.get(username);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function storeUserData(userData) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readwrite');
        const store = transaction.objectStore('users');
        const request = store.put(userData);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

// Session Management
async function storeSessionData(sessionData) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['sessions'], 'readwrite');
        const store = transaction.objectStore('sessions');
        const request = store.add(sessionData);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

// Offline Helpers
async function hashPassword(password) {
    let hash = 0;
    for (let i = 0; i < password.length; i++) {
        const char = password.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return hash.toString(16);
}

// Offline Status Management
function updateOfflineStatus() {
    const body = document.querySelector('body');
    const messageContainer = document.getElementById('message-container');
    
    if (!navigator.onLine) {
        body.classList.add('offline');
        if (messageContainer) {
            messageContainer.innerHTML = '<p class="notice">Working in offline mode. Limited functionality available.</p>';
        }
    } else {
        body.classList.remove('offline');
        if (messageContainer) {
            messageContainer.innerHTML = '';
        }
    }
}

// PWA Installation
function initPWAInstallPrompt() {
    let deferredPrompt;
    const installModal = document.getElementById('installModal');
    const installButton = document.getElementById('installNow');
    const laterButton = document.getElementById('installLater');

    // Check if elements exist and if app is in standalone mode
    if (!installModal) return; // Exit if modal doesn't exist
    
    if (window.matchMedia('(display-mode: standalone)').matches) {
        installModal.style.display = 'none';
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        if (shouldShowInstallPrompt()) {
            setTimeout(() => {
                if (installModal) {
                    installModal.classList.add('show');
                }
            }, 2000);
        }
    });

    if (installButton) {
        installButton.addEventListener('click', async () => {
            if (deferredPrompt && installModal) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                deferredPrompt = null;
                installModal.classList.remove('show');
                console.log(`User response to the install prompt: ${outcome}`);
            }
        });
    }

    if (laterButton) {
        laterButton.addEventListener('click', () => {
            if (installModal) {
                installModal.classList.remove('show');
                localStorage.setItem('installPromptDismissed', Date.now());
            }
        });
    }
}

function shouldShowInstallPrompt() {
    const dismissedTime = localStorage.getItem('installPromptDismissed');
    if (!dismissedTime) return true;
    const threeDays = 3 * 24 * 60 * 60 * 1000;
    return Date.now() - parseInt(dismissedTime) > threeDays;
}

// Service Worker Registration
async function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            });
            console.log('ServiceWorker registration successful with scope:', registration.scope);
            
            registration.update();
            
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        console.log('New service worker installed');
                    }
                });
            });
        } catch (err) {
            console.error('ServiceWorker registration failed:', err);
        }
    }
}

// Initialize App
async function initApp() {
    try {
        await openDB();
        console.log('IndexedDB initialized successfully');
        
        // Register for periodic cache updates
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then(registration => {
                // Try to update cache every hour
                setInterval(() => {
                    registration.sync.register('update-cache');
                }, 60 * 60 * 1000);
            });
        }
    } catch (err) {
        console.error('IndexedDB initialization failed:', err);
    }
}

initApp(); 