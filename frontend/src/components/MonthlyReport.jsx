import React, { useEffect, useState } from "react";
import { FileText, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { motion } from "framer-motion";
import { api } from "../lib/api";
import { Card } from "./SubTabs";

/**
 * MonthlyReport — Financial health report card display.
 * Fetches the monthly financial report from the analytics API and
 * renders a summary card with income vs spending, category adherence,
 * savings progress, and predicted month-end balance.
 *
 * Validates: Requirements 6.2, 6.6
 */
export function MonthlyReport() {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api
            .get("/analytics/monthly-report")
            .then((r) => setReport(r.data))
            .catch(() => setReport(null))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="mx-5 mt-4 animate-pulse">
                <div className="h-5 bg-slate-100 rounded w-40 mb-3" />
                <div className="h-24 bg-slate-50 rounded-xl" />
            </Card>
        );
    }

    if (!report) {
        return (
            <Card className="mx-5 mt-4">
                <div className="flex items-center gap-2 text-slate-400">
                    <FileText className="w-4 h-4" />
                    <span className="text-sm font-semibold">No report available yet</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                    Keep logging expenses to generate your monthly financial health report.
                </p>
            </Card>
        );
    }

    const {
        total_income = 0,
        total_spending = 0,
        savings_progress = 0,
        predicted_end_balance = 0,
        categories = [],
        month_label = "This Month",
    } = report;

    const netFlow = total_income - total_spending;
    const netPositive = netFlow >= 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-5 mt-4 space-y-3"
            data-testid="monthly-report"
        >
            {/* Header card */}
            <Card>
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bdy-bg text-white flex items-center justify-center">
                        <FileText className="w-4 h-4" />
                    </div>
                    <div>
                        <h3 className="font-display font-bold text-base">Financial Health Report</h3>
                        <p className="text-[11px] text-slate-500">{month_label}</p>
                    </div>
                </div>

                {/* Income vs Spending */}
                <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 rounded-xl bg-emerald-50">
                        <div className="text-[10px] font-semibold uppercase text-emerald-700">Income</div>
                        <div className="font-display font-bold text-lg text-emerald-700">
                            ₹{total_income.toLocaleString()}
                        </div>
                    </div>
                    <div className="p-3 rounded-xl bg-rose-50">
                        <div className="text-[10px] font-semibold uppercase text-rose-700">Spending</div>
                        <div className="font-display font-bold text-lg text-rose-700">
                            ₹{total_spending.toLocaleString()}
                        </div>
                    </div>
                </div>

                {/* Net flow */}
                <div
                    className={`mt-2 p-3 rounded-xl ${netPositive ? "bg-emerald-50 border border-emerald-100" : "bg-rose-50 border border-rose-100"
                        }`}
                >
                    <div className="flex items-center gap-2">
                        {netPositive ? (
                            <TrendingUp className="w-4 h-4 text-emerald-600" />
                        ) : (
                            <TrendingDown className="w-4 h-4 text-rose-600" />
                        )}
                        <span
                            className={`text-sm font-semibold ${netPositive ? "text-emerald-700" : "text-rose-700"
                                }`}
                        >
                            {netPositive ? "+" : ""}₹{netFlow.toLocaleString()} net
                        </span>
                    </div>
                </div>
            </Card>

            {/* Category adherence */}
            {categories.length > 0 && (
                <Card>
                    <h4 className="font-display font-bold text-sm mb-3">Budget Adherence</h4>
                    <div className="space-y-2.5" data-testid="report-categories">
                        {categories.map((cat) => {
                            const pct = cat.adherence_pct ?? 0;
                            const isOver = pct > 100;
                            return (
                                <div key={cat.name}>
                                    <div className="flex justify-between items-center text-xs mb-1">
                                        <span className="font-semibold text-slate-700">{cat.name}</span>
                                        <span
                                            className={`font-bold ${isOver ? "text-rose-600" : pct > 80 ? "text-amber-600" : "text-emerald-600"
                                                }`}
                                        >
                                            {pct}%
                                        </span>
                                    </div>
                                    <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all ${isOver ? "bg-rose-500" : pct > 80 ? "bg-amber-500" : "bdy-bg"
                                                }`}
                                            style={{ width: `${Math.min(pct, 100)}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </Card>
            )}

            {/* Savings & Prediction */}
            <Card>
                <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 rounded-xl bg-slate-50">
                        <div className="text-[10px] font-semibold uppercase text-slate-500">Savings Progress</div>
                        <div className="font-display font-bold text-lg mt-0.5">{savings_progress}%</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-50">
                        <div className="text-[10px] font-semibold uppercase text-slate-500">Predicted End</div>
                        <div
                            className={`font-display font-bold text-lg mt-0.5 ${predicted_end_balance >= 0 ? "text-emerald-700" : "text-rose-700"
                                }`}
                        >
                            ₹{predicted_end_balance.toLocaleString()}
                        </div>
                    </div>
                </div>
            </Card>
        </motion.div>
    );
}

export default MonthlyReport;
