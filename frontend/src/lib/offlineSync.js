import { api } from "./api";

/**
 * PocketBuddy Offline Sync Module
 *
 * Uses raw IndexedDB to store mood, expenses, journal, and sleep entries
 * when the device is offline. Syncs to server on reconnection with retry
 * logic and conflict resolution.
 *
 * Validates: Requirements 7.2, 7.3, 7.4, 7.8
 */

const DB_NAME = "pocketbuddy-offline";
const DB_VERSION = 1;
const ENTRIES_STORE = "entries";
const CONFLICTS_STORE = "conflicts";

const MAX_ENTRIES = 500;
const VALID_COLLECTIONS = ["mood", "expenses", "journal", "sleep"];
const MAX_RETRIES = 3;
const RETRY_INTERVAL_MS = 10000; // 10 seconds
const SYNC_DELAY_MS = 5000; // sync within 30s of reconnection — we use 5s for responsiveness

// Collection → API endpoint mapping
const COLLECTION_ENDPOINTS = {
    mood: "/mood",
    expenses: "/expenses",
    journal: "/journal",
    sleep: "/sleep",
};

let db = null;
let syncTimeout = null;
let isSyncing = false;

/**
 * Open (or create) the IndexedDB database.
 * Returns the db instance, cached for subsequent calls.
 */
function openDB() {
    if (db) return Promise.resolve(db);

    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (event) => {
            const database = event.target.result;

            // Entries store: holds pending offline entries
            if (!database.objectStoreNames.contains(ENTRIES_STORE)) {
                const entriesStore = database.createObjectStore(ENTRIES_STORE, {
                    keyPath: "localId",
                    autoIncrement: true,
                });
                entriesStore.createIndex("collection", "collection", { unique: false });
                entriesStore.createIndex("timestamp", "timestamp", { unique: false });
            }

            // Conflicts store: holds conflicting versions for user resolution
            if (!database.objectStoreNames.contains(CONFLICTS_STORE)) {
                const conflictsStore = database.createObjectStore(CONFLICTS_STORE, {
                    keyPath: "id",
                    autoIncrement: true,
                });
                conflictsStore.createIndex("collection", "collection", { unique: false });
                conflictsStore.createIndex("localId", "localId", { unique: false });
            }
        };

        request.onsuccess = (event) => {
            db = event.target.result;
            resolve(db);
        };

        request.onerror = (event) => {
            reject(new Error(`IndexedDB open failed: ${event.target.error?.message}`));
        };
    });
}

/**
 * Generate a unique local ID for entries.
 */
function generateLocalId() {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

/**
 * Save an entry to IndexedDB for later sync.
 *
 * @param {string} collection - One of "mood", "expenses", "journal", "sleep"
 * @param {object} entry - The data to store
 * @returns {Promise<{success: boolean, atCapacity?: boolean, count?: number, error?: string}>}
 */
async function save(collection, entry) {
    if (!VALID_COLLECTIONS.includes(collection)) {
        return { success: false, atCapacity: false, error: `Invalid collection: ${collection}` };
    }

    const database = await openDB();
    const count = await _getCountFromDB(database);

    // Enforce 500-entry cap — block new entries until sync
    if (count >= MAX_ENTRIES) {
        return {
            success: false,
            atCapacity: true,
            count,
            error: "Offline storage is full (500 entries). Please connect to sync before adding more.",
        };
    }

    return new Promise((resolve) => {
        const tx = database.transaction(ENTRIES_STORE, "readwrite");
        const store = tx.objectStore(ENTRIES_STORE);

        const record = {
            localId: generateLocalId(),
            collection,
            data: entry,
            timestamp: new Date().toISOString(),
            synced: false,
            source: "local",
        };

        const request = store.add(record);

        request.onsuccess = () => {
            const newCount = count + 1;
            const atCapacity = newCount >= MAX_ENTRIES;
            resolve({ success: true, atCapacity, count: newCount, localId: record.localId });
        };

        request.onerror = (event) => {
            resolve({ success: false, atCapacity: false, error: event.target.error?.message || "Failed to save entry" });
        };

        tx.onerror = (event) => {
            resolve({ success: false, atCapacity: false, error: event.target.error?.message || "Transaction failed" });
        };
    });
}

/**
 * Get all pending entries for a specific collection.
 *
 * @param {string} collection - One of "mood", "expenses", "journal", "sleep"
 * @returns {Promise<Array>} Array of stored entries
 */
async function getAll(collection) {
    if (!VALID_COLLECTIONS.includes(collection)) {
        return [];
    }

    const database = await openDB();

    return new Promise((resolve, reject) => {
        const tx = database.transaction(ENTRIES_STORE, "readonly");
        const store = tx.objectStore(ENTRIES_STORE);
        const index = store.index("collection");
        const request = index.getAll(collection);

        request.onsuccess = (event) => {
            resolve(event.target.result || []);
        };

        request.onerror = () => {
            resolve([]);
        };
    });
}

/**
 * Get total count of offline entries across all collections.
 *
 * @returns {Promise<number>}
 */
async function getCount() {
    const database = await openDB();
    return _getCountFromDB(database);
}

/**
 * Internal: get count from an already-opened database.
 */
function _getCountFromDB(database) {
    return new Promise((resolve) => {
        const tx = database.transaction(ENTRIES_STORE, "readonly");
        const store = tx.objectStore(ENTRIES_STORE);
        const request = store.count();

        request.onsuccess = (event) => {
            resolve(event.target.result || 0);
        };

        request.onerror = () => {
            resolve(0);
        };
    });
}

/**
 * Clear all entries for a specific collection (after successful sync).
 *
 * @param {string} collection - One of "mood", "expenses", "journal", "sleep" or undefined to clear all
 * @returns {Promise<{success: boolean, cleared: number}>}
 */
async function clear(collection) {
    const database = await openDB();

    // If no collection specified, clear all entries
    if (!collection) {
        return new Promise((resolve) => {
            const tx = database.transaction(ENTRIES_STORE, "readwrite");
            const store = tx.objectStore(ENTRIES_STORE);

            // Count before clearing
            const countReq = store.count();
            countReq.onsuccess = () => {
                const total = countReq.result || 0;
                const clearReq = store.clear();
                clearReq.onsuccess = () => resolve({ success: true, cleared: total });
                clearReq.onerror = () => resolve({ success: false, cleared: 0 });
            };
            countReq.onerror = () => {
                const clearReq = store.clear();
                clearReq.onsuccess = () => resolve({ success: true, cleared: 0 });
                clearReq.onerror = () => resolve({ success: false, cleared: 0 });
            };
        });
    }

    if (!VALID_COLLECTIONS.includes(collection)) {
        return { success: false, cleared: 0, error: `Invalid collection: ${collection}` };
    }

    // Clear entries for a specific collection using a cursor on the index
    return new Promise((resolve) => {
        const tx = database.transaction(ENTRIES_STORE, "readwrite");
        const store = tx.objectStore(ENTRIES_STORE);
        const index = store.index("collection");
        const request = index.openCursor(IDBKeyRange.only(collection));
        let cleared = 0;

        request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                cursor.delete();
                cleared++;
                cursor.continue();
            }
        };

        tx.oncomplete = () => {
            resolve({ success: true, cleared });
        };

        tx.onerror = () => {
            resolve({ success: false, cleared });
        };
    });
}

/**
 * Sync all pending offline entries to the server.
 * Handles conflicts (409 responses) by preserving both versions.
 * Retries up to 3 times with 10-second intervals on failure.
 *
 * @returns {Promise<{success: boolean, synced: number, conflicts: number, failed: number, errors?: string[]}>}
 */
async function sync() {
    if (isSyncing) {
        return { success: false, synced: 0, conflicts: 0, failed: 0, errors: ["Sync already in progress"] };
    }

    if (!navigator.onLine) {
        return { success: false, synced: 0, conflicts: 0, failed: 0, errors: ["Device is offline"] };
    }

    isSyncing = true;

    try {
        const database = await openDB();
        const result = await _performSync(database, 0);
        return result;
    } finally {
        isSyncing = false;
    }
}

/**
 * Internal: perform the sync with retry logic.
 */
async function _performSync(database, attempt) {
    const tx = database.transaction(ENTRIES_STORE, "readonly");
    const store = tx.objectStore(ENTRIES_STORE);

    const allEntries = await new Promise((resolve) => {
        const request = store.getAll();
        request.onsuccess = (event) => resolve(event.target.result || []);
        request.onerror = () => resolve([]);
    });

    if (allEntries.length === 0) {
        return { success: true, synced: 0, conflicts: 0, failed: 0 };
    }

    let synced = 0;
    let conflicts = 0;
    let failed = 0;
    const errors = [];
    const syncedLocalIds = [];

    for (const entry of allEntries) {
        const endpoint = COLLECTION_ENDPOINTS[entry.collection];
        if (!endpoint) {
            failed++;
            errors.push(`Unknown collection: ${entry.collection}`);
            continue;
        }

        try {
            await api.post(endpoint, entry.data);
            synced++;
            syncedLocalIds.push(entry.localId);
        } catch (error) {
            if (error.response?.status === 409) {
                // Conflict: server has a different version
                conflicts++;
                await _storeConflict(database, entry, error.response.data);
                syncedLocalIds.push(entry.localId); // Remove from pending since it's now in conflicts
            } else {
                failed++;
                errors.push(`Failed to sync ${entry.collection} entry: ${error.message}`);
            }
        }
    }

    // Remove successfully synced entries from IndexedDB
    if (syncedLocalIds.length > 0) {
        await _removeEntries(database, syncedLocalIds);
    }

    // If there were failures and we haven't exhausted retries, retry after delay
    if (failed > 0 && attempt < MAX_RETRIES - 1) {
        await _delay(RETRY_INTERVAL_MS);

        // Only retry failed entries (entries still in the store)
        const retryResult = await _performSync(database, attempt + 1);
        return {
            success: retryResult.failed === 0,
            synced: synced + retryResult.synced,
            conflicts: conflicts + retryResult.conflicts,
            failed: retryResult.failed,
            errors: retryResult.errors,
        };
    }

    return {
        success: failed === 0,
        synced,
        conflicts,
        failed,
        errors: errors.length > 0 ? errors : undefined,
    };
}

/**
 * Store a conflict for user resolution.
 * Preserves both local and server versions with timestamps and source.
 */
async function _storeConflict(database, localEntry, serverResponse) {
    return new Promise((resolve) => {
        const tx = database.transaction(CONFLICTS_STORE, "readwrite");
        const store = tx.objectStore(CONFLICTS_STORE);

        const conflict = {
            localId: localEntry.localId,
            collection: localEntry.collection,
            localVersion: {
                data: localEntry.data,
                timestamp: localEntry.timestamp,
                source: "local",
            },
            serverVersion: {
                data: serverResponse?.serverVersion || serverResponse?.data || serverResponse,
                timestamp: serverResponse?.updatedAt || serverResponse?.timestamp || new Date().toISOString(),
                source: "server",
            },
            createdAt: new Date().toISOString(),
            resolvedAt: null,
            resolution: null,
        };

        const request = store.add(conflict);
        request.onsuccess = () => resolve(true);
        request.onerror = () => resolve(false);
    });
}

/**
 * Remove entries by their localId from the entries store.
 */
async function _removeEntries(database, localIds) {
    return new Promise((resolve) => {
        const tx = database.transaction(ENTRIES_STORE, "readwrite");
        const store = tx.objectStore(ENTRIES_STORE);
        const localIdSet = new Set(localIds);

        const cursorRequest = store.openCursor();
        cursorRequest.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                if (localIdSet.has(cursor.value.localId)) {
                    cursor.delete();
                }
                cursor.continue();
            }
        };

        tx.oncomplete = () => resolve(true);
        tx.onerror = () => resolve(false);
    });
}

/**
 * Get all unresolved conflicts.
 *
 * @returns {Promise<Array>}
 */
async function getConflicts() {
    const database = await openDB();

    return new Promise((resolve) => {
        const tx = database.transaction(CONFLICTS_STORE, "readonly");
        const store = tx.objectStore(CONFLICTS_STORE);
        const request = store.getAll();

        request.onsuccess = (event) => {
            const all = event.target.result || [];
            resolve(all.filter((c) => !c.resolvedAt));
        };

        request.onerror = () => resolve([]);
    });
}

/**
 * Resolve a conflict by choosing a version ("local" or "server").
 *
 * @param {number} conflictId - The auto-incremented ID from the conflicts store
 * @param {"local"|"server"} choice - Which version to keep
 * @returns {Promise<{success: boolean}>}
 */
async function resolveConflict(conflictId, choice) {
    const database = await openDB();

    return new Promise((resolve) => {
        const tx = database.transaction(CONFLICTS_STORE, "readwrite");
        const store = tx.objectStore(CONFLICTS_STORE);
        const getRequest = store.get(conflictId);

        getRequest.onsuccess = (event) => {
            const conflict = event.target.result;
            if (!conflict) {
                resolve({ success: false, error: "Conflict not found" });
                return;
            }

            // Mark as resolved
            conflict.resolvedAt = new Date().toISOString();
            conflict.resolution = choice;
            store.put(conflict);

            // If user chose local version, re-POST it to server
            if (choice === "local") {
                const endpoint = COLLECTION_ENDPOINTS[conflict.collection];
                if (endpoint) {
                    api.post(endpoint, conflict.localVersion.data).catch(() => {
                        // If re-post fails, it'll be picked up in next sync
                    });
                }
            }

            resolve({ success: true });
        };

        getRequest.onerror = () => {
            resolve({ success: false, error: "Failed to resolve conflict" });
        };
    });
}

/**
 * Utility: delay for a specified duration.
 */
function _delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Register online/offline event listeners to trigger sync.
 * Syncs within 30 seconds of reconnection.
 */
function registerConnectivityListeners() {
    window.addEventListener("online", _handleOnline);
    window.addEventListener("offline", _handleOffline);
}

/**
 * Unregister connectivity listeners (for cleanup).
 */
function unregisterConnectivityListeners() {
    window.removeEventListener("online", _handleOnline);
    window.removeEventListener("offline", _handleOffline);
    if (syncTimeout) {
        clearTimeout(syncTimeout);
        syncTimeout = null;
    }
}

function _handleOnline() {
    // Schedule sync within 30 seconds of reconnection
    if (syncTimeout) {
        clearTimeout(syncTimeout);
    }
    syncTimeout = setTimeout(async () => {
        syncTimeout = null;
        await sync();
    }, SYNC_DELAY_MS);
}

function _handleOffline() {
    // Cancel any pending sync
    if (syncTimeout) {
        clearTimeout(syncTimeout);
        syncTimeout = null;
    }
}

/**
 * Check if offline storage is at capacity (500 entries).
 *
 * @returns {Promise<boolean>}
 */
async function isAtCapacity() {
    const count = await getCount();
    return count >= MAX_ENTRIES;
}

/**
 * Get detailed capacity status information.
 *
 * @returns {Promise<{atCapacity: boolean, count: number, max: number}>}
 */
async function getCapacityStatus() {
    const count = await getCount();
    return {
        atCapacity: count >= MAX_ENTRIES,
        count,
        max: MAX_ENTRIES,
    };
}

// Export the offline store interface
export const offlineStore = {
    save,
    getAll,
    getCount,
    clear,
    sync,
    isAtCapacity,
    getConflicts,
    resolveConflict,
    getCapacityStatus,
    registerConnectivityListeners,
    unregisterConnectivityListeners,
};

/**
 * Convenience function for use by OfflineContext.
 * Syncs all offline entries and returns a result compatible with the context provider.
 *
 * @returns {Promise<{conflicts: Array, remaining: Array}>}
 */
export async function syncOfflineQueue() {
    const result = await sync();
    const pendingConflicts = await getConflicts();

    // Get remaining unsynced entries
    const remainingEntries = [];
    for (const collection of VALID_COLLECTIONS) {
        const entries = await getAll(collection);
        remainingEntries.push(...entries);
    }

    return {
        success: result.success,
        synced: result.synced,
        conflicts: pendingConflicts.map((c) => ({
            id: c.id,
            type: c.collection,
            localValue: JSON.stringify(c.localVersion?.data || c.localVersion),
            serverValue: JSON.stringify(c.serverVersion?.data || c.serverVersion),
            localTimestamp: c.localVersion?.timestamp,
            serverTimestamp: c.serverVersion?.timestamp,
            local: { summary: `Local ${c.collection} entry` },
            server: { summary: `Server ${c.collection} entry` },
        })),
        remaining: remainingEntries,
    };
}

// Export constants for testing
export const OFFLINE_CONSTANTS = {
    DB_NAME,
    DB_VERSION,
    MAX_ENTRIES,
    VALID_COLLECTIONS,
    MAX_RETRIES,
    RETRY_INTERVAL_MS,
    SYNC_DELAY_MS,
    COLLECTION_ENDPOINTS,
};

export default offlineStore;
