import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Moon, Brain, Activity, Calendar, ClipboardList, Timer, Users, Heart, Phone, Sparkles, Play, Pause } from "lucide-react";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell } from "recharts";

const ScoreRing = ({ score, label }) => {
  const r = 30, c = 2 * Math.PI * r;
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-20 h-20">
        <svg width="80" height="80" className="transform -rotate-90">
          <circle cx="40" cy="40" r={r} stroke="#E2E8F0" strokeWidth="6" fill="none" />
          <circle cx="40" cy="40" r={r} stroke="var(--bdy)" strokeWidth="6" fill="none"
            strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center font-display font-bold text-lg">{score}</div>
      </div>
      <div className="text-[11px] text-slate-600 font-semibold mt-1">{label}</div>
    </div>
  );
};

const Dashboard = () => {
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/wellness/scores").then((r) => setS(r.data)); }, []);
  if (!s) return null;
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex justify-around mt-2">
          <ScoreRing score={s.sleep_score} label="Sleep" />
          <ScoreRing score={s.stress_score} label="Calm" />
          <ScoreRing score={s.burnout_score} label="Burnout" />
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-base">Daily Wellness Actions</h3>
        <div className="mt-3 space-y-2">
          {[
            { i: Brain, t: "Quick Check-in", s: "Track your mood & stress" },
            { i: Heart, t: "Breathing Exercise", s: "3 min · reduce stress" },
            { i: Timer, t: "Focus Session", s: "25 min Pomodoro" },
            { i: Moon, t: "Sleep Tips", s: "Improve sleep quality" },
          ].map((a, idx) => (
            <button key={idx} data-testid={`wellness-action-${idx}`} className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition">
              <div className="w-9 h-9 rounded-xl bdy-soft flex items-center justify-center"><a.i className="w-4 h-4 bdy-text" /></div>
              <div className="flex-1 text-left">
                <div className="text-sm font-semibold">{a.t}</div>
                <div className="text-[11px] text-slate-500">{a.s}</div>
              </div>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
};

const Sleep = () => {
  const [data, setData] = useState([]);
  useEffect(() => { api.get("/sleep/weekly").then((r) => setData(r.data)); }, []);
  const last = data[data.length - 1];
  const avg = data.length ? data.reduce((s, d) => s + d.hours, 0) / data.length : 0;
  const diffMin = last ? Math.round((last.hours - avg) * 60) : 0;
  const formatHrs = (h) => `${Math.floor(h)}h ${Math.round((h - Math.floor(h)) * 60)}m`;
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Last Night</h3>
        <div className="font-display font-bold text-3xl mt-1" data-testid="last-night-hours">
          {last ? formatHrs(last.hours) : "—"}
        </div>
        <p className="text-xs text-slate-500">
          {last
            ? diffMin === 0
              ? "On par with your average"
              : `${Math.abs(diffMin)} min ${diffMin > 0 ? "more" : "less"} than usual`
            : "Log sleep to see trends"}
        </p>
        <div className="h-28 mt-3" data-testid="sleep-chart">
          <ResponsiveContainer>
            <BarChart data={data}>
              <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={10} />
              <Bar dataKey="hours" radius={[6, 6, 0, 0]}>
                {data.map((d, i) => (
                  <Cell key={i} fill={d.hours >= 7 ? "#34D399" : d.hours >= 6 ? "#FBBF24" : "#F87171"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-sm">Bedtime Planner</h3>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {["10:30pm", "11:00pm", "11:30pm"].map((t) => (
            <button key={t} className="p-2 rounded-xl bg-slate-50 text-xs font-semibold text-slate-700 hover:bdy-soft" data-testid={`bedtime-${t}`}>{t}</button>
          ))}
        </div>
      </Card>
    </div>
  );
};

const Burnout = () => {
  const [score, setScore] = useState(50);
  const [sleeps, setSleeps] = useState([]);
  useEffect(() => {
    api.get("/wellness/scores").then((r) => setScore(r.data.burnout_score));
    api.get("/sleep/weekly").then((r) => setSleeps(r.data));
  }, []);
  // marker = inverse of burnout_score (higher score = healthier = left side of gradient)
  const markerLeft = `${Math.max(2, Math.min(96, 100 - score))}%`;
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Burnout Risk</h3>
        <div className="mt-3 h-3 rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500 relative">
          <div className="absolute -top-1 w-5 h-5 rounded-full border-4 border-white shadow bg-slate-900 transition-all" style={{ left: markerLeft }} data-testid="burnout-marker" />
        </div>
        <div className="flex justify-between text-[10px] mt-1 text-slate-500 font-semibold"><span>Low</span><span>Med</span><span>High</span></div>
        <div className="mt-4 space-y-2">
          {sleeps.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-[10px] w-8 text-slate-500">{s.day}</span>
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bdy-bg" style={{ width: `${Math.min(100, s.hours * 12)}%` }} />
              </div>
              <span className="text-[10px] text-slate-600">{s.hours}h</span>
            </div>
          ))}
        </div>
        <InsightCard icon={Sparkles} title="Recovery suggestion" text={score < 50 ? "Burnout risk is elevated. Block tonight as no-screen and sleep 8h." : "You're tracking well. Keep your evening wind-down ritual consistent."} />
      </Card>
    </div>
  );
};

const AICard = ({ card }) => {
  const isPlan = card.kind === "plan" || /plan/i.test(card.kind || "");
  return (
    <div className={`rounded-2xl p-4 ${isPlan ? "bg-emerald-50 border border-emerald-100" : "bdy-soft border border-[color:var(--bdy)]/15"}`}>
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${isPlan ? "bg-emerald-500" : "bdy-bg"} text-white`}>
          <Sparkles className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
            {isPlan ? "Plan" : "Motivation"}
          </div>
          <div className="text-sm font-display font-bold text-slate-900">{card.title}</div>
          <div className="text-xs text-slate-700 mt-1 leading-relaxed">{card.text}</div>
        </div>
      </div>
    </div>
  );
};

const Stress = () => {
  const [data, setData] = useState([]);
  const [cards, setCards] = useState([]);
  const [loadingCards, setLoadingCards] = useState(true);
  useEffect(() => {
    api.get("/mood/weekly").then((r) => setData(r.data));
    api.get("/wellness/cards?kind=stress").then((r) => { setCards(r.data); setLoadingCards(false); }).catch(() => setLoadingCards(false));
  }, []);
  const moodEmoji = { great: "😄", good: "🙂", okay: "😐", bad: "🙁", terrible: "😢" };
  // dynamic triggers from data
  const stressAvg = data.length ? Math.round(data.reduce((s, d) => s + (d.stress || 0), 0) / data.length) : 0;
  const worstDay = [...data].sort((a, b) => (b.stress || 0) - (a.stress || 0))[0];
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Weekly Mood</h3>
        <div className="flex justify-between mt-3" data-testid="mood-timeline">
          {data.map((m, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className="text-2xl">{moodEmoji[m.mood] || "😐"}</div>
              <div className="text-[10px] text-slate-500 mt-1">{m.day}</div>
            </div>
          ))}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="p-2.5 rounded-xl bg-slate-50">
            <div className="text-[10px] text-slate-500 font-semibold">AVG STRESS</div>
            <div className="font-display font-bold text-lg">{stressAvg}/100</div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-50">
            <div className="text-[10px] text-slate-500 font-semibold">PEAK DAY</div>
            <div className="font-display font-bold text-lg">{worstDay ? worstDay.day : "—"}</div>
          </div>
        </div>
      </Card>

      <div data-testid="wellness-ai-cards" className="space-y-2">
        {loadingCards && (
          <Card><div className="text-xs text-slate-500 flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bdy-bg animate-pulse" /> Wellness AI is thinking…</div></Card>
        )}
        {cards.map((c, i) => <AICard key={i} card={c} />)}
      </div>
    </div>
  );
};

const Routine = () => {
  const [habits, setHabits] = useState([]);
  useEffect(() => { api.get("/routine/habits").then((r) => setHabits(r.data)); }, []);
  const worst = [...habits].sort((a, b) => a.value - b.value)[0];
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Habit Consistency</h3>
        <p className="text-xs text-slate-500">Last 7 days · computed from your check-ins, sleep, journal & workouts.</p>
        <div className="mt-3 space-y-2.5" data-testid="habit-list">
          {habits.map((h) => (
            <div key={h.habit}>
              <div className="flex justify-between text-xs">
                <span className="font-semibold">{h.habit}</span><span className="text-slate-500">{h.value}%</span>
              </div>
              <div className="h-2 mt-1 rounded-full bg-slate-100">
                <div className={`h-full rounded-full ${h.value >= 70 ? "bg-emerald-500" : h.value >= 40 ? "bdy-bg" : "bg-rose-400"}`} style={{ width: `${h.value}%` }} />
              </div>
            </div>
          ))}
        </div>
        {worst && (
          <InsightCard icon={Sparkles} title="Schedule disruption"
            text={`Your weakest habit this week is "${worst.habit}" (${worst.value}%). Pick one specific time tomorrow and protect it.`} />
        )}
      </Card>
    </div>
  );
};

const CheckIns = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base">PHQ-2 Check-In</h3>
      <p className="text-xs text-slate-500">Over the last 2 weeks…</p>
      {["Felt little interest or pleasure?", "Felt down or hopeless?"].map((q, i) => (
        <div key={i} className="mt-3">
          <p className="text-sm font-semibold">{q}</p>
          <div className="grid grid-cols-4 gap-1.5 mt-2">
            {["Never", "Some days", "Most days", "Daily"].map((o, j) => (
              <button key={j} data-testid={`phq-${i}-${j}`} className="py-1.5 rounded-lg bg-slate-50 text-[11px] font-semibold hover:bdy-soft">{o}</button>
            ))}
          </div>
        </div>
      ))}
    </Card>
    <Card>
      <h3 className="font-display font-bold text-sm">Reflection</h3>
      <p className="text-xs text-slate-500 mt-1">Write 1 thing you're proud of today.</p>
      <textarea data-testid="reflection-text" rows={3} className="w-full mt-2 bg-slate-50 rounded-xl p-2 text-sm border border-slate-200 outline-none" />
    </Card>
  </div>
);

const Focus = () => {
  const [running, setRunning] = useState(false);
  const [time, setTime] = useState(25 * 60);
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setTime((t) => (t > 0 ? t - 1 : 0)), 1000);
    return () => clearInterval(id);
  }, [running]);
  const mm = String(Math.floor(time / 60)).padStart(2, "0");
  const ss = String(time % 60).padStart(2, "0");
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="text-center">
          <div className="text-xs text-slate-500 font-semibold">FOCUS · POMODORO</div>
          <div className="font-display font-bold text-6xl mt-2 bdy-text" data-testid="pomodoro-time">{mm}:{ss}</div>
          <button onClick={() => setRunning(!running)} data-testid="pomodoro-toggle"
            className="mt-3 bdy-bg text-white font-semibold px-6 py-2.5 rounded-full flex items-center gap-2 mx-auto active:scale-95">
            {running ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />} {running ? "Pause" : "Start"}
          </button>
        </div>
        <div className="mt-4">
          <div className="text-xs font-semibold text-slate-500">Today: 3 sessions completed 🎉</div>
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-sm">Break Activities</h3>
        <ul className="text-xs text-slate-700 mt-2 space-y-1">
          <li>• 5-min stretch routine</li>
          <li>• Box breathing (4-4-4-4)</li>
          <li>• Walk outside</li>
          <li>• Hydrate + snack</li>
        </ul>
      </Card>
    </div>
  );
};

const Social = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base">Social Balance</h3>
      <p className="text-xs text-slate-500 mt-1">You connected with 3 people this week.</p>
      <div className="mt-3 space-y-2">
        {[{ n: "Study group", d: "Tomorrow 5pm" }, { n: "Movie night", d: "Saturday" }, { n: "Coffee w/ Priya", d: "Sunday" }].map((e, i) => (
          <div key={i} className="p-3 rounded-xl bg-slate-50 flex justify-between">
            <span className="text-sm font-semibold">{e.n}</span>
            <span className="text-xs text-slate-500">{e.d}</span>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const Support = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base">Guided Practices</h3>
      <div className="mt-3 space-y-2">
        {[{ n: "Box Breathing", d: "3 min" }, { n: "Body Scan", d: "10 min" }, { n: "Sleep Wind-down", d: "8 min" }, { n: "Gratitude Pause", d: "2 min" }].map((p, i) => (
          <button key={i} data-testid={`practice-${i}`} className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-50">
            <div className="w-9 h-9 rounded-xl bdy-soft flex items-center justify-center"><Heart className="w-4 h-4 bdy-text" /></div>
            <div className="flex-1 text-left">
              <div className="text-sm font-semibold">{p.n}</div>
              <div className="text-[11px] text-slate-500">{p.d}</div>
            </div>
          </button>
        ))}
      </div>
    </Card>
    <Card className="bg-rose-50 border-rose-200">
      <div className="flex items-center gap-3">
        <Phone className="w-5 h-5 text-rose-600" />
        <div>
          <div className="text-sm font-bold text-rose-700">In crisis? Talk to someone.</div>
          <div className="text-xs text-rose-600">Campus counseling: 24/7 support</div>
        </div>
      </div>
    </Card>
  </div>
);

const TABS = [
  { key: "dash", label: "Dashboard", C: Dashboard },
  { key: "sleep", label: "Sleep", C: Sleep },
  { key: "burn", label: "Burnout", C: Burnout },
  { key: "stress", label: "Stress", C: Stress },
  { key: "routine", label: "Routine", C: Routine },
  { key: "check", label: "Check-Ins", C: CheckIns },
  { key: "focus", label: "Focus", C: Focus },
  { key: "social", label: "Social", C: Social },
  { key: "support", label: "Support", C: Support },
];

export default function WellnessBuddy() {
  const [tab, setTab] = useState("dash");
  const Active = TABS.find((t) => t.key === tab).C;
  return (
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Wellness Buddy ☁️" subtitle="Mind. Body. Balance." gradient />
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="well-tab" />
      <Active />
    </div>
  );
}
