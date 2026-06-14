import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";
import { useOffline } from "../context/OfflineContext";

export const SyncStatus = () => {
    const { syncStatus, pendingSync, triggerSync } = useOffline();

    const showStatus = syncStatus === "syncing" || syncStatus === "success" || syncStatus === "error";

    return (
        <AnimatePresence>
            {showStatus && (
                <motion.div
                    initial={{ y: 50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 50, opacity: 0 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50"
                    data-testid="sync-status"
                >
                    {syncStatus === "syncing" && (
                        <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2.5 shadow-lg border border-slate-200">
                            <RefreshCw className="w-4 h-4 text-purple-600 animate-spin" />
                            <span className="text-sm font-medium text-slate-700">
                                Syncing {pendingSync} {pendingSync === 1 ? "entry" : "entries"}...
                            </span>
                        </div>
                    )}

                    {syncStatus === "success" && (
                        <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2.5 shadow-lg border border-emerald-200">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span className="text-sm font-medium text-emerald-700">All synced ✓</span>
                        </div>
                    )}

                    {syncStatus === "error" && (
                        <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2.5 shadow-lg border border-rose-200">
                            <AlertCircle className="w-4 h-4 text-rose-600" />
                            <span className="text-sm font-medium text-rose-700">Sync failed</span>
                            <button
                                onClick={triggerSync}
                                data-testid="sync-retry-btn"
                                className="ml-1 text-xs font-semibold text-purple-600 hover:text-purple-800 underline"
                            >
                                Retry
                            </button>
                        </div>
                    )}
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default SyncStatus;
