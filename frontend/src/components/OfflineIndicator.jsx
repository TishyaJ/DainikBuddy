import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WifiOff } from "lucide-react";
import { useOffline } from "../context/OfflineContext";

export const OfflineIndicator = () => {
    const { isOnline, pendingSync } = useOffline();

    return (
        <AnimatePresence>
            {!isOnline && (
                <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: "easeInOut" }}
                    className="overflow-hidden"
                    data-testid="offline-indicator"
                >
                    <div className="bg-amber-50 border border-amber-200 px-4 py-2.5 flex items-center gap-2">
                        <WifiOff className="w-4 h-4 text-amber-600 shrink-0" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-amber-800">
                                You're offline. Data will sync when connected.
                            </p>
                            {pendingSync > 0 && (
                                <p className="text-xs text-amber-600">
                                    {pendingSync} {pendingSync === 1 ? "entry" : "entries"} waiting to sync
                                </p>
                            )}
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default OfflineIndicator;
