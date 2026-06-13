import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Card, InsightCard } from "../components/SubTabs";
import Onboarding from "./Onboarding";
import { ArrowLeft, Pencil, Wallet, Heart, Flame, Sparkles, LogOut, Check, X } from "lucide-react";
import { useGamification } from "../context/GamificationContext";
import { useAuth } from "../context/AuthContext";
import XPProgressBar from "../components/XPProgressBar";
import StreakCounter from "../components/StreakCounter";
import AchievementBadge from "../components/AchievementBadge";

const PATTERN_LABELS = {
  spending_style: { label: "Spending style", icon: "💸", map: { careful: "Carefully tracked", impulse: "Impulse buyer", essentials: "Essentials first", mix: "Mix of both" } },
  saving_habit: { label: "Extra cash goes to", icon: "🐷", map: { save: "Savings goal", experiences: "Experiences", stuff: "New stuff", share: "Friends & family" } },
  money_stressor: { label: "Money stressor", icon: "😰", map: { tuition: "Tuition", food: "Daily food", rent: "Rent / hostel", fun: "Going out", none: "Nothing major" } },
  sleep: { label: "Sleep pattern", icon: "🌙", map: { "7-8h": "Solid 7–8h", "<6h": "Less than 6h", irregular: "Irregular", late: "Late but enough" } },
  energy_peak: { label: "Energy peak", icon: "⚡", map: { morning: "Mornings", afternoon: "Afternoons", evening: "Evenings", night: "Late night" } },
  self_care_primary: { label: "Self-care", icon: "🌿", map: { workout: "Workout", music: "Music", walk: "Walking", social: "Friends", meditate: "Meditate" } },
};

export default function Profile() {
  const nav = useNavigate();
  const { logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [income, setIncome] = useState("");
  const [showEditPattern, setShowEditPattern] = useState(false);

  const load = async () => {
    const { data } = await api.get("/profile");
    setProfile(data);
    setName(data.name);
    setIncome(String(data.monthly_income || 0));
  };
  useEffect(() => { load(); }, []);

  const saveBasic = async () => {
    await api.patch("/profile", { name: name.trim(), monthly_income: parseFloat(income) || 0 });
    setEditing(false);
    await load();
  };

  if (!profile) return null;

  if (showEditPattern) {
    return <Onboarding initial={profile} isEdit onDone={() => { setShowEditPattern(false); load(); }} />;
  }

  const pattern = profile.your_pattern || {};
  const hasPattern = Object.keys(pattern).length > 0;
  const initial = profile.avatar_initial || profile.name?.[0] || "A";

  return (
    <div data-domain="helper" className="flex-1 overflow-auto scroll-area pb-4 bg-[#FAFAFA]" data-testid="profile-screen">
      <div className="bdy-gradient text-white px-5 pt-6 pb-10 rounded-b-3xl">
        <div className="flex items-center justify-between">
          <button onClick={() => nav(-1)} data-testid="profile-back-btn" className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <span className="font-display font-bold text-base">Your Profile</span>
          <div className="w-9" />
        </div>

        <div className="flex flex-col items-center mt-5">
          <div className="w-20 h-20 rounded-full bg-white/20 ring-4 ring-white/30 flex items-center justify-center text-3xl font-display font-bold">
            {initial}
          </div>
          {editing ? (
            <input
              data-testid="profile-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-3 bg-white/20 placeholder-white/60 text-white text-xl font-display font-bold rounded-xl px-3 py-1.5 outline-none focus:bg-white/30 text-center"
            />
          ) : (
            <div className="mt-3 font-display font-bold text-2xl">{profile.name}</div>
          )}
          <div className="mt-1 flex items-center gap-3 text-xs text-white/80">
            <span className="flex items-center gap-1"><Flame className="w-3.5 h-3.5 text-orange-300" /> {profile.streak_days} day streak</span>
            <span>·</span>
            <span>₹{(profile.monthly_income || 0).toLocaleString()}/mo</span>
          </div>
        </div>
      </div>

      <div className="px-5 -mt-5 space-y-3">
        <Card>
          <div className="flex justify-between items-center">
            <h3 className="font-display font-bold text-base">Account</h3>
            {editing ? (
              <div className="flex gap-1">
                <button onClick={saveBasic} data-testid="profile-save-btn" className="w-8 h-8 rounded-lg bdy-bg text-white flex items-center justify-center">
                  <Check className="w-4 h-4" />
                </button>
                <button onClick={() => { setEditing(false); setName(profile.name); setIncome(String(profile.monthly_income)); }}
                  className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button onClick={() => setEditing(true)} data-testid="profile-edit-btn"
                className="text-xs font-semibold bdy-text flex items-center gap-1">
                <Pencil className="w-3.5 h-3.5" /> Edit
              </button>
            )}
          </div>

          <div className="mt-3 space-y-2">
            <Row icon="🧑" label="Display name">
              {editing ? (
                <input
                  data-testid="profile-name-input"
                  value={name} onChange={(e) => setName(e.target.value)}
                  className="bg-slate-50 rounded-lg px-2.5 py-1 text-sm w-32 border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
                />
              ) : (
                <span className="text-sm font-semibold">{profile.name}</span>
              )}
            </Row>
            <Row icon="💰" label="Monthly income">
              {editing ? (
                <input
                  data-testid="profile-income-input"
                  type="number" value={income} onChange={(e) => setIncome(e.target.value)}
                  className="bg-slate-50 rounded-lg px-2.5 py-1 text-sm w-28 border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
                />
              ) : (
                <span className="text-sm font-semibold">₹{(profile.monthly_income || 0).toLocaleString()}</span>
              )}
            </Row>
            <Row icon="🔥" label="Check-in streak">
              <span className="text-sm font-semibold">{profile.streak_days} days</span>
            </Row>
          </div>
        </Card>

        <GamificationCard />

        <Card>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-display font-bold text-base">Your Pattern</h3>
              <p className="text-xs text-slate-500">How money & wellness usually work for you.</p>
            </div>
            <button
              onClick={() => setShowEditPattern(true)}
              data-testid="edit-pattern-btn"
              className="text-xs font-semibold bdy-text flex items-center gap-1"
            >
              <Pencil className="w-3.5 h-3.5" /> {hasPattern ? "Edit" : "Set up"}
            </button>
          </div>

          {hasPattern ? (
            <div className="mt-3 grid grid-cols-2 gap-2" data-testid="pattern-grid">
              {Object.entries(PATTERN_LABELS).map(([k, meta]) => {
                const v = pattern[k];
                if (!v) return null;
                return (
                  <div key={k} className="p-2.5 rounded-xl bg-slate-50">
                    <div className="text-[10px] font-semibold uppercase text-slate-500 flex items-center gap-1">
                      <span>{meta.icon}</span> {meta.label}
                    </div>
                    <div className="text-sm font-display font-bold mt-0.5">{meta.map[v] || v}</div>
                  </div>
                );
              })}
              {pattern.stress_baseline != null && (
                <div className="p-2.5 rounded-xl bg-slate-50 col-span-2">
                  <div className="text-[10px] font-semibold uppercase text-slate-500">⚡ Stress baseline</div>
                  <div className="mt-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bdy-bg" style={{ width: `${pattern.stress_baseline * 10}%` }} />
                  </div>
                  <div className="text-[11px] text-slate-600 mt-0.5">{pattern.stress_baseline}/10</div>
                </div>
              )}
            </div>
          ) : (
            <InsightCard icon={Sparkles} title="Tell us about you" text="Set up your pattern so each buddy gives advice that actually fits your life." />
          )}
        </Card>

        <Card>
          <h3 className="font-display font-bold text-sm">Settings</h3>
          <button
            onClick={async () => {
              if (!window.confirm("Re-run the Your-Pattern onboarding? Your existing pattern stays until you save the new one.")) return;
              await api.patch("/profile", { onboarded: false });
              window.location.href = "/";
            }}
            data-testid="rerun-onboarding-btn"
            className="mt-3 w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 active:scale-[0.99]"
          >
            <div className="flex items-center gap-2">
              <span>🔄</span>
              <span className="text-sm font-semibold">Re-run onboarding</span>
            </div>
            <span className="text-xs text-slate-500">Edit name + pattern + goals</span>
          </button>
          <button
            onClick={() => setShowEditPattern(true)}
            data-testid="settings-edit-pattern-btn"
            className="mt-2 w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 active:scale-[0.99]"
          >
            <div className="flex items-center gap-2">
              <span>✨</span>
              <span className="text-sm font-semibold">Edit Your Pattern only</span>
            </div>
            <Pencil className="w-3.5 h-3.5 text-slate-500" />
          </button>
          <button
            onClick={() => {
              if (!window.confirm("Are you sure you want to log out?")) return;
              logout();
              nav("/login", { replace: true });
            }}
            data-testid="logout-btn"
            className="mt-2 w-full flex items-center justify-between p-3 rounded-xl bg-red-50 hover:bg-red-100 active:scale-[0.99]"
            aria-label="Log out"
          >
            <div className="flex items-center gap-2">
              <LogOut className="w-4 h-4 text-red-500" />
              <span className="text-sm font-semibold text-red-600">Log out</span>
            </div>
          </button>
        </Card>

        <Card>
          <h3 className="font-display font-bold text-sm">About</h3>
          <ul className="mt-2 text-xs text-slate-600 space-y-1">
            <li>· PocketBuddy v0.1 — student super-app</li>
            <li>· Made for students by Emergent</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

function GamificationCard() {
  const { status, achievements, loading, error } = useGamification();

  if (loading) {
    return (
      <Card>
        <h3 className="font-display font-bold text-base">Gamification</h3>
        <div className="mt-3 flex items-center justify-center py-4">
          <div className="w-5 h-5 border-2 border-slate-300 border-t-[color:var(--bdy)] rounded-full animate-spin" />
        </div>
      </Card>
    );
  }

  if (error || !status) {
    return (
      <Card>
        <h3 className="font-display font-bold text-base">Gamification</h3>
        <p className="mt-2 text-xs text-slate-500">Unable to load gamification data.</p>
      </Card>
    );
  }

  // Combine earned and available achievements for display
  const allBadges = [
    ...(achievements?.earned || []).map((a) => ({ ...a, earned: true })),
    ...(achievements?.available || []).map((a) => ({ ...a, earned: false })),
  ];

  return (
    <Card>
      <h3 className="font-display font-bold text-base">Gamification</h3>

      <div className="mt-3 space-y-3">
        {/* XP Progress */}
        <XPProgressBar
          totalXp={status.total_xp}
          level={status.level}
          xpToNextLevel={status.xp_to_next_level}
        />

        {/* Streak */}
        <StreakCounter streakDays={status.streak_days} />

        {/* Badges grid */}
        {allBadges.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Badges</p>
            <div className="grid grid-cols-3 gap-2">
              {allBadges.map((badge) => (
                <AchievementBadge key={badge.id || badge.name} achievement={badge} />
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

const Row = ({ icon, label, value, children }) => (
  <div className="flex items-center justify-between py-1.5">
    <div className="flex items-center gap-2 text-sm text-slate-700">
      <span>{icon}</span>
      <span className="font-semibold">{label}</span>
    </div>
    {children ?? <span className="text-sm font-semibold">{value}</span>}
  </div>
);
