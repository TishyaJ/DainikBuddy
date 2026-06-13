import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Smile, Frown, Meh, Heart, Zap, Mic, Camera, Plus, Target, Sparkles } from "lucide-react";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell } from "recharts";

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
  const [insights, setInsights] = useState([]);
  useEffect(() => {
    api.get("/life-balance").then((r) => setLb(r.data));
    api.get("/insights/daily").then((r) => setInsights(r.data));
  }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-lg">Today's AI Snapshot</h3>
        <p className="text-xs text-slate-500 mt-1">Cross-domain summary for Alex</p>
        {lb && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {lb.domains.map((d) => (
              <div key={d.name} className="p-3 rounded-xl bg-slate-50">
                <div className="text-[10px] uppercase text-slate-500 font-semibold">{d.name}</div>
                <div className="text-2xl font-bold font-display mt-0.5">{d.score}</div>
              </div>
            ))}
          </div>
        )}
      </Card>
      {insights.map((i, idx) => (
        <InsightCard key={idx} icon={Sparkles} title={i.title} text={i.detail} />
      ))}
      <Card className="bdy-gradient text-white">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          <h3 className="font-display font-bold text-lg">Tomorrow's Advice</h3>
        </div>
        <p className="text-sm mt-2 text-white/90">
          Start your day with the harder subject. Take a 5-min walk after lunch. Lights out by 11:30pm to recover sleep.
        </p>
      </Card>
    </div>
  );
};

const TABS = [
  { key: "mood", label: "Mood", C: Mood },
  { key: "expense", label: "Expense", C: Expense },
  { key: "journal", label: "Journal", C: Journal },
  { key: "goals", label: "Goals", C: Goals },
  { key: "summary", label: "AI Summary", C: Summary },
];

export default function DailyHub() {
  const [tab, setTab] = useState("mood");
  const Active = TABS.find((t) => t.key === tab).C;
  return (
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Good morning, Alex ☀️" subtitle="Here's your snapshot for today" />
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
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="daily-tab" />
      <Active />
    </div>
  );
}
