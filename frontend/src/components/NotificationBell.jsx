import React from "react";
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "../context/NotificationContext";

export const NotificationBell = ({ gradient = false }) => {
    const { unreadCount } = useNotifications();
    const nav = useNavigate();

    return (
        <button
            data-testid="notification-bell"
            onClick={() => nav("/notifications")}
            className={`relative w-9 h-9 rounded-full flex items-center justify-center ${gradient
                    ? "bg-white/20 text-white"
                    : "bg-white text-slate-700 border border-slate-200"
                }`}
        >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
                <span
                    data-testid="notification-badge"
                    className="absolute -top-1 -right-1 min-w-[18px] h-[18px] rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center px-1"
                >
                    {unreadCount > 99 ? "99+" : unreadCount}
                </span>
            )}
        </button>
    );
};
