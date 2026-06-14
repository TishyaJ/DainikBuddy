import React from "react";
import { Trophy, Target, Users } from "lucide-react";
import { Card } from "./SubTabs";
import { EmptyState } from "./EmptyState";

export const SharedGoalLeaderboard = ({ goal }) => {
    if (!goal) return null;

    const target = goal.target || 1;
    // Sort members by completion percentage descending
    const sortedMembers = [...(goal.members || [])].sort((a, b) => {
        const pctA = ((a.current || 0) / target) * 100;
        const pctB = ((b.current || 0) / target) * 100;
        return pctB - pctA;
    });

    return (
        <Card
            data-testid={`leaderboard-${goal.id}`}
        >
            {/* Goal header */}
            <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
                    <Target className="w-4 h-4 text-amber-600" />
                </div>
                <div className="flex-1">
                    <h4 className="text-sm font-semibold text-slate-900 font-display">{goal.title}</h4>
                    <p className="text-xs text-slate-500">Target: {target}</p>
                </div>
            </div>

            {/* Members leaderboard */}
            <div className="space-y-2.5">
                {sortedMembers.map((member, i) => {
                    const current = member.current || 0;
                    const pct = Math.min(Math.round((current / target) * 100), 100);

                    return (
                        <div key={member.user_id || i} data-testid={`leaderboard-member-${i}`} className="flex items-center gap-3">
                            {/* Rank */}
                            <div className="w-5 text-center">
                                {i === 0 ? (
                                    <Trophy className="w-4 h-4 text-amber-500 mx-auto" />
                                ) : (
                                    <span className="text-xs font-bold text-slate-400">{i + 1}</span>
                                )}
                            </div>

                            {/* Name and progress */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-medium text-slate-700 truncate">
                                        {member.display_name || "Member"}
                                    </span>
                                    <span className="text-xs text-slate-500 shrink-0 ml-2">
                                        {current}/{target} ({pct}%)
                                    </span>
                                </div>
                                <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                                    <div
                                        className="h-full rounded-full bg-gradient-to-r from-purple-400 to-pink-400 transition-all duration-300"
                                        style={{ width: `${pct}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {sortedMembers.length === 0 && (
                <EmptyState
                    icon={Users}
                    title="No members yet"
                    description="Invite group members to start tracking this goal together."
                    useCard={false}
                    testid="leaderboard-empty-state"
                />
            )}
        </Card>
    );
};

export default SharedGoalLeaderboard;
