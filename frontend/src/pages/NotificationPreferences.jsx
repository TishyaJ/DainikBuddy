import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, DollarSign, Heart, Flame, Users } from "lucide-react";
import { Switch } from "../components/ui/switch";
import { useNotifications } from "../context/NotificationContext";

const PREFERENCE_OPTIONS = [
    {
        key: "budget_alerts",
        label: "Budget Alerts",
        description: "Get notified when you're close to budget limits",
        icon: DollarSign,
        color: "bg-green-100 text-green-600",
    },
    {
        key: "wellness_reminders",
        label: "Wellness Reminders",
        description: "Mindfulness and self-care nudges",
        icon: Heart,
        color: "bg-pink-100 text-pink-600",
    },
    {
        key: "streak_celebrations",
        label: "Streak Celebrations",
        description: "Celebrate your daily streaks and milestones",
        icon: Flame,
        color: "bg-orange-100 text-orange-600",
    },
    {
        key: "social_updates",
        label: "Social Updates",
        description: "Community activity and friend interactions",
        icon: Users,
        color: "bg-blue-100 text-blue-600",
    },
];

const NotificationPreferences = () => {
    const nav = useNavigate();
    const { preferences, updatePreferences } = useNotifications();

    const handleToggle = (key, checked) => {
        updatePreferences({ [key]: checked });
    };

    return (
        <div className="flex flex-col h-full bg-slate-50">
            {/* Header */}
            <div className="px-5 pt-6 pb-4 bg-white border-b border-slate-100">
                <div className="flex items-center gap-3">
                    <button
                        data-testid="preferences-back"
                        onClick={() => nav(-1)}
                        className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 text-slate-700"
                    >
                        <ArrowLeft className="w-4 h-4" />
                    </button>
                    <h1 className="font-display font-bold text-xl">Notification Preferences</h1>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
                <div className="space-y-3">
                    {PREFERENCE_OPTIONS.map((option) => {
                        const IconComponent = option.icon;
                        const isChecked = preferences?.[option.key] ?? true;

                        return (
                            <div
                                key={option.key}
                                data-testid={`preference-${option.key}`}
                                className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex items-center gap-3"
                            >
                                <div
                                    className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${option.color}`}
                                >
                                    <IconComponent className="w-4 h-4" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-slate-800">{option.label}</p>
                                    <p className="text-xs text-slate-500 mt-0.5">{option.description}</p>
                                </div>
                                <Switch
                                    data-testid={`toggle-${option.key}`}
                                    checked={isChecked}
                                    onCheckedChange={(checked) => handleToggle(option.key, checked)}
                                />
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default NotificationPreferences;
