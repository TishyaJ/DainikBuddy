import React, { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { api } from "../lib/api";

/**
 * AnomalyFlag — Inline spending anomaly indicator.
 * Fetches detected anomalies from the analytics API and renders
 * a banner for each one showing the amount, average, and % deviation.
 *
 * Validates: Requirements 6.3
 */
export function AnomalyFlag({ limit = 5 }) {
    const [anomalies, setAnomalies] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api
            .get("/analytics/anomalies")
            .then((r) => setAnomalies((r.data || []).slice(0, limit)))
            .catch(() => setAnomalies([]))
            .finally(() => setLoading(false));
    }, [limit]);

    if (loading || anomalies.length === 0) return null;

    return (
        <div className="space-y-2" data-testid="anomaly-flags">
            {anomalies.map((a, idx) => (
                <motion.div
                    key={a.id || idx}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-start gap-3 p-3 rounded-xl bg-rose-50 border border-rose-100"
                    data-testid={`anomaly-flag-${idx}`}
                >
                    <div className="w-8 h-8 rounded-lg bg-rose-100 flex items-center justify-center shrink-0">
                        <AlertTriangle className="w-4 h-4 text-rose-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                            <span className="text-sm font-semibold text-rose-700 truncate">
                                Spending Anomaly
                            </span>
                            <span className="text-xs font-bold text-rose-600 shrink-0">
                                +{Math.round(a.deviation_pct || 0)}%
                            </span>
                        </div>
                        <p className="text-xs text-rose-600 mt-0.5 leading-relaxed">
                            You spent{" "}
                            <span className="font-semibold">₹{(a.amount || 0).toLocaleString()}</span>{" "}
                            {a.date ? `on ${a.date}` : "today"} — your 30-day daily average is{" "}
                            <span className="font-semibold">₹{(a.daily_average || 0).toLocaleString()}</span>.
                        </p>
                        {a.category && (
                            <span className="inline-block mt-1.5 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-rose-100 text-rose-700">
                                {a.category}
                            </span>
                        )}
                    </div>
                </motion.div>
            ))}
        </div>
    );
}

export default AnomalyFlag;
