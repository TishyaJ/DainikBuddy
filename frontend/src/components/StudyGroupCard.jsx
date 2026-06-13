import React from "react";
import { useNavigate } from "react-router-dom";
import { Users, Copy } from "lucide-react";
import { motion } from "framer-motion";

const AVATAR_COLORS = [
    "from-purple-400 to-pink-400",
    "from-blue-400 to-cyan-400",
    "from-green-400 to-emerald-400",
    "from-orange-400 to-amber-400",
    "from-rose-400 to-red-400",
];

export const StudyGroupCard = ({ group }) => {
    const nav = useNavigate();
    const members = group.members || [];
    const previewMembers = members.slice(0, 4);

    const handleCopy = (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(group.invite_code);
    };

    return (
        <motion.div
            data-testid={`group-card-${group.id}`}
            whileTap={{ scale: 0.98 }}
            onClick={() => nav(`/social/group/${group.id}`)}
            className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 cursor-pointer active:bg-slate-50 transition-colors"
        >
            <div className="flex items-center justify-between mb-3">
                <h3 className="font-display font-semibold text-sm text-slate-900 truncate flex-1">
                    {group.name}
                </h3>
                <div className="flex items-center gap-1 text-xs text-slate-500">
                    <Users className="w-3.5 h-3.5" />
                    <span>{group.member_count || members.length}</span>
                </div>
            </div>

            {/* Member avatars preview */}
            <div className="flex items-center gap-1 mb-3">
                {previewMembers.map((member, i) => (
                    <div
                        key={member.id || i}
                        className={`w-8 h-8 rounded-full bg-gradient-to-br ${AVATAR_COLORS[i % AVATAR_COLORS.length]} text-white text-xs font-bold flex items-center justify-center ring-2 ring-white -ml-${i > 0 ? "1.5" : "0"}`}
                        style={{ marginLeft: i > 0 ? "-6px" : "0" }}
                    >
                        {(member.display_name || "?")[0].toUpperCase()}
                    </div>
                ))}
                {members.length > 4 && (
                    <div
                        className="w-8 h-8 rounded-full bg-slate-100 text-slate-500 text-xs font-bold flex items-center justify-center ring-2 ring-white"
                        style={{ marginLeft: "-6px" }}
                    >
                        +{members.length - 4}
                    </div>
                )}
            </div>

            {/* Invite code */}
            {group.invite_code && (
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Code:</span>
                    <code className="text-xs font-mono font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded">
                        {group.invite_code}
                    </code>
                    <button
                        data-testid={`copy-code-${group.id}`}
                        onClick={handleCopy}
                        className="p-1 rounded-md hover:bg-slate-100 transition-colors"
                    >
                        <Copy className="w-3 h-3 text-slate-400" />
                    </button>
                </div>
            )}
        </motion.div>
    );
};

export default StudyGroupCard;
