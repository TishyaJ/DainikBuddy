import React from "react";
import { motion } from "framer-motion";
import { Star } from "lucide-react";

export default function XPProgressBar({ totalXp, level, xpToNextLevel }) {
    // Progress within current level: XP earned toward next level out of 100
    const progressPercent = Math.max(0, Math.min(100, ((100 - xpToNextLevel) / 100) * 100));

    return (
        <div className="flex items-center gap-3" data-testid="xp-progress-bar">
            {/* Level badge */}
            <div className="flex items-center gap-1 shrink-0">
                <Star className="w-4 h-4 text-[color:var(--bdy)]" />
                <span className="font-display font-bold text-sm text-slate-800">
                    Lv.{level}
                </span>
            </div>

            {/* Progress bar */}
            <div className="flex-1">
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden relative">
                    <motion.div
                        className="h-full rounded-full"
                        style={{
                            background: "linear-gradient(90deg, var(--bdy-soft), var(--bdy))",
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${progressPercent}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                    />
                </div>
            </div>

            {/* XP text */}
            <span className="text-xs font-semibold text-slate-500 shrink-0">
                {totalXp} XP
            </span>
        </div>
    );
}
