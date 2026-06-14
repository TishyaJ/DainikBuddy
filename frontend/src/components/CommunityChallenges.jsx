import React, { useState, useEffect } from "react";
import { api } from "../lib/api";
import { Card } from "./SubTabs";
import { EmptyState } from "./EmptyState";
import { Zap, Clock, TrendingUp, Plus, X, Check, Trophy, XCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const TYPE_BADGES = {
    streak: { label: "Streak", color: "bg-orange-100 text-orange-700" },
    xp: { label: "XP", color: "bg-purple-100 text-purple-700" },
    sessions: { label: "Sessions", color: "bg-blue-100 text-blue-700" },
    goals: { label: "Goals", color: "bg-green-100 text-green-700" },
    finance: { label: "Finance", color: "bg-emerald-100 text-emerald-700" },
    wellness: { label: "Wellness", color: "bg-pink-100 text-pink-700" },
    productivity: { label: "Productivity", color: "bg-indigo-100 text-indigo-700" },
};

const CHALLENGE_TYPES = [
    { key: "finance", label: "Finance" },
    { key: "wellness", label: "Wellness" },
    { key: "productivity", label: "Productivity" },
];

const MOOD_EMOJIS = ["😫", "😟", "😐", "🙂", "😄"];

function timeRemaining(endsAt) {
    if (!endsAt) return "";
    const diff = new Date(endsAt) - new Date();
    if (diff <= 0) return "Ended";
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    if (days > 0) return `${days}d ${hours}h left`;
    return `${hours}h left`;
}

const ReflectionForm = ({ onSubmit, onSkip }) => {
    const [mood, setMood] = useState(3);
    const [reflection, setReflection] = useState("");

    return (
        <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-200"
        >
            <p className="text-xs font-semibold text-slate-700 mb-2">How did it go?</p>
            {/* Mood slider */}
            <div className="flex items-center justify-between mb-2">
                {MOOD_EMOJIS.map((emoji, i) => (
                    <button
                        key={i}
                        onClick={() => setMood(i + 1)}
                        data-testid={`mood-emoji-${i + 1}`}
                        aria-label={`Set mood to ${i + 1} out of 5`}
                        className={`text-xl transition-transform ${mood === i + 1 ? "scale-125" : "opacity-50"}`}
                    >
                        {emoji}
                    </button>
                ))}
            </div>
            {/* Reflection text */}
            <textarea
                data-testid="challenge-reflection-input"
                value={reflection}
                onChange={(e) => setReflection(e.target.value.slice(0, 200))}
                placeholder="How did it go? (optional)"
                aria-label="Write a reflection about the challenge"
                className="w-full bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)] resize-none"
                rows={2}
                maxLength={200}
            />
            <div className="flex justify-between items-center mt-1 mb-2">
                <span className="text-[10px] text-slate-400">{reflection.length}/200</span>
            </div>
            <div className="flex gap-2">
                <motion.button
                    data-testid="save-reflection-btn"
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onSubmit({ mood, reflection: reflection.trim() || null })}
                    aria-label="Save reflection and celebrate"
                    className="flex-1 py-2 rounded-full text-xs font-semibold text-white bdy-bg"
                >
                    Save & Celebrate 🎉
                </motion.button>
                <button
                    data-testid="skip-reflection-btn"
                    onClick={onSkip}
                    aria-label="Skip reflection"
                    className="px-3 py-2 rounded-full text-xs font-semibold text-slate-500 hover:text-slate-700"
                >
                    Skip
                </button>
            </div>
        </motion.div>
    );
};

const CelebrationState = ({ xpAwarded, title }) => (
    <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mt-3 p-4 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 text-center"
        data-testid="challenge-celebration"
    >
        <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: 2, duration: 0.6 }}
            className="text-3xl mb-1"
        >
            🏆
        </motion.div>
        <p className="text-sm font-display font-bold text-slate-900">Challenge Completed!</p>
        <p className="text-xs text-slate-600 mt-0.5">{title}</p>
        <div className="mt-2 inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold">
            <Trophy className="w-3 h-3" /> +{xpAwarded} XP
        </div>
    </motion.div>
);

export const CommunityChallenges = () => {
    const [challenges, setChallenges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [joiningId, setJoiningId] = useState(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [creating, setCreating] = useState(false);
    const [newTitle, setNewTitle] = useState("");
    const [newDescription, setNewDescription] = useState("");
    const [newType, setNewType] = useState("finance");
    const [completingId, setCompletingId] = useState(null);
    const [reflectionId, setReflectionId] = useState(null);
    const [celebrationData, setCelebrationData] = useState(null);
    const [closingId, setClosingId] = useState(null);
    const [currentUserId, setCurrentUserId] = useState(null);

    useEffect(() => {
        fetchChallenges();
        // Get current user ID from profile
        api.get("/profile").then((r) => setCurrentUserId(r.data?.user_id)).catch(() => { });
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
            await fetchChallenges();
        } catch {
            // silently fail
        } finally {
            setJoiningId(null);
        }
    };

    const handleMarkComplete = (challengeId) => {
        setReflectionId(challengeId);
    };

    const handleCompleteWithReflection = async (challengeId, { mood, reflection }) => {
        setCompletingId(challengeId);
        try {
            const res = await api.post(`/social/challenges/${challengeId}/complete`, { mood, reflection });
            setCelebrationData({ id: challengeId, xp: res.data.xp_awarded || 50, title: res.data.challenge_title });
            setReflectionId(null);
            await fetchChallenges();
        } catch {
            // silently fail
        } finally {
            setCompletingId(null);
        }
    };

    const handleSkipReflection = async (challengeId) => {
        setCompletingId(challengeId);
        try {
            const res = await api.post(`/social/challenges/${challengeId}/complete`, {});
            setCelebrationData({ id: challengeId, xp: res.data.xp_awarded || 50, title: res.data.challenge_title });
            setReflectionId(null);
            await fetchChallenges();
        } catch {
            // silently fail
        } finally {
            setCompletingId(null);
        }
    };

    const handleClose = async (challengeId) => {
        if (!window.confirm("Close this challenge early? All participants will see it as ended.")) return;
        setClosingId(challengeId);
        try {
            await api.post(`/social/challenges/${challengeId}/close`);
            await fetchChallenges();
        } catch {
            // silently fail
        } finally {
            setClosingId(null);
        }
    };

    const handleCreate = async () => {
        if (!newTitle.trim() || !newDescription.trim()) return;
        setCreating(true);
        try {
            await api.post("/social/challenges", {
                title: newTitle.trim(),
                description: newDescription.trim(),
                type: newType,
                criteria: {},
                badge_id: `challenge-${Date.now()}`,
            });
            setNewTitle("");
            setNewDescription("");
            setNewType("finance");
            setShowCreateForm(false);
            await fetchChallenges();
        } catch {
            // silently fail
        } finally {
            setCreating(false);
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

    return (
        <div data-testid="community-challenges" className="space-y-3 px-5">
            {/* Create Challenge Button */}
            <motion.button
                data-testid="create-challenge-btn"
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowCreateForm(!showCreateForm)}
                aria-label="Create a new community challenge"
                className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-full text-xs font-semibold text-white bdy-bg shadow-sm"
            >
                {showCreateForm ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                {showCreateForm ? "Cancel" : "Create Challenge"}
            </motion.button>

            {/* Create Challenge Form */}
            <AnimatePresence>
                {showCreateForm && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                    >
                        <Card>
                            <h4 className="font-display font-semibold text-sm text-slate-900 mb-3">New Challenge</h4>
                            <div className="space-y-2.5">
                                <input
                                    data-testid="challenge-title-input"
                                    type="text"
                                    value={newTitle}
                                    onChange={(e) => setNewTitle(e.target.value)}
                                    placeholder="Challenge title"
                                    aria-label="Enter challenge title"
                                    className="w-full bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
                                    maxLength={80}
                                />
                                <textarea
                                    data-testid="challenge-description-input"
                                    value={newDescription}
                                    onChange={(e) => setNewDescription(e.target.value)}
                                    placeholder="Describe the challenge…"
                                    aria-label="Enter challenge description"
                                    className="w-full bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)] resize-none"
                                    rows={2}
                                    maxLength={200}
                                />
                                <div>
                                    <label className="text-xs font-semibold text-slate-600 mb-1 block">Type</label>
                                    <div className="flex gap-2" data-testid="challenge-type-selector">
                                        {CHALLENGE_TYPES.map((t) => (
                                            <button
                                                key={t.key}
                                                onClick={() => setNewType(t.key)}
                                                data-testid={`challenge-type-${t.key}`}
                                                aria-label={`Select ${t.label} challenge type`}
                                                className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${newType === t.key
                                                    ? "bdy-bg text-white"
                                                    : "bg-slate-100 text-slate-600"
                                                    }`}
                                            >
                                                {t.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <p className="text-[10px] text-slate-400">
                                    Duration: current week (Monday 00:00 UTC – Sunday 23:59 UTC)
                                </p>
                                <motion.button
                                    data-testid="submit-challenge-btn"
                                    whileTap={{ scale: 0.95 }}
                                    onClick={handleCreate}
                                    disabled={!newTitle.trim() || !newDescription.trim() || creating}
                                    aria-label="Submit new challenge"
                                    className="w-full py-2.5 rounded-full text-sm font-semibold text-white bdy-bg disabled:opacity-50"
                                >
                                    {creating ? "Creating…" : "Create Challenge"}
                                </motion.button>
                            </div>
                        </Card>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Challenge List */}
            {challenges.length === 0 && !showCreateForm ? (
                <EmptyState
                    icon={Zap}
                    title="No active challenges right now"
                    description="Be the first to create a challenge, or check back next Monday for new ones!"
                    testid="challenges-empty-state"
                />
            ) : (
                challenges.map((challenge) => {
                    const badge = TYPE_BADGES[challenge.type] || TYPE_BADGES.xp;
                    const isJoined = challenge.joined || challenge.participants?.some(p => p.user_id === currentUserId);
                    const participant = challenge.participants?.find(p => p.user_id === currentUserId);
                    const isCompleted = participant?.completed;
                    const isCreator = challenge.creator_id === currentUserId;
                    const progress = participant?.progress || challenge.progress || 0;
                    const target = challenge.target || 100;
                    const pct = Math.min(Math.round((progress / target) * 100), 100);
                    const isCelebrating = celebrationData?.id === challenge.id;

                    return (
                        <motion.div
                            key={challenge.id}
                            data-testid={`challenge-${challenge.id}`}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card>
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
                                    <span className="text-xs text-slate-400">{timeRemaining(challenge.ends_at || challenge.end_date)}</span>
                                </div>

                                {/* Action states */}
                                {isCelebrating ? (
                                    <CelebrationState xpAwarded={celebrationData.xp} title={celebrationData.title} />
                                ) : isCompleted ? (
                                    <div className="mt-2 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-center" data-testid={`challenge-completed-${challenge.id}`}>
                                        <div className="flex items-center justify-center gap-1 text-emerald-700">
                                            <Check className="w-4 h-4" />
                                            <span className="text-xs font-bold">Completed</span>
                                        </div>
                                        <span className="text-[10px] text-emerald-600">+{challenge.xp_reward || 50} XP earned</span>
                                    </div>
                                ) : isJoined ? (
                                    <div>
                                        {/* Joined badge */}
                                        <div className="flex items-center gap-1 mb-2">
                                            <span className="text-xs font-semibold text-emerald-600 flex items-center gap-0.5">
                                                <Check className="w-3 h-3" /> Joined ✓
                                            </span>
                                        </div>
                                        {/* Progress bar */}
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
                                        {/* Mark Completed button */}
                                        <AnimatePresence>
                                            {reflectionId === challenge.id ? (
                                                <ReflectionForm
                                                    onSubmit={(data) => handleCompleteWithReflection(challenge.id, data)}
                                                    onSkip={() => handleSkipReflection(challenge.id)}
                                                />
                                            ) : (
                                                <motion.button
                                                    data-testid={`mark-complete-${challenge.id}`}
                                                    whileTap={{ scale: 0.95 }}
                                                    onClick={() => handleMarkComplete(challenge.id)}
                                                    disabled={completingId === challenge.id}
                                                    aria-label={`Mark challenge ${challenge.title} as completed`}
                                                    className="mt-3 w-full py-2 rounded-full text-xs font-semibold text-white bg-emerald-600 disabled:opacity-50 transition-all"
                                                >
                                                    {completingId === challenge.id ? "Completing…" : "Mark Completed ✓"}
                                                </motion.button>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                ) : (
                                    <motion.button
                                        data-testid={`join-challenge-${challenge.id}`}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => handleJoin(challenge.id)}
                                        disabled={joiningId === challenge.id}
                                        aria-label={`Join challenge ${challenge.title}`}
                                        className="w-full py-2 rounded-full text-xs font-semibold text-white bdy-bg disabled:opacity-50 transition-all"
                                    >
                                        {joiningId === challenge.id ? "Joining…" : "Join Challenge"}
                                    </motion.button>
                                )}

                                {/* Creator: Close Challenge button */}
                                {isCreator && !isCompleted && !challenge.ended_early && (
                                    <motion.button
                                        data-testid={`close-challenge-${challenge.id}`}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => handleClose(challenge.id)}
                                        disabled={closingId === challenge.id}
                                        aria-label={`Close challenge ${challenge.title} early`}
                                        className="mt-2 w-full py-2 rounded-full text-xs font-semibold text-rose-600 bg-rose-50 border border-rose-200 disabled:opacity-50 transition-all flex items-center justify-center gap-1"
                                    >
                                        <XCircle className="w-3 h-3" />
                                        {closingId === challenge.id ? "Closing…" : "Close Challenge"}
                                    </motion.button>
                                )}
                            </Card>
                        </motion.div>
                    );
                })
            )}
        </div>
    );
};

export default CommunityChallenges;
