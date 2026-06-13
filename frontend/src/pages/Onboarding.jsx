import React, { useState } from "react";
import { api } from "../lib/api";
import { Sparkles, ArrowRight, Wallet, Heart, ChevronLeft } from "lucide-react";

const Q_MONEY = [
  {
    key: "spending_style", label: "How do you usually spend?", emoji: "💸",
    options: [
      { v: "careful", t: "Carefully tracked" },
      { v: "impulse", t: "Often on impulse" },
      { v: "essentials", t: "Mostly essentials" },
      { v: "mix", t: "Mix of plan + spontaneous" },
    ],
  },
  {
    key: "saving_habit", label: "Extra cash usually goes to…", emoji: "🐷",
    options: [
      { v: "save", t: "Savings goal" },
      { v: "experiences", t: "Experiences" },
      { v: "stuff", t: "New stuff" },
      { v: "share", t: "Friends & family" },
    ],
  },
  {
    key: "money_stressor", label: "Biggest money stressor right now?", emoji: "😰",
    options: [
      { v: "tuition", t: "Tuition / fees" },
      { v: "food", t: "Daily food" },
      { v: "rent", t: "Rent / hostel" },
      { v: "fun", t: "Going out" },
      { v: "none", t: "Nothing really" },
    ],
  },
];

const Q_WELL = [
  {
    key: "sleep", label: "Your sleep most nights?", emoji: "🌙",
    options: [
      { v: "7-8h", t: "Solid 7–8h" },
      { v: "<6h", t: "Less than 6h" },
      { v: "irregular", t: "All over the place" },
      { v: "late", t: "Late but enough" },
    ],
  },
  {
    key: "energy_peak", label: "You feel most energetic…", emoji: "⚡",
    options: [
      { v: "morning", t: "Mornings" },
      { v: "afternoon", t: "Afternoons" },
      { v: "evening", t: "Evenings" },
      { v: "night", t: "Late night" },
    ],
  },
  {
    key: "self_care_primary", label: "Self-care looks like…", emoji: "🌿",
    options: [
      { v: "workout", t: "Workout" },
      { v: "music", t: "Music" },
      { v: "walk", t: "Walk outside" },
      { v: "social", t: "Friends" },
      { v: "meditate", t: "Meditate" },
    ],
  },
];

const PillRow = ({ value, options, onSelect, testidPrefix }) => (
  <div className="flex flex-wrap gap-2 mt-3">
    {options.map((o) => (
      <button
        key={o.v}
        onClick={() => onSelect(o.v)}
        data-testid={`${testidPrefix}-${o.v}`}
        className={`px-3.5 py-2 rounded-full text-sm font-semibold transition active:scale-95 ${
          value === o.v
            ? "bdy-bg text-white shadow-md"
            : "bg-white text-slate-700 border border-slate-200"
        }`}
      >
        {o.t}
      </button>
    ))}
  </div>
);

const Slider = ({ label, value, onChange, testid }) => (
  <div className="mt-4">
    <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
      <span>{label}</span>
      <span className="bdy-text">{value}/10</span>
    </div>
    <input
      type="range" min="1" max="10" value={value}
      onChange={(e) => onChange(parseInt(e.target.value))}
      className="bdy-slider" style={{ "--val": `${(value - 1) * 11.1}%` }}
      data-testid={testid}
    />
  </div>
);

const PRESET_GOALS = [
  "Study 3 hrs/day",
  "Sleep before 11pm",
  "Gym 3x/week",
  "Save ₹500/week",
  "Read 20 pages/day",
  "Drink 8 glasses water",
  "Meditate 10 min/day",
  "Walk 6,000 steps",
];

export default function Onboarding({ onDone, initial = {}, isEdit = false }) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState(initial.name || "Alex");
  const [pattern, setPattern] = useState({ stress_baseline: 5, ...(initial.your_pattern || {}) });
  const [goals, setGoals] = useState(initial.goals || []);
  const [customGoal, setCustomGoal] = useState("");
  const [saving, setSaving] = useState(false);

  const setKey = (k, v) => setPattern((p) => ({ ...p, [k]: v }));

  const toggleGoal = (g) => setGoals((arr) => arr.includes(g) ? arr.filter((x) => x !== g) : [...arr, g]);

  const save = async () => {
    setSaving(true);
    await api.post("/profile/onboard", { name, your_pattern: pattern, goals });
    setSaving(false);
    onDone?.();
  };

  const steps = [
    {
      title: "Welcome to PocketBuddy", sub: "A 60-second setup so we tailor everything to you.",
      domain: "helper", emoji: "✨",
      body: (
        <div className="mt-6">
          <label className="text-xs font-semibold text-slate-600">What should I call you?</label>
          <input
            data-testid="onb-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            className="w-full mt-2 bg-white rounded-xl px-3 py-3 text-base border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
          />
          <p className="text-xs text-slate-500 mt-3">You'll see this name and your saved pattern in your Profile. Edit anytime.</p>
        </div>
      ),
      canNext: () => name.trim().length > 0,
    },
    {
      title: "Money Pattern", sub: "Quick taps. No wrong answers.",
      domain: "finance", emoji: "💙", icon: Wallet,
      body: (
        <div>
          {Q_MONEY.map((q) => (
            <div key={q.key} className="mt-5">
              <div className="text-sm font-display font-bold text-slate-800">{q.emoji} {q.label}</div>
              <PillRow value={pattern[q.key]} options={q.options} onSelect={(v) => setKey(q.key, v)} testidPrefix={`onb-${q.key}`} />
            </div>
          ))}
        </div>
      ),
      canNext: () => Q_MONEY.every((q) => pattern[q.key]),
    },
    {
      title: "Wellbeing Pattern", sub: "Tell me how you usually feel.",
      domain: "wellness", emoji: "☁️", icon: Heart,
      body: (
        <div>
          {Q_WELL.map((q) => (
            <div key={q.key} className="mt-5">
              <div className="text-sm font-display font-bold text-slate-800">{q.emoji} {q.label}</div>
              <PillRow value={pattern[q.key]} options={q.options} onSelect={(v) => setKey(q.key, v)} testidPrefix={`onb-${q.key}`} />
            </div>
          ))}
          <Slider
            label="Typical stress baseline"
            value={pattern.stress_baseline || 5}
            onChange={(v) => setKey("stress_baseline", v)}
            testid="onb-stress-slider"
          />
        </div>
      ),
      canNext: () => Q_WELL.every((q) => pattern[q.key]) && pattern.stress_baseline != null,
    },
    {
      title: "Daily Goals", sub: "Pick 2–4 you want to track on your home page.",
      domain: "helper", emoji: "🎯",
      body: (
        <div>
          <div className="flex flex-wrap gap-2 mt-2">
            {PRESET_GOALS.map((g) => (
              <button key={g} onClick={() => toggleGoal(g)} data-testid={`onb-goal-${g.slice(0, 10)}`}
                className={`px-3 py-2 rounded-full text-xs font-semibold transition active:scale-95 ${
                  goals.includes(g) ? "bdy-bg text-white shadow-md" : "bg-white text-slate-700 border border-slate-200"
                }`}>
                {goals.includes(g) ? "✓ " : ""}{g}
              </button>
            ))}
          </div>
          <div className="mt-4">
            <label className="text-[11px] font-semibold text-slate-600">Add your own</label>
            <div className="flex gap-2 mt-1.5">
              <input
                data-testid="onb-custom-goal"
                value={customGoal}
                onChange={(e) => setCustomGoal(e.target.value)}
                placeholder="e.g. Finish thesis chapter"
                className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
              />
              <button
                onClick={() => { if (customGoal.trim()) { toggleGoal(customGoal.trim()); setCustomGoal(""); } }}
                data-testid="onb-add-custom-goal"
                className="px-3 py-2 rounded-xl bdy-bg text-white text-sm font-semibold"
              >
                Add
              </button>
            </div>
          </div>
          {goals.length > 0 && (
            <div className="mt-4 p-3 rounded-xl bg-slate-50">
              <div className="text-[10px] font-semibold uppercase text-slate-500">Selected</div>
              <div className="text-xs text-slate-700 mt-1">{goals.join(" · ")}</div>
            </div>
          )}
        </div>
      ),
      canNext: () => goals.length >= 1,
    },
  ];

  const cur = steps[step];

  return (
    <div data-domain={cur.domain} className="absolute inset-0 z-50 flex flex-col bg-[#FAFAFA]" data-testid="onboarding-screen">
      <div className="bdy-gradient text-white px-5 pt-7 pb-6 rounded-b-3xl">
        <div className="flex items-center justify-between">
          <button
            onClick={() => step > 0 ? setStep(step - 1) : onDone?.()}
            data-testid="onb-back"
            className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center disabled:opacity-30"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="text-[11px] font-semibold tracking-widest opacity-80">{step + 1} / {steps.length}</div>
          {isEdit ? (
            <button onClick={onDone} data-testid="onb-skip" className="text-xs font-semibold opacity-80">Cancel</button>
          ) : <div className="w-9" />}
        </div>
        <div className="mt-3 flex gap-1.5">
          {steps.map((_, i) => (
            <div key={i} className={`h-1 flex-1 rounded-full ${i <= step ? "bg-white" : "bg-white/30"}`} />
          ))}
        </div>
        <div className="mt-5">
          <div className="text-4xl">{cur.emoji}</div>
          <h1 className="font-display font-bold text-2xl mt-2 leading-tight">{cur.title}</h1>
          <p className="text-sm text-white/85 mt-1">{cur.sub}</p>
        </div>
      </div>

      <div className="flex-1 overflow-auto scroll-area px-5 py-5">
        {cur.body}
      </div>

      <div className="px-5 pb-5 pt-2 border-t border-slate-100 bg-white">
        {step < steps.length - 1 ? (
          <button
            onClick={() => setStep(step + 1)}
            disabled={!cur.canNext()}
            data-testid="onb-next"
            className="w-full bdy-bg text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50 active:scale-95"
          >
            Continue <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={save}
            disabled={!cur.canNext() || saving}
            data-testid="onb-save"
            className="w-full bdy-bg text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50 active:scale-95"
          >
            <Sparkles className="w-4 h-4" /> {saving ? "Saving..." : isEdit ? "Save Pattern" : "Save & Start"}
          </button>
        )}
      </div>
    </div>
  );
}
