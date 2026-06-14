import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Star } from "lucide-react";
import { useGamification } from "../context/GamificationContext";

// Simple particle component for celebration effect
function Particle({ delay, x, y }) {
    return (
        <motion.div
            className="absolute w-2 h-2 rounded-full"
            style={{
                background: `hsl(${Math.random() * 60 + 30}, 90%, 60%)`,
                left: "50%",
                top: "50%",
            }}
            initial={{ opacity: 1, x: 0, y: 0, scale: 1 }}
            animate={{
                opacity: [1, 1, 0],
                x: x,
                y: y,
                scale: [1, 1.5, 0],
            }}
            transition={{
                duration: 2,
                delay: delay,
                ease: "easeOut",
            }}
        />
    );
}

export default function LevelUpOverlay() {
    const { showLevelUp, dismissLevelUp, status } = useGamification();
    const level = status?.level || 1;

    // Generate random particles
    const particles = Array.from({ length: 16 }, (_, i) => ({
        id: i,
        delay: Math.random() * 0.5,
        x: (Math.random() - 0.5) * 200,
        y: (Math.random() - 0.5) * 200,
    }));

    return (
        <AnimatePresence>
            {showLevelUp && (
                <motion.div
                    className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    onClick={dismissLevelUp}
                    data-testid="level-up-overlay"
                >
                    {/* Particles */}
                    <div className="absolute inset-0 pointer-events-none overflow-hidden">
                        {particles.map((p) => (
                            <Particle key={p.id} delay={p.delay} x={p.x} y={p.y} />
                        ))}
                    </div>

                    {/* Main content — scale-up: 0 → 1.1 → 1 */}
                    <motion.div
                        className="flex flex-col items-center text-center px-6"
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: [0, 1.1, 1], opacity: 1 }}
                        exit={{ scale: 0.8, opacity: 0 }}
                        transition={{ duration: 0.5, times: [0, 0.7, 1], ease: "easeOut" }}
                    >
                        {/* Star icon */}
                        <motion.div
                            className="w-20 h-20 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center shadow-lg"
                            animate={{ rotate: [0, 10, -10, 0] }}
                            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                        >
                            <Star className="w-10 h-10 text-white fill-white" />
                        </motion.div>

                        {/* Level up text */}
                        <motion.h2
                            className="mt-5 text-3xl font-display font-bold text-white"
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                        >
                            Level Up!
                        </motion.h2>

                        <motion.p
                            className="mt-2 text-5xl font-display font-bold text-yellow-400"
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.4 }}
                        >
                            {level}
                        </motion.p>

                        <motion.p
                            className="mt-3 text-sm text-white/80"
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.6 }}
                        >
                            Congratulations! Keep up the great work 🎉
                        </motion.p>

                        <motion.p
                            className="mt-4 text-xs text-white/50"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 1 }}
                        >
                            Tap anywhere to dismiss
                        </motion.p>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
