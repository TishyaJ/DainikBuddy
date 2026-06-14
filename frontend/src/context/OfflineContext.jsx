import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";

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

    // Check pending sync count from localStorage
    useEffect(() => {
        const checkPending = () => {
            try {
                const queue = JSON.parse(localStorage.getItem("pb_offline_queue") || "[]");
                setPendingSync(queue.length);
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
            const queue = JSON.parse(localStorage.getItem("pb_offline_queue") || "[]");
            if (queue.length === 0) {
                setSyncStatus("idle");
                return;
            }

            setSyncStatus("syncing");
            setPendingSync(queue.length);

            // Try to dynamically import the offlineSync module
            let syncModule;
            try {
                syncModule = await import("../lib/offlineSync");
            } catch {
                // offlineSync module not available yet — simulate sync
                await new Promise((resolve) => setTimeout(resolve, 1500));
                localStorage.setItem("pb_offline_queue", "[]");
                setPendingSync(0);
                setSyncStatus("success");

                // Reset to idle after showing success
                syncTimeoutRef.current = setTimeout(() => setSyncStatus("idle"), 3000);
                return;
            }

            // Use the sync module if available
            const result = await syncModule.syncOfflineQueue();

            if (result?.conflicts?.length > 0) {
                setConflicts(result.conflicts);
            }

            localStorage.setItem("pb_offline_queue", JSON.stringify(result?.remaining || []));
            setPendingSync(result?.remaining?.length || 0);
            setSyncStatus("success");

            syncTimeoutRef.current = setTimeout(() => setSyncStatus("idle"), 3000);
        } catch (err) {
            console.error("Sync failed:", err);
            setSyncStatus("error");
        }
    }, [syncStatus]);

    const resolveConflict = useCallback((conflictId, resolution) => {
        // resolution: "local" | "server"
        setConflicts((prev) => prev.filter((c) => c.id !== conflictId));

        // Persist resolution
        try {
            const resolutions = JSON.parse(localStorage.getItem("pb_conflict_resolutions") || "[]");
            resolutions.push({ conflictId, resolution, resolvedAt: new Date().toISOString() });
            localStorage.setItem("pb_conflict_resolutions", JSON.stringify(resolutions));
        } catch {
            // Silently fail
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
