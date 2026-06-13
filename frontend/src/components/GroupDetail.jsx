import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { SharedGoalLeaderboard } from "./SharedGoalLeaderboard";
import {
    ArrowLeft,
    Users,
    Copy,
    LogOut,
    Plus,
    Target,
    Clock,
    Loader2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const AVATAR_COLORS = [
    "from-purple-400 to-pink-400",
    "from-blue-400 to-cyan-400",
    "from-green-400 to-emerald-400",
    "from-orange-400 to-amber-400",
    "from-rose-400 to-red-400",
];

function formatTimeAgo(dateStr) {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

export const GroupDetail = () => {
    const { groupId } = useParams();
    const nav = useNavigate();
    const [group, setGroup] = useState(null);
    const [goals, setGoals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
    const [showNewGoal, setShowNewGoal] = useState(false);
    const [newGoalTitle, setNewGoalTitle] = useState("");
    const [newGoalTarget, setNewGoalTarget] = useState("");
    const [creating, setCreating] = useState(false);
    const [copied, setCopied] = useState(false);

    const fetchGroup = useCallback(async () => {
        try {
            const [groupRes, goalsRes] = await Promise.all([
                api.get(`/social/groups/${groupId}`),
                api.get(`/social/groups/${groupId}/goals`),
            ]);
            setGroup(groupRes.data);
            setGoals(goalsRes.data);
        } catch {
            // silently fail
        } finally {
            setLoading(false);
        }
    }, [groupId]);

    useEffect(() => {
        fetchGroup();
    }, [fetchGroup]);

    const handleCopyCode = () => {
        if (group?.invite_code) {
            navigator.clipboard.writeText(group.invite_code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleLeave = async () => {
        try {
            await api.post(`/social/groups/${groupId}/leave`);
            nav("/social");
        } catch {
            // silently fail
        }
    };

    const handleCreateGoal = async () => {
        if (!newGoalTitle.trim() || !newGoalTarget) return;
        setCreating(true);
        try {
            await api.post(`/social/groups/${groupId}/goals`, {
                title: newGoalTitle.trim(),
                target: Number(newGoalTarget),
            });
            setNewGoalTitle("");
            setNewGoalTarget("");
            setShowNewGoal(false);
            await fetchGroup();
        } catch {
            // silently fail
        } finally {
            setCreating(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[300px]">
                <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
            </div>
        );
    }

    if (!group) {
        return (
            <div className="p-5 text-center">
                <p className="text-sm text-slate-500">Group not found</p>
                <button onClick={() => nav("/social")} className="text-sm text-purple-600 mt-2">
                    Go back
                </button>
            </div>
        );
    }

    const members = group.members || [];
    const activityFeed = (group.activity_feed || []).slice(0, 20);

    return (
        <div className="pb-6">
            {/* Header */}
            <div className="px-5 pt-6 pb-4">
                <div className="flex items-center gap-3 mb-4">
                    <button
                        data-testid="group-back"
                        onClick={() => nav("/social")}
                        className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center"
                    >
                        <ArrowLeft className="w-4 h-4 text-slate-600" />
                    </button>
                    <h1 className="font-display font-bold text-xl text-slate-900 truncate flex-1">
                        {group.name}
                    </h1>
                </div>

                {/* Invite code + actions */}
                <div className="flex items-center gap-2 mb-2">
                    <code className="text-xs font-mono font-semibold text-purple-600 bg-purple-50 px-2.5 py-1 rounded-lg">
                        {group.invite_code}
                    </code>
                    <button
                        data-testid="copy-invite-code"
                        onClick={handleCopyCode}
                        className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                        <Copy className="w-3.5 h-3.5 text-slate-500" />
                    </button>
                    {copied && <span className="text-xs text-green-600">Copied!</span>}
                    <div className="flex-1" />
                    <button
                        data-testid="leave-group"
                        onClick={() => setShowLeaveConfirm(true)}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 transition-colors"
                    >
                        <LogOut className="w-3 h-3" /> Leave
                    </button>
                </div>
            </div>

            {/* Members section */}
            <div className="px-5 mb-5">
                <div className="flex items-center gap-2 mb-3">
                    <Users className="w-4 h-4 text-slate-500" />
                    <h3 className="text-sm font-semibold text-slate-700">Members ({members.length})</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                    {members.map((member, i) => (
                        <div
                            key={member.id || i}
                            data-testid={`member-${i}`}
                            className="flex items-center gap-2 bg-slate-50 rounded-full pl-1 pr-3 py-1"
                        >
                            <div
                                className={`w-7 h-7 rounded-full bg-gradient-to-br ${AVATAR_COLORS[i % AVATAR_COLORS.length]} text-white text-xs font-bold flex items-center justify-center`}
                            >
                                {(member.display_name || "?")[0].toUpperCase()}
                            </div>
                            <div>
                                <span className="text-xs font-medium text-slate-700">
                                    {member.display_name || "Member"}
                                </span>
                                {member.level != null && (
                                    <span className="text-[10px] text-slate-400 ml-1">Lv.{member.level}</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Shared goals */}
            <div className="px-5 mb-5">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-slate-500" />
                        <h3 className="text-sm font-semibold text-slate-700">Shared Goals</h3>
                    </div>
                    <button
                        data-testid="create-goal"
                        onClick={() => setShowNewGoal(true)}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-semibold text-purple-600 bg-purple-50 hover:bg-purple-100 transition-colors"
                    >
                        <Plus className="w-3 h-3" /> New Goal
                    </button>
                </div>

                {/* New goal form */}
                <AnimatePresence>
                    {showNewGoal && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden mb-3"
                        >
                            <div className="bg-slate-50 rounded-xl p-3 space-y-2">
                                <input
                                    data-testid="goal-title-input"
                                    type="text"
                                    placeholder="Goal title"
                                    value={newGoalTitle}
                                    onChange={(e) => setNewGoalTitle(e.target.value)}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:border-purple-300 outline-none"
                                />
                                <input
                                    data-testid="goal-target-input"
                                    type="number"
                                    placeholder="Target (e.g. 10)"
                                    value={newGoalTarget}
                                    onChange={(e) => setNewGoalTarget(e.target.value)}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:border-purple-300 outline-none"
                                    min="1"
                                />
                                <div className="flex gap-2">
                                    <button
                                        data-testid="goal-submit"
                                        onClick={handleCreateGoal}
                                        disabled={creating || !newGoalTitle.trim() || !newGoalTarget}
                                        className="flex-1 py-2 rounded-full text-xs font-semibold text-white bdy-bg disabled:opacity-50"
                                    >
                                        {creating ? "Creating…" : "Create"}
                                    </button>
                                    <button
                                        onClick={() => setShowNewGoal(false)}
                                        className="px-3 py-2 rounded-full text-xs font-medium text-slate-600 bg-white border border-slate-200"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {goals.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-4">
                        No shared goals yet. Create one to start!
                    </p>
                ) : (
                    <div className="space-y-3">
                        {goals.map((goal) => (
                            <SharedGoalLeaderboard key={goal.id} goal={goal} />
                        ))}
                    </div>
                )}
            </div>

            {/* Activity feed */}
            <div className="px-5">
                <div className="flex items-center gap-2 mb-3">
                    <Clock className="w-4 h-4 text-slate-500" />
                    <h3 className="text-sm font-semibold text-slate-700">Recent Activity</h3>
                </div>
                {activityFeed.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-4">No activity yet</p>
                ) : (
                    <div data-testid="activity-feed" className="space-y-2">
                        {activityFeed.map((item, i) => (
                            <div
                                key={item.id || i}
                                data-testid={`activity-item-${i}`}
                                className="flex items-start gap-2 py-2 border-b border-slate-50 last:border-0"
                            >
                                <div className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-1.5 shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs text-slate-700 leading-relaxed">{item.message}</p>
                                    <span className="text-[10px] text-slate-400">
                                        {formatTimeAgo(item.created_at)}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Leave confirmation modal */}
            <AnimatePresence>
                {showLeaveConfirm && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6"
                        onClick={() => setShowLeaveConfirm(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0.9 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-white rounded-2xl p-5 w-full max-w-[300px] text-center"
                        >
                            <h3 className="font-display font-semibold text-base text-slate-900 mb-2">
                                Leave Group?
                            </h3>
                            <p className="text-xs text-slate-500 mb-4">
                                You'll lose access to shared goals and activity.
                            </p>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setShowLeaveConfirm(false)}
                                    className="flex-1 py-2 rounded-full text-xs font-semibold text-slate-600 bg-slate-100"
                                >
                                    Cancel
                                </button>
                                <button
                                    data-testid="confirm-leave"
                                    onClick={handleLeave}
                                    className="flex-1 py-2 rounded-full text-xs font-semibold text-white bg-red-500"
                                >
                                    Leave
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default GroupDetail;
