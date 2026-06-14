import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { offlineStore, syncOfflineQueue } from "../lib/offlineSync";

const OfflineContext = createContext({
    isOnline: true,
    pendingSync: 0,
    conflicts: [],
    syncStatus: "idle", // idle | syncing | error | success
    triggerSync: () => { },
    resolveConflict: () => { },
    dismissConflicts: () => { },
});

export const OfflineProvider = ({ children }) => {
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [pendingSync, setPendingSync] = useState(0);
    const [conflicts, setConflicts] = useState([]);
    const [syncStatus, setSyncStatus] = useState("idle");
    const wasOfflineRef = useRef(!navigator.onLine);
    const syncTimeoutRef = useRef(null);

    // Listen for online/offline events — updates within 2 seconds
    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true);
            // If we were offline, trigger sync on reconnect
            if (wasOfflineRef.current) {
                wasOfflineRef.current = false;
                triggerSync();
            }
        };

        const handleOffline = () => {
            setIsOnline(false);
            wasOfflineRef.current = true;
            setSyncStatus("idle");
        };

        window.addEventListener("online", handleOnline);
        window.addEventListener("offline", handleOffline);

        return () => {
            window.removeEventListener("online", handleOnline);
            window.removeEventListener("offline", handleOffline);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Check pending sync count from IndexedDB
    useEffect(() => {
        const checkPending = async () => {
            try {
                const count = await offlineStore.getCount();
                setPendingSync(count);
            } catch {
                setPendingSync(0);
            }
        };

        checkPending();
        const interval = setInterval(checkPending, 3000);
        return () => clearInterval(interval);
    }, []);

    const triggerSync = useCallback(async () => {
        if (syncStatus === "syncing") return;

        try {
            const count = await offlineStore.getCount();
            if (count === 0) {
                setSyncStatus("idle");
                return;
            }

            setSyncStatus("syncing");
            setPendingSync(count);

            const result = await syncOfflineQueue();

            if (result?.conflicts?.length > 0) {
                setConflicts(result.conflicts);
            }

            setPendingSync(result?.remaining?.length || 0);
            setSyncStatus("success");

            // Reset to idle after showing success
            syncTimeoutRef.current = setTimeout(() => setSyncStatus("idle"), 3000);
        } catch (err) {
            console.error("Sync failed:", err);
            setSyncStatus("error");
        }
    }, [syncStatus]);

    const resolveConflict = useCallback(async (conflictId, resolution) => {
        // resolution: "local" | "server"
        try {
            await offlineStore.resolveConflict(conflictId, resolution);
            setConflicts((prev) => prev.filter((c) => c.id !== conflictId));
        } catch {
            // Silently fail — conflict stays in list
        }
    }, []);

    const dismissConflicts = useCallback(() => {
        setConflicts([]);
    }, []);

    useEffect(() => {
        return () => {
            if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
        };
    }, []);

    return (
        <OfflineContext.Provider
            value={{
                isOnline,
                pendingSync,
                conflicts,
                syncStatus,
                triggerSync,
                resolveConflict,
                dismissConflicts,
            }}
        >
            {children}
        </OfflineContext.Provider>
    );
};

export const useOffline = () => useContext(OfflineContext);
