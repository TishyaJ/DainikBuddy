import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Bell, DollarSign, Heart, Flame, Settings, BellOff } from "lucide-react";
import { useNotifications } from "../context/NotificationContext";

const CATEGORY_ICONS = {
    reminder: Bell,
    budget: DollarSign,
    wellness: Heart,
    streak: Flame,
};

function getRelativeTime(dateStr) {
    const now = new Date();
    const date = new Date(dateStr);
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffMs / 86400000);

    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin} min ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
}

const NotificationCenter = () => {
    const nav = useNavigate();
    const { notifications, loading, markDismissed } = useNotifications();

    const recentNotifications = [...notifications]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 10);

    return (
        <div className="flex flex-col h-full bg-slate-50">
            {/* Header */}
            <div className="px-5 pt-6 pb-4 bg-white border-b border-slate-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button
                            data-testid="notification-back"
                            onClick={() => nav(-1)}
                            className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 text-slate-700"
                        >
                            <ArrowLeft className="w-4 h-4" />
                        </button>
                        <h1 className="font-display font-bold text-xl">Notifications</h1>
                    </div>
                    <button
                        data-testid="notification-preferences-link"
                        onClick={() => nav("/notifications/preferences")}
                        className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 text-slate-700"
                    >
                        <Settings className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : recentNotifications.length === 0 ? (
                    <div
                        data-testid="notification-empty-state"
                        className="flex flex-col items-center justify-center py-16 text-center"
                    >
                        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                            <BellOff className="w-8 h-8 text-slate-400" />
                        </div>
                        <p className="text-slate-500 text-base font-medium">No notifications yet</p>
                        <p className="text-slate-400 text-sm mt-1">
                            We'll notify you about important updates
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {recentNotifications.map((notification) => {
                            const IconComponent = CATEGORY_ICONS[notification.category] || Bell;
                            return (
                                <div
                                    key={notification.id}
                                    data-testid="notification-item"
                                    className={`bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex items-start gap-3 ${!notification.is_read ? "border-l-4 border-l-purple-400" : ""
                                        }`}
                                >
                                    <div
                                        className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${!notification.is_read
                                                ? "bg-purple-100 text-purple-600"
                                                : "bg-slate-100 text-slate-500"
                                            }`}
                                    >
                                        <IconComponent className="w-4 h-4" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-2">
                                            <p
                                                className={`text-sm leading-tight ${!notification.is_read ? "font-semibold text-slate-800" : "text-slate-600"
                                                    }`}
                                            >
                                                {notification.title}
                                            </p>
                                            <span className="text-[11px] text-slate-400 whitespace-nowrap shrink-0">
                                                {getRelativeTime(notification.created_at)}
                                            </span>
                                        </div>
                                        {notification.body && (
                                            <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                                                {notification.body}
                                            </p>
                                        )}
                                    </div>
                                    <button
                                        data-testid="notification-dismiss"
                                        onClick={() => markDismissed(notification.id)}
                                        className="text-slate-400 hover:text-slate-600 text-xs shrink-0 mt-1"
                                        title="Dismiss"
                                    >
                                        ✕
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotificationCenter;
