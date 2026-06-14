import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Clock, Server, Smartphone } from "lucide-react";
import { useOffline } from "../context/OfflineContext";

export const ConflictResolution = () => {
    const { conflicts, resolveConflict, dismissConflicts } = useOffline();

    const hasConflicts = conflicts.length > 0;

    return (
        <AnimatePresence>
            {hasConflicts && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
                    data-testid="conflict-modal"
                >
                    <motion.div
                        initial={{ scale: 0.95, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.95, opacity: 0 }}
                        transition={{ duration: 0.2, ease: "easeOut" }}
                        className="bg-white rounded-2xl w-full max-w-sm max-h-[80vh] overflow-hidden shadow-xl"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                            <h2 className="font-display font-bold text-base text-slate-800">
                                Resolve Conflicts ({conflicts.length})
                            </h2>
                            <button
                                onClick={dismissConflicts}
                                data-testid="conflict-dismiss-btn"
                                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Conflict List */}
                        <div className="overflow-auto max-h-[60vh] p-4 space-y-3">
                            {conflicts.map((conflict) => (
                                <div
                                    key={conflict.id}
                                    className="bg-slate-50 rounded-xl p-3 space-y-2"
                                    data-testid={`conflict-item-${conflict.id}`}
                                >
                                    <div className="text-xs font-semibold text-slate-500 uppercase">
                                        {conflict.type || "Entry"} Conflict
                                    </div>

                                    {/* Local version */}
                                    <div className="bg-white rounded-lg p-2.5 border border-blue-100">
                                        <div className="flex items-center gap-1.5 mb-1">
                                            <Smartphone className="w-3 h-3 text-blue-600" />
                                            <span className="text-[11px] font-semibold text-blue-700">Local Version</span>
                                        </div>
                                        <p className="text-xs text-slate-700 line-clamp-2">
                                            {conflict.localValue || conflict.local?.summary || "Local changes"}
                                        </p>
                                        {conflict.localTimestamp && (
                                            <div className="flex items-center gap-1 mt-1">
                                                <Clock className="w-3 h-3 text-slate-400" />
                                                <span className="text-[10px] text-slate-500">
                                                    {new Date(conflict.localTimestamp).toLocaleString()}
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Server version */}
                                    <div className="bg-white rounded-lg p-2.5 border border-purple-100">
                                        <div className="flex items-center gap-1.5 mb-1">
                                            <Server className="w-3 h-3 text-purple-600" />
                                            <span className="text-[11px] font-semibold text-purple-700">Server Version</span>
                                        </div>
                                        <p className="text-xs text-slate-700 line-clamp-2">
                                            {conflict.serverValue || conflict.server?.summary || "Server changes"}
                                        </p>
                                        {conflict.serverTimestamp && (
                                            <div className="flex items-center gap-1 mt-1">
                                                <Clock className="w-3 h-3 text-slate-400" />
                                                <span className="text-[10px] text-slate-500">
                                                    {new Date(conflict.serverTimestamp).toLocaleString()}
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Resolution buttons */}
                                    <div className="flex gap-2 pt-1">
                                        <button
                                            onClick={() => resolveConflict(conflict.id, "local")}
                                            data-testid={`conflict-keep-local-${conflict.id}`}
                                            className="flex-1 text-xs font-semibold py-2 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition"
                                        >
                                            Keep Local
                                        </button>
                                        <button
                                            onClick={() => resolveConflict(conflict.id, "server")}
                                            data-testid={`conflict-keep-server-${conflict.id}`}
                                            className="flex-1 text-xs font-semibold py-2 rounded-lg bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition"
                                        >
                                            Keep Server
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default ConflictResolution;
