import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { SubTabs } from "../components/SubTabs";
import { StudyGroupCard } from "../components/StudyGroupCard";
import { InviteCodeInput } from "../components/InviteCodeInput";
import { CommunityChallenges } from "../components/CommunityChallenges";
import { EmptyState } from "../components/EmptyState";
import { ExerciseTracker } from "../components/Exercise";
import {
    ArrowLeft,
    Plus,
    UserPlus,
    Users,
    X,
    Sparkles,
    Target,
    Dumbbell,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import PageTransition from "../components/PageTransition";
import { SkeletonList } from "../components/Skeleton";
import { Card } from "../components/SubTabs";

const TABS = [
    { key: "groups", label: "My Groups" },
    { key: "challenges", label: "Challenges" },
    { key: "goals", label: "Goals" },
    { key: "fitness", label: "Fitness" },
];

const GoalsTab = () => {
    const [goals, setGoals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newTitle, setNewTitle] = useState("");
    const [newTarget, setNewTarget] = useState("");
    const [expandedId, setExpandedId] = useState(null);
    const [updating, setUpdating] = useState(null);

    const load = useCallback(async () => {
        try {
            const r = await api.get("/goals");
            setGoals(r.data);
        } catch { /* */ } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const addGoal = async () => {
        if (!newTitle.trim()) return;
        const target = parseFloat(newTarget) || 100;
        await api.post("/goals", { title: newTitle.trim(), target, current: 0, unit: "%" });
        setNewTitle(""); setNewTarget("");
        load();
    };

    const handleProgress = async (id, val) => {
        setUpdating(id);
        try {
            await api.patch(`/goals/${id}`, { current: val });
            setGoals((prev) => prev.map((g) => g.id === id ? { ...g, current: val } : g));
        } catch { /* */ } finally { setUpdating(null); }
    };

    const handleArchive = async (id) => {
        await api.patch(`/goals/${id}`, { status: "done" });
        setGoals((prev) => prev.filter((g) => g.id !== id));
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this goal permanently?")) return;
        await api.delete(`/goals/${id}`);
        setGoals((prev) => prev.filter((g) => g.id !== id));
    };

    const active = goals.filter(g => g.status === "active");

    return (
        <div className="px-5 space-y-3">
            <Card>
                <h3 className="font-display font-bold text-base">My Goals</h3>
                {loading ? <SkeletonList count={3} /> : active.length === 0 ? (
                    <EmptyState icon={Target} title="No goals yet" description="Set a goal to track your progress with accountability." />
                ) : (
                    <div className="mt-3 space-y-2" data-testid="social-goals-list">
                        {active.map((g) => {
                            const pct = g.target > 0 ? Math.min(100, Math.round((g.current / g.target) * 100)) : 0;
                            const expanded = expandedId === g.id;
                            return (
                                <div key={g.id} className="p-2 rounded-xl bg-slate-50">
                                    <div className="flex justify-between text-sm cursor-pointer" onClick={() => setExpandedId(expanded ? null : g.id)}
                                        role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") setExpandedId(expanded ? null : g.id); }}>
                                        <span className="font-semibold">{g.title}</span>
                                        <span className="bdy-text font-bold">{pct}%</span>
                                    </div>
                                    <div className="h-2 mt-1 rounded-full bg-slate-100">
                                        <div className="h-full bdy-bg rounded-full transition-all" style={{ width: `${pct}%` }} />
                                    </div>
                                    {expanded && (
                                        <div className="mt-2 pt-2 border-t border-slate-200">
                                            <div className="flex justify-between text-xs text-slate-500 mb-1">
                                                <span>{g.current} / {g.target} {g.unit || ""}</span>
                                                <span className="bdy-text font-semibold">{pct}%</span>
                                            </div>
                                            <input type="range" min="0" max={g.target} step={g.target >= 100 ? 1 : 0.5}
                                                value={g.current}
                                                onChange={(e) => setGoals((p) => p.map((x) => x.id === g.id ? { ...x, current: parseFloat(e.target.value) } : x))}
                                                onMouseUp={(e) => handleProgress(g.id, parseFloat(e.target.value))}
                                                onTouchEnd={(e) => handleProgress(g.id, parseFloat(e.target.value))}
                                                className="bdy-slider w-full" disabled={updating === g.id} />
                                        </div>
                                    )}
                                    {pct >= 100 && (
                                        <div className="mt-2 flex gap-2">
                                            <button onClick={() => handleArchive(g.id)} className="flex-1 py-1.5 rounded-lg text-xs font-semibold text-white bdy-bg">Archive</button>
                                            <button onClick={() => handleDelete(g.id)} className="flex-1 py-1.5 rounded-lg text-xs font-semibold text-rose-600 bg-rose-50 border border-rose-200">Delete</button>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                    <div className="flex gap-2">
                        <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="Goal title"
                            aria-label="Enter goal title" className="flex-1 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
                        <input type="number" min="0" value={newTarget} onChange={(e) => setNewTarget(e.target.value)} placeholder="Target"
                            aria-label="Enter goal target" className="w-20 bg-slate-50 rounded-xl px-2 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
                    </div>
                    <button onClick={addGoal} disabled={!newTitle.trim()}
                        className="w-full bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 disabled:opacity-50 active:scale-95">
                        <Plus className="w-4 h-4" /> Add Goal
                    </button>
                </div>
            </Card>
        </div>
    );
};

const StudyGroups = () => {
    const nav = useNavigate();
    const [activeTab, setActiveTab] = useState("groups");
    const [groups, setGroups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showJoinModal, setShowJoinModal] = useState(false);
    const [newGroupName, setNewGroupName] = useState("");
    const [creating, setCreating] = useState(false);
    const [joinLoading, setJoinLoading] = useState(false);
    const [joinError, setJoinError] = useState("");

    const fetchGroups = useCallback(async () => {
        try {
            const res = await api.get("/social/groups");
            setGroups(res.data);
        } catch {
            // silently fail
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchGroups();
    }, [fetchGroups]);

    const handleCreateGroup = async () => {
        if (!newGroupName.trim()) return;
        setCreating(true);
        try {
            await api.post("/social/groups", { name: newGroupName.trim() });
            setNewGroupName("");
            setShowCreateModal(false);
            await fetchGroups();
        } catch {
            // silently fail
        } finally {
            setCreating(false);
        }
    };

    const handleJoinGroup = async (code) => {
        setJoinLoading(true);
        setJoinError("");
        try {
            await api.post("/social/groups/join", { invite_code: code });
            setShowJoinModal(false);
            await fetchGroups();
        } catch (err) {
            setJoinError(err?.response?.data?.detail || "Invalid invite code");
        } finally {
            setJoinLoading(false);
        }
    };

    return (
        <PageTransition className="flex-1 overflow-auto scroll-area pb-6">
            {/* Header */}
            <div className="px-5 pt-6 pb-3">
                <div className="flex items-center gap-3 mb-1">
                    <button
                        data-testid="social-back"
                        onClick={() => nav("/")}
                        aria-label="Go back to home"
                        className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center"
                    >
                        <ArrowLeft className="w-4 h-4 text-slate-600" />
                    </button>
                    <h1 className="font-display font-bold text-xl text-slate-900">Social</h1>
                </div>
            </div>

            {/* Tabs */}
            <SubTabs tabs={TABS} active={activeTab} onChange={setActiveTab} testid="social-tab" />

            {/* Groups tab */}
            {activeTab === "groups" && (
                <div className="mt-3">
                    {/* Action buttons */}
                    <div className="flex gap-2 px-5 mb-4">
                        <motion.button
                            data-testid="create-group-btn"
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setShowCreateModal(true)}
                            aria-label="Create a new study group"
                            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold text-white bdy-bg shadow-sm"
                        >
                            <Plus className="w-3.5 h-3.5" /> Create Group
                        </motion.button>
                        <motion.button
                            data-testid="join-group-btn"
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setShowJoinModal(true)}
                            aria-label="Join a study group with invite code"
                            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold bdy-text bdy-soft border border-[color:var(--bdy)]/20"
                        >
                            <UserPlus className="w-3.5 h-3.5" /> Join Group
                        </motion.button>
                    </div>

                    {/* Groups list */}
                    {loading ? (
                        <div className="px-5">
                            <SkeletonList count={3} />
                        </div>
                    ) : groups.length === 0 ? (
                        <div className="px-5">
                            <EmptyState
                                icon={Users}
                                title="No groups yet"
                                description="Create a study group or join one with an invite code to connect with peers."
                                ctaLabel="Create Group"
                                onCta={() => setShowCreateModal(true)}
                                testid="groups-empty-state"
                            />
                        </div>
                    ) : (
                        <div data-testid="groups-list" className="space-y-3 px-5">
                            {groups.map((group) => (
                                <StudyGroupCard key={group.id} group={group} />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Challenges tab */}
            {activeTab === "challenges" && (
                <div className="mt-3">
                    <CommunityChallenges />
                </div>
            )}

            {/* Goals tab */}
            {activeTab === "goals" && (
                <div className="mt-3">
                    <GoalsTab />
                </div>
            )}

            {/* Fitness tab */}
            {activeTab === "fitness" && (
                <div className="mt-3">
                    <ExerciseTracker />
                </div>
            )}

            {/* Create Group Modal */}
            <AnimatePresence>
                {showCreateModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6"
                        onClick={() => setShowCreateModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-white rounded-2xl p-5 w-full max-w-[320px]"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-display font-semibold text-base text-slate-900">
                                    Create Group
                                </h3>
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="p-1 rounded-full hover:bg-slate-100"
                                >
                                    <X className="w-4 h-4 text-slate-500" />
                                </button>
                            </div>
                            <input
                                data-testid="create-group-name"
                                type="text"
                                placeholder="Group name"
                                value={newGroupName}
                                onChange={(e) => setNewGroupName(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleCreateGroup()}
                                aria-label="Enter group name"
                                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-300 outline-none mb-3"
                                maxLength={50}
                            />
                            <motion.button
                                data-testid="create-group-submit"
                                whileTap={{ scale: 0.95 }}
                                onClick={handleCreateGroup}
                                disabled={!newGroupName.trim() || creating}
                                aria-label="Submit group creation"
                                className="w-full py-2.5 rounded-full text-sm font-semibold text-white bdy-bg disabled:opacity-50"
                            >
                                {creating ? "Creating…" : "Create"}
                            </motion.button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Join Group Modal */}
            <AnimatePresence>
                {showJoinModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6"
                        onClick={() => setShowJoinModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-white rounded-2xl p-5 w-full max-w-[320px]"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-display font-semibold text-base text-slate-900">
                                    Join Group
                                </h3>
                                <button
                                    onClick={() => setShowJoinModal(false)}
                                    className="p-1 rounded-full hover:bg-slate-100"
                                >
                                    <X className="w-4 h-4 text-slate-500" />
                                </button>
                            </div>
                            <p className="text-xs text-slate-500 mb-4">
                                Enter the 6-character invite code to join a group
                            </p>
                            <InviteCodeInput
                                onSubmit={handleJoinGroup}
                                loading={joinLoading}
                                error={joinError}
                            />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </PageTransition>
    );
};

export default StudyGroups;
