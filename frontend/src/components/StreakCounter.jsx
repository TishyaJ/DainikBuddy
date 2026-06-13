import React from "react";
import { motion } from "framer-motion";
import { Flame } from "lucide-react";

export default function StreakCounter({ streakDays }) {
    const hasStreak = streakDays > 0;

    return (
        <div className="flex items-center gap-2" data-testid="streak-counter">
            {hasStreak ? (
                <motion.div
                    animate={{
                        scale: [1, 1.15, 1],
                        opacity: [1, 0.8, 1],
                    }}
                    transition={{
                        duration: 1.2,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                >
                    <Flame className="w-5 h-5 text-orange-500" />
                </motion.div>
            ) : (
                <Flame className="w-5 h-5 text-slate-300" />
            )}
            <div className="flex items-baseline gap-1">
                <span className="font-display font-bold text-lg text-slate-800">
                    {streakDays}
                </span>
                <span className="text-xs text-slate-500">day streak</span>
            </div>
        </div>
    );
}
