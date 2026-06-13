import React from "react";
import { Flame, Bell } from "lucide-react";

export const Header = ({ title, subtitle, gradient = false }) => (
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
        <div
          data-testid="streak-counter"
          className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
            gradient ? "bg-white/20 text-white" : "bg-orange-100 text-orange-700"
          }`}
        >
          <Flame className="w-3.5 h-3.5" /> 5
        </div>
        <button
          data-testid="notification-bell"
          className={`w-9 h-9 rounded-full flex items-center justify-center ${
            gradient ? "bg-white/20 text-white" : "bg-white text-slate-700 border border-slate-200"
          }`}
        >
          <Bell className="w-4 h-4" />
        </button>
        <div
          data-testid="user-avatar"
          className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 text-white text-sm font-bold flex items-center justify-center ring-2 ring-white"
        >
          A
        </div>
      </div>
    </div>
  </div>
);
