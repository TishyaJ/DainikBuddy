import React from "react";
import { motion } from "framer-motion";
import { Trophy, Lock, Check } from "lucide-react";

export default function AchievementBadge({ achievement, index = 0 }) {
    const { name, description, earned } = achievement;

    return (
        <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{
                type: "spring",
                stiffness: 300,
                damping: 20,
                delay: index * 0.08,
            }}
            className={`relative flex flex-col items-center p-3 rounded-xl border text-center ${earned
                ? "bg-white border-slate-100 shadow-sm"
                : "bg-slate-50 border-slate-100 opacity-60"
                }`}
            data-testid="achievement-badge"
        >
            {/* Icon */}
            <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${earned ? "bdy-bg text-white" : "bg-slate-200 text-slate-400"
                    }`}
            >
                {earned ? (
                    <Trophy className="w-5 h-5" />
                ) : (
                    <Lock className="w-4 h-4" />
                )}
            </div>

            {/* Checkmark overlay for earned badges */}
            {earned && (
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 400, damping: 15, delay: 0.3 + index * 0.08 }}
                    className="absolute top-2 right-2 w-4 h-4 rounded-full bg-green-500 flex items-center justify-center"
                >
                    <Check className="w-2.5 h-2.5 text-white" />
                </motion.div>
            )}

            {/* Name */}
            <span
                className={`mt-2 text-xs font-semibold leading-tight ${earned ? "text-slate-800" : "text-slate-400"
                    }`}
            >
                {name}
            </span>

            {/* Description */}
            {description && (
                <span className="mt-0.5 text-[10px] text-slate-400 leading-tight line-clamp-2">
                    {description}
                </span>
            )}
        </motion.div>
    );
}
