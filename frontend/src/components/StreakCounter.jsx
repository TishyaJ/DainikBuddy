import React from "react";
import { motion } from "framer-motion";
import { Flame } from "lucide-react";

const MILESTONES = [7, 14, 30, 60, 90];

export default function StreakCounter({ streakDays }) {
    const hasStreak = streakDays > 0;
    const isMilestone = MILESTONES.includes(streakDays);

    return (
        <motion.div
            className="flex items-center gap-2"
            data-testid="streak-counter"
            animate={isMilestone ? { scale: [1, 1.2, 1] } : {}}
            transition={isMilestone ? { duration: 0.4, ease: "easeInOut" } : {}}
        >
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
                {isMilestone && (
                    <motion.span
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: "spring", stiffness: 400, damping: 10 }}
                        className="text-xs ml-1"
                    >
                        🎉
                    </motion.span>
                )}
            </div>
        </motion.div>
    );
}
