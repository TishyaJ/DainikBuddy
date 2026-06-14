import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Tasks } from "../components/Tasks";
import { Plus, Target, Sparkles, TrendingUp, AlertTriangle, RefreshCw, CheckCircle2, Moon, Info } from "lucide-react";
import { VoiceInputButton } from "../components/VoiceInputButton";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, Radar } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { useGamification } from "../context/GamificationContext";
import PageTransition from "../components/PageTransition";
import { SkeletonCard } from "../components/Skeleton";

const MOODS = [
  { key: "great", emoji: "😄", label: "Great" },
  { key: "good", emoji: "🙂", label: "Good" },
  { key: "okay", emoji: "😐", label: "Okay" },
  { key: "bad", emoji: "🙁", label: "Bad" },
  { key: "terrible", emoji: "😢", label: "Tough" },
];

const Slider = ({ label, value, onChange, testid }) => (
  <div className="mt-3">
    <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
      <span>{label}</span>
      <span className="text-[color:var(--bdy)]">{value}%</span>
    </div>
    <input
      type="range" min="0" max="100" value={value}
      onChange={(e) => onChange(parseInt(e.target.value))}
      className="bdy-slider"
      style={{ "--val": `${value}%` }}
      data-testid={testid}
      aria-label={`${label} level, ${value} percent`}
    />
  </div>
);

const Mood = () => {
  const [mood, setMood] = useState("good");
  const [energy, setEnergy] = useState(70);
  const [stress, setStress] = useState(40);
  const [motivation, setMotivation] = useState(75);
  const [saved, setSaved] = useState(false);
  const save = async () => {
    await api.post("/mood", { mood, energy, stress, motivation });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };
  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">How are you feeling?</h3>
      <div className="flex justify-between mt-3" data-testid="mood-row">
        {MOODS.map((m) => (
          <button
            key={m.key} onClick={() => setMood(m.key)}
            data-testid={`mood-${m.key}`}
            aria-label={`Set mood to ${m.label}`}
            className={`flex flex-col items-center transition-transform ${mood === m.key ? "scale-110" : "opacity-60"}`}
          >
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl ${mood === m.key ? "bdy-soft ring-2 ring-[color:var(--bdy)]" : "bg-slate-100"}`}>
              {m.emoji}
            </div>
            <span className="text-[10px] mt-1 font-semibold text-slate-600">{m.label}</span>
          </button>
        ))}
      </div>
      <Slider label="Energy" value={energy} onChange={setEnergy} testid="slider-energy" />
      <Slider label="Stress" value={stress} onChange={setStress} testid="slider-stress" />
      <Slider label="Motivation" value={motivation} onChange={setMotivation} testid="slider-motivation" />
      <button
        onClick={save}
        data-testid="save-mood-btn"
        aria-label="Log mood check-in"
        className="w-full mt-4 bdy-bg text-white font-semibold py-3 rounded-xl active:scale-95 transition"
      >
        {saved ? "Saved ✓" : "Log Check-In"}
      </button>
      <InsightCard
        icon={Sparkles}
        title="AI Check-In Note"
        text={stress > 60 ? "Your stress is elevated. A 3-min breathing exercise could help right now." : "You're tracking well. Keep your evening routine consistent."}
      />
    </Card>
  );
};

const Expense = () => {
  const [amount, setAmount] = useState("");
  const [merchant, setMerchant] = useState("");
  const [category, setCategory] = useState("food");
  const [list, setList] = useState([]);
  const load = async () => setList((await api.get("/expenses?limit=10")).data);
  useEffect(() => { load(); }, []);
  const save = async () => {
    if (!amount) return;
    await api.post("/expenses", { amount: parseFloat(amount), category, merchant });
    setAmount(""); setMerchant(""); load();
  };
  const cats = ["food", "transport", "entertainment", "education", "misc"];
  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">Log an Expense</h3>
      <div className="grid grid-cols-2 gap-2 mt-3">
        <input data-testid="exp-amount" type="number" placeholder="₹ Amount" value={amount}
          onChange={(e) => setAmount(e.target.value)}
          aria-label="Enter expense amount"
          className="bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
        <input data-testid="exp-merchant" placeholder="Where?" value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
          aria-label="Enter merchant or location"
          className="bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
      </div>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {cats.map((c) => (
          <button key={c} data-testid={`cat-${c}`} onClick={() => setCategory(c)}
            aria-label={`Select category ${c}`}
            className={`px-3 py-1 rounded-full text-[11px] font-semibold capitalize ${category === c ? "bdy-bg text-white" : "bg-slate-100 text-slate-600"}`}>
            {c}
          </button>
        ))}
      </div>
      <div className="mt-3">
        <button onClick={save} data-testid="save-expense-btn" aria-label="Add expense" className="w-full bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 active:scale-95">
          <Plus className="w-4 h-4" /> Add Expense
        </button>
      </div>
      <div className="mt-4">
        <div className="text-xs font-semibold text-slate-500 mb-2">TODAY'S LOG</div>
        <div className="space-y-1.5" data-testid="expense-list">
          {list.slice(0, 5).map((e) => (
            <div key={e.id} className="flex justify-between text-sm py-1.5 border-b border-slate-100">
              <span className="text-slate-700">{e.merchant || e.category}</span>
              <span className="font-semibold">₹{e.amount}</span>
            </div>
          ))}
          {list.length === 0 && <p className="text-xs text-slate-400">No expenses yet.</p>}
        </div>
      </div>
    </Card>
  );
};

const MAX_JOURNAL_CHARS = 5000;

const Journal = () => {
  const [text, setText] = useState("");
  const [list, setList] = useState([]);
  const [weekly, setWeekly] = useState([]);
  const [voiceError, setVoiceError] = useState("");
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const textBeforeVoiceRef = React.useRef("");

  const load = async () => {
    setList((await api.get("/journal?limit=5")).data);
    setWeekly((await api.get("/journal/weekly")).data);
  };
  useEffect(() => { load(); }, []);
  const save = async () => {
    if (!text.trim()) return;
    await api.post("/journal", { text });
    setText(""); load();
  };

  const handleVoiceTranscript = useCallback((transcript) => {
    setVoiceError("");
    setIsTranscribing(true);
    setInterimTranscript(transcript);

    // Append transcript to text that existed before voice started, respecting 5000 char cap
    const baseText = textBeforeVoiceRef.current;
    const separator = baseText && !baseText.endsWith(" ") && !baseText.endsWith("\n") ? " " : "";
    const available = MAX_JOURNAL_CHARS - baseText.length - separator.length;
    const truncatedTranscript = transcript.slice(0, Math.max(0, available));
    setText(baseText + separator + truncatedTranscript);
  }, []);

  const handleVoiceError = useCallback((message) => {
    setVoiceError(message);
    setIsTranscribing(false);
    setInterimTranscript("");
    // Clear error after 5 seconds
    setTimeout(() => setVoiceError(""), 5000);
  }, []);

  const handleVoiceEnd = useCallback(() => {
    setIsTranscribing(false);
    setInterimTranscript("");
  }, []);

  // Track base text when voice recording starts (via the button click)
  const handleVoiceStart = useCallback(() => {
    textBeforeVoiceRef.current = text;
  }, [text]);

  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">Daily Journal</h3>
      <textarea
        data-testid="journal-textarea"
        value={text} onChange={(e) => setText(e.target.value.slice(0, MAX_JOURNAL_CHARS))}
        placeholder="What's on your mind today?" rows={4}
        maxLength={MAX_JOURNAL_CHARS}
        aria-label="Write your journal entry"
        className="w-full mt-3 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)] resize-none"
      />
      <div className="flex justify-between items-center mt-1 mb-1">
        <span className="text-[10px] text-slate-400">{text.length}/{MAX_JOURNAL_CHARS}</span>
        {isTranscribing && (
          <span className="text-[10px] text-red-500 font-medium animate-pulse">● Recording...</span>
        )}
      </div>
      {voiceError && (
        <div data-testid="voice-error-message" className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-2">
          {voiceError}
        </div>
      )}
      <div className="grid grid-cols-2 gap-2 mt-1">
        <button onClick={save} data-testid="save-journal-btn" aria-label="Save journal entry" className="bdy-bg text-white font-semibold py-2.5 rounded-xl active:scale-95">
          Save
        </button>
        <VoiceInputButton
          onTranscript={handleVoiceTranscript}
          onError={handleVoiceError}
          onEnd={handleVoiceEnd}
          onStart={handleVoiceStart}
          disabled={text.length >= MAX_JOURNAL_CHARS}
          className=""
        />
      </div>
      <div className="mt-4">
        <div className="text-xs font-semibold text-slate-500 mb-2">WEEKLY SENTIMENT</div>
        <div className="h-24" data-testid="weekly-sentiment-chart">
          <ResponsiveContainer>
            <BarChart data={weekly}>
              <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={10} />
              <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                {weekly.map((d, i) => (
                  <Cell key={i} fill={d.score > 0 ? "var(--bdy)" : d.score < 0 ? "#F87171" : "#CBD5E1"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="mt-2 space-y-1.5">
        {list.slice(0, 3).map((j) => (
          <div key={j.id} className="text-xs p-2 bg-slate-50 rounded-lg">
            <span className={`font-semibold mr-2 ${j.sentiment === "positive" ? "text-emerald-600" : j.sentiment === "negative" ? "text-rose-600" : "text-slate-500"}`}>
              {j.sentiment}
            </span>
            <span className="text-slate-700 line-clamp-2">{j.text}</span>
          </div>
        ))}
        {list.length === 0 && <p className="text-xs text-slate-400">No journal entries yet. Write your first thought above.</p>}
      </div>
    </Card>
  );
};

const Goals = () => {
  const [goals, setGoals] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [updating, setUpdating] = useState(null);

  const loadGoals = async () => {
    try {
      const r = await api.get("/goals");
      setGoals(r.data);
    } catch { /* silently fail */ }
  };

  useEffect(() => { loadGoals(); }, []);

  const handleProgressChange = async (goalId, newValue, target) => {
    setUpdating(goalId);
    try {
      await api.patch(`/goals/${goalId}`, { current: newValue });
      setGoals((prev) => prev.map((g) => g.id === goalId ? { ...g, current: newValue } : g));
    } catch { /* silently fail */ } finally {
      setUpdating(null);
    }
  };

  const handleArchive = async (goalId) => {
    try {
      await api.patch(`/goals/${goalId}`, { status: "done" });
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
    } catch { /* silently fail */ }
  };

  const handleDelete = async (goalId) => {
    if (!window.confirm("Delete this goal permanently?")) return;
    try {
      await api.delete(`/goals/${goalId}`);
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
    } catch { /* silently fail */ }
  };

  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">Goal Review</h3>
      <div className="space-y-3 mt-3" data-testid="goals-list">
        {goals.map((g) => {
          const pct = g.target > 0 ? Math.min(100, Math.round((g.current / g.target) * 100)) : 0;
          const isExpanded = expandedId === g.id;
          return (
            <div key={g.id} className="p-3 rounded-xl bg-slate-50">
              <div
                className="flex justify-between items-center cursor-pointer"
                onClick={() => setExpandedId(isExpanded ? null : g.id)}
                data-testid={`goal-row-${g.id}`}
                aria-label={`Update progress for ${g.title}`}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setExpandedId(isExpanded ? null : g.id); }}
              >
                <div className="flex items-center gap-2">
                  <Target className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-sm font-semibold">{g.title}</span>
                </div>
                <span className={`text-xs font-bold ${g.status === "missed" ? "text-rose-600" : "text-emerald-600"}`}>
                  {pct}%
                </span>
              </div>
              <div className="h-2 mt-2 rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bdy-bg transition-all" style={{ width: `${pct}%` }} />
              </div>
              {isExpanded && (
                <div className="mt-3 pt-2 border-t border-slate-200">
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Progress: {g.current} / {g.target} {g.unit || ""}</span>
                    <span className="bdy-text font-semibold">{pct}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max={g.target}
                    step={g.target >= 100 ? 1 : 0.5}
                    value={g.current}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      setGoals((prev) => prev.map((goal) => goal.id === g.id ? { ...goal, current: val } : goal));
                    }}
                    onMouseUp={(e) => handleProgressChange(g.id, parseFloat(e.target.value), g.target)}
                    onTouchEnd={(e) => handleProgressChange(g.id, parseFloat(e.target.value), g.target)}
                    className="bdy-slider w-full"
                    style={{ "--val": `${pct}%` }}
                    data-testid={`goal-slider-${g.id}`}
                    aria-label={`Set progress for ${g.title}, currently ${g.current} of ${g.target}`}
                    disabled={updating === g.id}
                  />
                  {updating === g.id && <p className="text-[10px] text-slate-400 mt-1">Saving…</p>}
                </div>
              )}
              {pct >= 100 && (
                <div className="mt-2 flex gap-2" data-testid={`goal-completion-actions-${g.id}`}>
                  <button
                    onClick={() => handleArchive(g.id)}
                    data-testid={`goal-archive-${g.id}`}
                    aria-label={`Archive completed goal ${g.title}`}
                    className="flex-1 py-1.5 rounded-lg text-xs font-semibold text-white bdy-bg active:scale-95 transition"
                  >
                    Archive
                  </button>
                  <button
                    onClick={() => handleDelete(g.id)}
                    data-testid={`goal-delete-${g.id}`}
                    aria-label={`Delete goal ${g.title}`}
                    className="flex-1 py-1.5 rounded-lg text-xs font-semibold text-rose-600 bg-rose-50 border border-rose-200 active:scale-95 transition"
                  >
                    Delete
                  </button>
                </div>
              )}
              {g.status === "missed" && (
                <p className="text-[11px] text-rose-600 mt-1">⚠ Behind schedule — try a smaller daily step.</p>
              )}
            </div>
          );
        })}
        {goals.length === 0 && <p className="text-xs text-slate-400 py-3">No goals yet. Create one to start tracking progress.</p>}
      </div>
      {goals.length > 0 && goals.some(g => g.status === "missed") && (
        <InsightCard icon={Sparkles} title="AI Recommendation" text="Some goals are behind schedule. Try breaking them into smaller daily steps to build momentum." />
      )}
    </Card>
  );
};

const Sleep = () => {
  const [hours, setHours] = useState("7");
  const [quality, setQuality] = useState("good");
  const [saved, setSaved] = useState(false);
  const [weekly, setWeekly] = useState([]);

  const load = async () => {
    try {
      const res = await api.get("/sleep/weekly");
      setWeekly(res.data);
    } catch { /* graceful degradation */ }
  };
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!hours || parseFloat(hours) <= 0) return;
    await api.post("/sleep", {
      hours: parseFloat(hours),
      quality,
      date: new Date().toISOString(),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
    load();
  };

  const qualities = ["good", "ok", "poor"];

  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">Log Sleep</h3>
      <p className="text-xs text-slate-500 mt-0.5">How did you sleep last night?</p>

      <div className="mt-3">
        <label className="text-xs font-semibold text-slate-600">Hours Slept</label>
        <input
          data-testid="sleep-hours"
          type="number"
          min="0"
          max="24"
          step="0.5"
          value={hours}
          onChange={(e) => setHours(e.target.value)}
          aria-label="Enter hours slept"
          className="w-full mt-1 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
          placeholder="e.g. 7.5"
        />
      </div>

      <div className="mt-3">
        <label className="text-xs font-semibold text-slate-600">Sleep Quality</label>
        <div className="flex gap-2 mt-1.5">
          {qualities.map((q) => (
            <button
              key={q}
              data-testid={`sleep-quality-${q}`}
              onClick={() => setQuality(q)}
              aria-label={`Set sleep quality to ${q}`}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold capitalize transition ${quality === q
                ? "bdy-bg text-white"
                : "bg-slate-100 text-slate-600"
                }`}
            >
              {q === "good" ? "😴 Good" : q === "ok" ? "😐 OK" : "😫 Poor"}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={save}
        data-testid="save-sleep-btn"
        aria-label="Log sleep entry"
        className="w-full mt-4 bdy-bg text-white font-semibold py-3 rounded-xl active:scale-95 transition"
      >
        {saved ? "Saved ✓" : "Log Sleep"}
      </button>

      <div className="mt-4">
        <div className="text-xs font-semibold text-slate-500 mb-2">THIS WEEK</div>
        <div className="space-y-1.5" data-testid="sleep-list">
          {weekly.map((s, i) => (
            <div key={i} className="flex justify-between items-center text-sm py-1.5 border-b border-slate-100">
              <span className="text-slate-700 font-medium">{s.day}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs capitalize text-slate-500">{s.quality}</span>
                <span className="font-semibold">{s.hours}h</span>
              </div>
            </div>
          ))}
          {weekly.length === 0 && <p className="text-xs text-slate-400">No sleep entries yet. Log your first night above.</p>}
        </div>
      </div>

      <InsightCard
        icon={Moon}
        title="Sleep Tip"
        text="Aim for 7–9 hours of consistent sleep. Log daily to track your patterns over time."
      />
    </Card>
  );
};

const Summary = () => {
  const [lb, setLb] = useState(null);
  const [lbError, setLbError] = useState(false);
  const [insights, setInsights] = useState([]);
  const [insightsError, setInsightsError] = useState(false);
  const [plan, setPlan] = useState(null);
  const [planError, setPlanError] = useState(false);
  const [checkedActions, setCheckedActions] = useState([false, false, false]);
  const [celebrating, setCelebrating] = useState(false);
  const [xpAwarded, setXpAwarded] = useState(false);
  const { refresh: refreshGamification } = useGamification();

  const fetchLifeBalance = useCallback(async () => {
    try {
      setLbError(false);
      const res = await api.get("/life-balance");
      setLb(res.data);
    } catch {
      setLbError(true);
    }
  }, []);

  const fetchInsights = useCallback(async () => {
    try {
      setInsightsError(false);
      const res = await api.get("/insights/daily");
      setInsights(Array.isArray(res.data) ? res.data : res.data?.insights || []);
    } catch {
      setInsightsError(true);
    }
  }, []);

  const fetchPlan = useCallback(async () => {
    try {
      setPlanError(false);
      const res = await api.get("/insights/tomorrow-plan");
      setPlan(res.data);
    } catch {
      setPlanError(true);
    }
  }, []);

  useEffect(() => {
    fetchLifeBalance();
    fetchInsights();
    fetchPlan();
  }, [fetchLifeBalance, fetchInsights, fetchPlan]);

  const isAfter8PM = new Date().getHours() >= 20;

  const handleActionToggle = async (index) => {
    if (xpAwarded) return;
    const updated = [...checkedActions];
    updated[index] = !updated[index];
    setCheckedActions(updated);

    if (updated.every(Boolean)) {
      try {
        const res = await api.post("/insights/complete-actions");
        if (res.data.success) {
          setCelebrating(true);
          setXpAwarded(true);
          refreshGamification();
          setTimeout(() => setCelebrating(false), 3000);
        }
      } catch {
        // Revert if API fails
        updated[index] = !updated[index];
        setCheckedActions([...updated]);
      }
    }
  };

  const radarData = lb?.domains?.map((d) => ({
    domain: d.name,
    score: d.score,
    fullMark: 100,
  })) || [];

  const lowDomains = lb?.domains?.filter((d) => d.score < 40) || [];
  const missingDomains = lb?.domains?.filter((d) => d.score === 0) || [];

  return (
    <div className="mx-5 mt-4 space-y-3">
      {/* Celebration Animation Overlay */}
      <AnimatePresence>
        {celebrating && (
          <motion.div
            data-testid="celebration-overlay"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.4 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          >
            <motion.div
              initial={{ scale: 0.5, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 15 }}
              className="bg-white rounded-3xl p-8 text-center shadow-2xl max-w-[300px]"
            >
              <motion.div
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ repeat: Infinity, duration: 1.2 }}
                className="text-6xl mb-3"
              >
                🎉
              </motion.div>
              <h3 className="font-display font-bold text-xl text-slate-900">All Done!</h3>
              <p className="text-sm text-slate-600 mt-1">You completed tomorrow's plan</p>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="mt-3 inline-flex items-center gap-1 px-4 py-2 rounded-full bdy-bg text-white font-bold text-lg"
              >
                +25 XP ⭐
              </motion.div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Partial Data Indicator */}
      {lb && lb.partial_data && (
        <div data-testid="partial-data-indicator" className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span className="text-xs text-amber-700 font-medium">
            Limited data available ({lb.days_used ? Math.min(...Object.values(lb.days_used)) : "< 7"} days). Scores will improve with more entries.
          </span>
        </div>
      )}

      {/* Life-Balance Radar Chart */}
      {lbError ? (
        <Card data-testid="lb-error">
          <div className="flex flex-col items-center py-4 gap-2">
            <AlertTriangle className="w-6 h-6 text-rose-500" />
            <p className="text-sm text-slate-600">Could not load life-balance data</p>
            <button
              onClick={fetchLifeBalance}
              data-testid="lb-retry-btn"
              aria-label="Retry loading life-balance data"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        </Card>
      ) : (
        <Card data-testid="life-balance-radar">
          <h3 className="font-display font-bold text-lg">Life Balance</h3>
          <p className="text-xs text-slate-500 mt-0.5">5-domain overview (last 7 days)</p>
          {lb && radarData.length > 0 && (
            <div className="mt-3 flex justify-center" data-testid="radar-chart-container">
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis
                    dataKey="domain"
                    tick={{ fontSize: 11, fill: "#64748b", fontWeight: 600 }}
                  />
                  <Radar
                    name="Score"
                    dataKey="score"
                    stroke="var(--bdy)"
                    fill="var(--bdy)"
                    fillOpacity={0.25}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
          {!lb && (
            <div className="h-[220px] flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-slate-300 border-t-[color:var(--bdy)] rounded-full animate-spin" />
            </div>
          )}
          {/* Low domain highlights */}
          {lowDomains.length > 0 && (
            <div className="mt-3 space-y-2" data-testid="low-domains">
              {lowDomains.map((d) => (
                <div
                  key={d.name}
                  className="flex items-start gap-2 p-2.5 rounded-xl bg-rose-50 border border-rose-200"
                  data-testid={`low-domain-${d.name.toLowerCase()}`}
                >
                  <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-rose-700">{d.name}</span>
                      <span className="text-xs font-semibold text-rose-500">{d.score}/100</span>
                    </div>
                    {d.actionable_step && (
                      <p className="text-xs text-rose-600 mt-0.5 leading-relaxed">{d.actionable_step}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          {/* Missing domain data encouragement */}
          {missingDomains.length > 0 && (
            <div className="mt-3 p-2.5 rounded-xl bg-amber-50 border border-amber-100" data-testid="summary-missing-domains">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-amber-700">Some domains need your input</p>
                  <p className="text-[11px] text-amber-600 mt-0.5">
                    Start logging {missingDomains.map((d) => d.name.toLowerCase()).join(", ")} data to see your full score. The more you log, the better your insights!
                  </p>
                </div>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* AI Insight Cards */}
      {insightsError ? (
        <Card data-testid="insights-error">
          <div className="flex flex-col items-center py-4 gap-2">
            <AlertTriangle className="w-6 h-6 text-rose-500" />
            <p className="text-sm text-slate-600">Could not load daily insights</p>
            <button
              onClick={fetchInsights}
              data-testid="insights-retry-btn"
              aria-label="Retry loading daily insights"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        </Card>
      ) : insights.length > 0 ? (
        <div className="space-y-2" data-testid="daily-insights">
          {insights.map((i, idx) => (
            <InsightCard key={idx} icon={Sparkles} title={i.title} text={i.detail} />
          ))}
        </div>
      ) : (
        <Card data-testid="insights-empty">
          <div className="flex items-start gap-2 py-2">
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500">
              No insights yet. Log your mood, expenses, and sleep to get personalized AI recommendations based on your data.
            </p>
          </div>
        </Card>
      )}

      {/* Tomorrow's Plan Card (visible after 8 PM) */}
      {isAfter8PM && !planError && plan?.available && plan.actions?.length > 0 && (
        <Card className="bdy-gradient text-white" data-testid="tomorrow-plan-card">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            <h3 className="font-display font-bold text-lg">Tomorrow's Plan</h3>
          </div>
          <p className="text-xs text-white/70 mt-1">3 actions based on your lowest-scoring domains</p>
          <div className="mt-3 space-y-2">
            {plan.actions.map((action, idx) => (
              <label
                key={idx}
                data-testid={`plan-action-${idx}`}
                className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition ${checkedActions[idx] ? "bg-white/25" : "bg-white/10"
                  } ${xpAwarded ? "opacity-70 pointer-events-none" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={checkedActions[idx]}
                  onChange={() => handleActionToggle(idx)}
                  className="mt-0.5 w-4 h-4 rounded accent-white"
                  data-testid={`plan-checkbox-${idx}`}
                />
                <div className="flex-1">
                  <div className="text-sm font-semibold">{action.action}</div>
                  <div className="text-[10px] text-white/70 mt-0.5 uppercase font-semibold">{action.domain}</div>
                </div>
              </label>
            ))}
          </div>
          {xpAwarded && (
            <div className="mt-3 flex items-center gap-2 text-sm font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>+25 XP earned!</span>
            </div>
          )}
        </Card>
      )}

      {/* Tomorrow's Plan Error */}
      {isAfter8PM && planError && (
        <Card data-testid="plan-error">
          <div className="flex flex-col items-center py-4 gap-2">
            <AlertTriangle className="w-6 h-6 text-rose-500" />
            <p className="text-sm text-slate-600">Could not load tomorrow's plan</p>
            <button
              onClick={fetchPlan}
              data-testid="plan-retry-btn"
              aria-label="Retry loading tomorrow's plan"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        </Card>
      )}
    </div>
  );
};

const TABS = [
  { key: "mood", label: "Mood", C: Mood },
  { key: "tasks", label: "Tasks", C: Tasks },
  { key: "expense", label: "Expense", C: Expense },
  { key: "journal", label: "Journal", C: Journal },
  { key: "sleep", label: "Sleep", C: Sleep },
  { key: "goals", label: "Goals", C: Goals },
  { key: "summary", label: "AI Summary", C: Summary },
];

export default function DailyHub() {
  const [tab, setTab] = useState("mood");
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const nav = useNavigate();
  useEffect(() => {
    api.get("/profile").then((r) => setProfile(r.data)).catch(() => setProfile({ name: "Friend" })).finally(() => setProfileLoading(false));
  }, []);
  const Active = TABS.find((t) => t.key === tab).C;

  if (profileLoading) {
    return (
      <div className="flex-1 overflow-auto scroll-area pb-4 px-5 pt-6 space-y-3">
        <SkeletonCard lines={2} />
        <SkeletonCard lines={4} />
      </div>
    );
  }

  return (
    <PageTransition className="flex-1 overflow-auto scroll-area pb-4">
      <Header title={`Good morning, ${profile?.name || "Friend"} ☀️`} subtitle="Here's your snapshot for today" />
      <Card className="mx-5 -mt-2 bdy-gradient text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-white/80">DAILY CHECK-IN</div>
            <div className="font-display font-bold text-xl mt-0.5">You're doing great! 🌟</div>
            <p className="text-xs text-white/85 mt-1">Small steps, big changes.</p>
          </div>
          <div className="text-4xl">☁️</div>
        </div>
      </Card>
      {/* Trends quick-access button */}
      <div className="px-5 mt-3">
        <button
          onClick={() => nav("/trends")}
          data-testid="trends-nav-btn"
          className="w-full flex items-center justify-between px-4 py-3 rounded-2xl bg-white shadow-sm border border-slate-100 active:scale-[0.98] transition"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bdy-bg text-white flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-slate-900">View Trends</p>
              <p className="text-[11px] text-slate-500">Track spending, mood & habits</p>
            </div>
          </div>
          <span className="text-xs font-semibold text-[color:var(--bdy)]">→</span>
        </button>
      </div>
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="daily-tab" />
      <Active />
    </PageTransition>
  );
}
