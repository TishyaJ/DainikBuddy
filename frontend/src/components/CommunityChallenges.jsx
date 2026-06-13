import React, { useState, useEffect } from "react";
import { api } from "../lib/api";
import { Zap, Clock, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

const TYPE_BADGES = {
    streak: { label: "Streak", color: "bg-orange-100 text-orange-700" },
    xp: { label: "XP", color: "bg-purple-100 text-purple-700" },
    sessions: { label: "Sessions", color: "bg-blue-100 text-blue-700" },
    goals: { label: "Goals", color: "bg-green-100 text-green-700" },
};

function timeRemaining(endsAt) {
    if (!endsAt) return "";
    const diff = new Date(endsAt) - new Date();
    if (diff <= 0) return "Ended";
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    if (days > 0) return `${days}d ${hours}h left`;
    return `${hours}h left`;
}

export const CommunityChallenges = () => {
    const [challenges, setChallenges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [joiningId, setJoiningId] = useState(null);

    useEffect(() => {
        fetchChallenges();
    }, []);

    const fetchChallenges = async () => {
        try {
            const res = await api.get("/social/challenges");
            setChallenges(res.data);
        } catch {
            // silently fail
        } finally {
            setLoading(false);
        }
    };

    const handleJoin = async (challengeId) => {
        setJoiningId(challengeId);
        try {
            await api.post(`/social/challenges/${challengeId}/join`);
            // Refresh challenges
            await fetchChallenges();
        } catch {
            // silently fail
        } finally {
            setJoiningId(null);
        }
    };

    if (loading) {
        return (
            <div className="space-y-3 px-5">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 animate-pulse h-24" />
                ))}
            </div>
        );
    }

    if (challenges.length === 0) {
        return (
            <div className="text-center py-10 px-5">
                <Zap className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No active challenges right now</p>
                <p className="text-xs text-slate-400 mt-1">Check back next week!</p>
            </div>
        );
    }

    return (
        <div data-testid="community-challenges" className="space-y-3 px-5">
            {challenges.map((challenge) => {
                const badge = TYPE_BADGES[challenge.type] || TYPE_BADGES.xp;
                const isJoined = challenge.joined;
                const progress = challenge.progress || 0;
                const target = challenge.target || 1;
                const pct = Math.min(Math.round((progress / target) * 100), 100);

                return (
                    <motion.div
                        key={challenge.id}
                        data-testid={`challenge-${challenge.id}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100"
                    >
                        <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                                <h4 className="text-sm font-semibold text-slate-900 font-display">
                                    {challenge.title}
                                </h4>
                                {challenge.description && (
                                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                                        {challenge.description}
                                    </p>
                                )}
                            </div>
                            <span className={`shrink-0 ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold ${badge.color}`}>
                                {badge.label}
                            </span>
                        </div>

                        {/* Time remaining */}
                        <div className="flex items-center gap-1 mb-3">
                            <Clock className="w-3 h-3 text-slate-400" />
                            <span className="text-xs text-slate-400">{timeRemaining(challenge.ends_at)}</span>
                        </div>

                        {/* Action */}
                        {isJoined ? (
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs text-slate-500 flex items-center gap-1">
                                        <TrendingUp className="w-3 h-3" /> Progress
                                    </span>
                                    <span className="text-xs font-semibold text-slate-700">{pct}%</span>
                                </div>
                                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                                    <div
                                        className="h-full rounded-full bg-gradient-to-r from-purple-400 to-pink-400 transition-all"
                                        style={{ width: `${pct}%` }}
                                    />
                                </div>
                            </div>
                        ) : (
                            <motion.button
                                data-testid={`join-challenge-${challenge.id}`}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => handleJoin(challenge.id)}
                                disabled={joiningId === challenge.id}
                                className="w-full py-2 rounded-full text-xs font-semibold text-white bdy-bg disabled:opacity-50 transition-all"
                            >
                                {joiningId === challenge.id ? "Joining…" : "Join Challenge"}
                            </motion.button>
                        )}
                    </motion.div>
                );
            })}
        </div>
    );
};

export default CommunityChallenges;
