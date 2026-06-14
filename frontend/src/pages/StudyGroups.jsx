import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { SubTabs } from "../components/SubTabs";
import { StudyGroupCard } from "../components/StudyGroupCard";
import { InviteCodeInput } from "../components/InviteCodeInput";
import { CommunityChallenges } from "../components/CommunityChallenges";
import { EmptyState } from "../components/EmptyState";
import {
    ArrowLeft,
    Plus,
    UserPlus,
    Users,
    X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import PageTransition from "../components/PageTransition";
import { SkeletonList } from "../components/Skeleton";

const TABS = [
    { key: "groups", label: "My Groups" },
    { key: "challenges", label: "Challenges" },
];

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
