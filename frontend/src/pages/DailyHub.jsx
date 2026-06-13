import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Tasks } from "../components/Tasks";
import { Smile, Frown, Meh, Heart, Zap, Mic, Camera, Plus, Target, Sparkles, TrendingUp, AlertTriangle, RefreshCw, CheckCircle2 } from "lucide-react";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, Radar } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { useGamification } from "../context/GamificationContext";

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
          className="bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
        <input data-testid="exp-merchant" placeholder="Where?" value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
          className="bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
      </div>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {cats.map((c) => (
          <button key={c} data-testid={`cat-${c}`} onClick={() => setCategory(c)}
            className={`px-3 py-1 rounded-full text-[11px] font-semibold capitalize ${category === c ? "bdy-bg text-white" : "bg-slate-100 text-slate-600"}`}>
            {c}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-2 mt-3">
        <button onClick={save} data-testid="save-expense-btn" className="bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 active:scale-95">
          <Plus className="w-4 h-4" /> Add
        </button>
        <button data-testid="scan-receipt-btn" className="bg-white border border-[color:var(--bdy)] text-[color:var(--bdy)] font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1">
          <Camera className="w-4 h-4" /> Scan
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

const Journal = () => {
  const [text, setText] = useState("");
  const [list, setList] = useState([]);
  const [weekly, setWeekly] = useState([]);
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
  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">Daily Journal</h3>
      <textarea
        data-testid="journal-textarea"
        value={text} onChange={(e) => setText(e.target.value)}
        placeholder="What's on your mind today?" rows={4}
        className="w-full mt-3 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)] resize-none"
      />
      <div className="grid grid-cols-2 gap-2 mt-2">
        <button onClick={save} data-testid="save-journal-btn" className="bdy-bg text-white font-semibold py-2.5 rounded-xl active:scale-95">
          Save
        </button>
        <button data-testid="voice-journal-btn" className="bg-white border border-[color:var(--bdy)] text-[color:var(--bdy)] font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1">
          <Mic className="w-4 h-4" /> Voice
        </button>
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
      </div>
    </Card>
  );
};

const Goals = () => {
  const [goals, setGoals] = useState([]);
  useEffect(() => { api.get("/goals").then((r) => setGoals(r.data)); }, []);
  return (
    <Card className="mx-5 mt-4">
      <h3 className="font-display font-bold text-lg">Goal Review</h3>
      <div className="space-y-3 mt-3" data-testid="goals-list">
        {goals.map((g) => (
          <div key={g.id} className="p-3 rounded-xl bg-slate-50">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Target className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-sm font-semibold">{g.title}</span>
              </div>
              <span className={`text-xs font-bold ${g.status === "missed" ? "text-rose-600" : "text-emerald-600"}`}>
                {g.current}%
              </span>
            </div>
            <div className="h-2 mt-2 rounded-full bg-slate-200 overflow-hidden">
              <div className="h-full bdy-bg transition-all" style={{ width: `${g.current}%` }} />
            </div>
            {g.status === "missed" && (
              <p className="text-[11px] text-rose-600 mt-1">⚠ Behind schedule — try a smaller daily step.</p>
            )}
          </div>
        ))}
      </div>
      <InsightCard icon={Sparkles} title="AI Recommendation" text="Sleep goal is slipping. Bundle it with study cutoff: stop studying by 11pm to protect 7+ hours." />
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
            Limited data available ({lb.days_used || "< 7"} days). Scores will improve with more entries.
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
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
            >
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        </Card>
      ) : (
        insights.length > 0 && (
          <div className="space-y-2" data-testid="daily-insights">
            {insights.map((i, idx) => (
              <InsightCard key={idx} icon={Sparkles} title={i.title} text={i.detail} />
            ))}
          </div>
        )
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
  { key: "goals", label: "Goals", C: Goals },
  { key: "summary", label: "AI Summary", C: Summary },
];

export default function DailyHub() {
  const [tab, setTab] = useState("mood");
  const [profile, setProfile] = useState({ name: "Alex" });
  const nav = useNavigate();
  useEffect(() => { api.get("/profile").then((r) => setProfile(r.data)); }, []);
  const Active = TABS.find((t) => t.key === tab).C;
  return (
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title={`Good morning, ${profile.name} ☀️`} subtitle="Here's your snapshot for today" />
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
    </div>
  );
}
