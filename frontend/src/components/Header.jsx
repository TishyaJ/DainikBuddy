import React, { useEffect, useState } from "react";
import { Flame, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { NotificationBell } from "./NotificationBell";
import { useGamification } from "../context/GamificationContext";

export const Header = ({ title, subtitle, gradient = false }) => {
  const [profile, setProfile] = useState({ streak_days: 0, avatar_initial: "A" });
  const { status } = useGamification();
  const nav = useNavigate();
  useEffect(() => {
    api.get("/profile").then((r) => setProfile(r.data)).catch(() => { });
  }, []);
  return (
    <div
      data-testid="app-header"
      className={`px-5 pt-6 pb-5 ${gradient ? "bdy-gradient text-white" : ""}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl leading-tight tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className={`text-sm mt-1 ${gradient ? "text-white/85" : "text-slate-500"}`}>
              {subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {status && (
            <button
              data-testid="xp-level-indicator"
              onClick={() => nav("/profile")}
              aria-label={`Level ${status.level}, ${status.total_xp} XP. View profile for details.`}
              className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${gradient ? "bg-white/20 text-white" : "bg-purple-100 text-purple-700"
                }`}
            >
              <Zap className="w-3.5 h-3.5" /> Lv{status.level}
            </button>
          )}
          <div
            data-testid="streak-counter"
            className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${gradient ? "bg-white/20 text-white" : "bg-orange-100 text-orange-700"
              }`}
          >
            <Flame className="w-3.5 h-3.5" /> {profile.streak_days}
          </div>
          <NotificationBell gradient={gradient} />
          <button
            onClick={() => nav("/profile")}
            data-testid="user-avatar"
            className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 text-white text-sm font-bold flex items-center justify-center ring-2 ring-white active:scale-95 transition"
          >
            {profile.avatar_initial || "A"}
          </button>
        </div>
      </div>
    </div>
  );
};
