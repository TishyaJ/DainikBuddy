import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid,
} from "recharts";
import { ArrowLeft, TrendingUp, TrendingDown, Minus, Loader2 } from "lucide-react";
import { api } from "../lib/api";

const TIME_RANGES = [
    { key: "7d", label: "7 Days" },
    { key: "30d", label: "30 Days" },
    { key: "90d", label: "90 Days" },
];

const METRICS = [
    { key: "spending", label: "Spending", type: "bar", color: "#8B5CF6", unit: "₹" },
    { key: "mood", label: "Mood", type: "line", color: "#10B981", unit: "" },
    { key: "sleep", label: "Sleep", type: "line", color: "#3B82F6", unit: "h" },
    { key: "habits", label: "Habits", type: "bar", color: "#F59E0B", unit: "%" },
];

const TrendBadge = ({ change }) => {
    if (change == null) return null;
    const isPositive = change > 0;
    const isNeutral = change === 0;
    const Icon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;
    const color = isNeutral
        ? "text-slate-500 bg-slate-100"
        : isPositive
            ? "text-emerald-700 bg-emerald-50"
            : "text-rose-700 bg-rose-50";

    return (
        <span className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-semibold ${color}`}>
            <Icon className="w-3 h-3" />
            {Math.abs(change).toFixed(1)}%
        </span>
    );
};

const CustomTooltip = ({ active, payload, label, unit }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-white rounded-xl px-3 py-2 shadow-lg border border-slate-100 text-xs">
            <p className="text-slate-500 font-medium">{label}</p>
            <p className="font-bold text-slate-900 mt-0.5">
                {unit === "₹" ? "₹" : ""}{payload[0].value}{unit !== "₹" ? unit : ""}
            </p>
        </div>
    );
};

export default function TrendsView() {
    const nav = useNavigate();
    const [range, setRange] = useState("30d");
    const [metric, setMetric] = useState("spending");
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchTrends = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await api.get("/analytics/trends", {
                params: { range, metric },
            });
            setData(res.data);
        } catch (err) {
            setError("Unable to load trends. Please try again.");
            setData(null);
        } finally {
            setLoading(false);
        }
    }, [range, metric]);

    useEffect(() => {
        fetchTrends();
    }, [fetchTrends]);

    const activeMetric = METRICS.find((m) => m.key === metric);
    const chartData = data?.data_points || [];
    const comparison = data?.comparison;

    return (
        <div className="flex-1 overflow-auto scroll-area pb-6">
            {/* Header */}
            <div className="px-5 pt-6 pb-4">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => nav(-1)}
                        className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center active:scale-95 transition"
                        aria-label="Go back"
                    >
                        <ArrowLeft className="w-4 h-4 text-slate-700" />
                    </button>
                    <div>
                        <h1 className="font-display font-bold text-xl tracking-tight">Trends</h1>
                        <p className="text-xs text-slate-500 mt-0.5">Track your progress over time</p>
                    </div>
                </div>
            </div>

            {/* Time Range Selector */}
            <div className="px-5">
                <div className="flex gap-2">
                    {TIME_RANGES.map((t) => (
                        <button
                            key={t.key}
                            onClick={() => setRange(t.key)}
                            data-testid={`range-${t.key}`}
                            className={`shrink-0 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all active:scale-95 ${range === t.key
                                    ? "bdy-bg text-white shadow-sm"
                                    : "bg-white text-slate-600 border border-slate-200"
                                }`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Metric Selector */}
            <div className="px-5 mt-3">
                <div className="flex gap-2 overflow-x-auto hide-sb">
                    {METRICS.map((m) => (
                        <button
                            key={m.key}
                            onClick={() => setMetric(m.key)}
                            data-testid={`metric-${m.key}`}
                            className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold transition-all active:scale-95 ${metric === m.key
                                    ? "bg-slate-900 text-white"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                        >
                            {m.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Comparison Badge */}
            {comparison && (
                <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mx-5 mt-4"
                >
                    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-xs text-slate-500 font-medium">
                                    {comparison.days_used || 30}-day comparison
                                </p>
                                <p className="text-lg font-bold font-display mt-0.5">
                                    {activeMetric.unit === "₹" ? "₹" : ""}
                                    {comparison.current_avg?.toFixed(1)}
                                    {activeMetric.unit !== "₹" ? activeMetric.unit : ""}
                                </p>
                            </div>
                            <TrendBadge change={comparison.change_pct} />
                        </div>
                        {comparison.previous_avg != null && (
                            <p className="text-[11px] text-slate-400 mt-1">
                                Previous avg: {activeMetric.unit === "₹" ? "₹" : ""}
                                {comparison.previous_avg?.toFixed(1)}
                                {activeMetric.unit !== "₹" ? activeMetric.unit : ""}
                            </p>
                        )}
                    </div>
                </motion.div>
            )}

            {/* Chart Area */}
            <div className="mx-5 mt-4">
                <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                    <AnimatePresence mode="wait">
                        {loading ? (
                            <motion.div
                                key="loading"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="h-52 flex items-center justify-center"
                            >
                                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                            </motion.div>
                        ) : error ? (
                            <motion.div
                                key="error"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="h-52 flex flex-col items-center justify-center text-center"
                            >
                                <p className="text-sm text-slate-500">{error}</p>
                                <button
                                    onClick={fetchTrends}
                                    className="mt-3 text-xs font-semibold text-[color:var(--bdy)] underline"
                                >
                                    Retry
                                </button>
                            </motion.div>
                        ) : chartData.length === 0 ? (
                            <motion.div
                                key="empty"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="h-52 flex flex-col items-center justify-center text-center px-4"
                            >
                                <p className="text-sm text-slate-500">
                                    Not enough data yet. Start logging to see trends here.
                                </p>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="chart"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                                className="h-52"
                                data-testid="trends-chart"
                            >
                                <ResponsiveContainer width="100%" height="100%">
                                    {activeMetric.type === "line" ? (
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                                            <XAxis
                                                dataKey="label"
                                                tickLine={false}
                                                axisLine={false}
                                                fontSize={10}
                                                tick={{ fill: "#94A3B8" }}
                                            />
                                            <YAxis
                                                tickLine={false}
                                                axisLine={false}
                                                fontSize={10}
                                                tick={{ fill: "#94A3B8" }}
                                                width={35}
                                            />
                                            <Tooltip content={<CustomTooltip unit={activeMetric.unit} />} />
                                            <Line
                                                type="monotone"
                                                dataKey="value"
                                                stroke={activeMetric.color}
                                                strokeWidth={2.5}
                                                dot={{ r: 3, fill: activeMetric.color }}
                                                activeDot={{ r: 5 }}
                                            />
                                        </LineChart>
                                    ) : (
                                        <BarChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                                            <XAxis
                                                dataKey="label"
                                                tickLine={false}
                                                axisLine={false}
                                                fontSize={10}
                                                tick={{ fill: "#94A3B8" }}
                                            />
                                            <YAxis
                                                tickLine={false}
                                                axisLine={false}
                                                fontSize={10}
                                                tick={{ fill: "#94A3B8" }}
                                                width={35}
                                            />
                                            <Tooltip content={<CustomTooltip unit={activeMetric.unit} />} />
                                            <Bar
                                                dataKey="value"
                                                fill={activeMetric.color}
                                                radius={[6, 6, 0, 0]}
                                                maxBarSize={32}
                                            />
                                        </BarChart>
                                    )}
                                </ResponsiveContainer>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Data Summary */}
            {!loading && !error && chartData.length > 0 && data?.summary && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="mx-5 mt-4"
                >
                    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                        <h3 className="text-sm font-semibold font-display text-slate-900">Summary</h3>
                        <div className="grid grid-cols-3 gap-3 mt-3">
                            {data.summary.map((item, idx) => (
                                <div key={idx} className="text-center">
                                    <p className="text-[10px] uppercase text-slate-500 font-semibold">{item.label}</p>
                                    <p className="text-base font-bold font-display mt-0.5">{item.value}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            )}
        </div>
    );
}
