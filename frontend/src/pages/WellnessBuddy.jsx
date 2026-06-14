import React, { useEffect, useState, useCallback } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Moon, Brain, Activity, Calendar, ClipboardList, Timer, Users, Heart, Phone, Sparkles, Play, Pause, Check, Save } from "lucide-react";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell } from "recharts";
import PageTransition from "../components/PageTransition";

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

const Dashboard = ({ onNavigate }) => {
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/wellness/scores").then((r) => setS(r.data)).catch(() => { }); }, []);
  if (!s) return null;

  const actions = [
    { i: Brain, t: "Quick Check-in", s: "Track your mood & stress", target: "stress" },
    { i: Heart, t: "Breathing Exercise", s: "3 min · reduce stress", target: "support" },
    { i: Timer, t: "Focus Session", s: "25 min Pomodoro", target: "focus" },
    { i: Moon, t: "Sleep Tips", s: "Improve sleep quality", target: "sleep" },
  ];

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
          {actions.map((a, idx) => (
            <button key={idx} data-testid={`wellness-action-${idx}`}
              onClick={() => onNavigate(a.target)}
              aria-label={`${a.t} - ${a.s}`}
              className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition">
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
  const [bedtimeGoal, setBedtimeGoal] = useState(null);
  const [saving, setSaving] = useState(false);
  const [sleepForm, setSleepForm] = useState({ hours: 7, quality: "good" });
  const [sleepSaved, setSleepSaved] = useState(false);

  useEffect(() => {
    api.get("/sleep/weekly").then((r) => setData(r.data)).catch(() => { });
    api.get("/sleep/bedtime-goal").then((r) => setBedtimeGoal(r.data.bedtime_goal)).catch(() => { });
  }, []);

  const last = data[data.length - 1];
  const avg = data.length ? data.reduce((s, d) => s + d.hours, 0) / data.length : 0;
  const diffMin = last ? Math.round((last.hours - avg) * 60) : 0;
  const formatHrs = (h) => `${Math.floor(h)}h ${Math.round((h - Math.floor(h)) * 60)}m`;

  const handleBedtimeGoal = async (time) => {
    setSaving(true);
    try {
      const res = await api.post("/sleep/bedtime-goal", { time });
      setBedtimeGoal(time);
    } catch (e) { /* ignore */ }
    setSaving(false);
  };

  const handleSaveSleep = async () => {
    setSleepSaved(false);
    try {
      await api.post("/sleep", { hours: parseFloat(sleepForm.hours), quality: sleepForm.quality });
      setSleepSaved(true);
      // Refresh weekly data
      const r = await api.get("/sleep/weekly");
      setData(r.data);
    } catch (e) { /* ignore */ }
  };

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

      {/* Sleep Entry Form */}
      <Card>
        <h3 className="font-display font-bold text-sm">Log Sleep</h3>
        <div className="mt-2 space-y-3">
          <div>
            <label className="text-xs text-slate-500 font-semibold">Hours slept</label>
            <input
              type="number"
              min="0" max="24" step="0.5"
              value={sleepForm.hours}
              onChange={(e) => setSleepForm(f => ({ ...f, hours: e.target.value }))}
              className="w-full mt-1 p-2 rounded-xl bg-slate-50 border border-slate-200 text-sm outline-none"
              data-testid="sleep-hours-input"
              aria-label="Enter hours slept"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 font-semibold">Quality</label>
            <div className="grid grid-cols-3 gap-2 mt-1">
              {["good", "ok", "poor"].map((q) => (
                <button key={q} data-testid={`sleep-quality-${q}`}
                  onClick={() => setSleepForm(f => ({ ...f, quality: q }))}
                  className={`py-1.5 rounded-lg text-xs font-semibold transition ${sleepForm.quality === q ? "bdy-bg text-white" : "bg-slate-50 text-slate-700 hover:bg-slate-100"}`}>
                  {q === "good" ? "😊 Good" : q === "ok" ? "😐 OK" : "😴 Poor"}
                </button>
              ))}
            </div>
          </div>
          <button onClick={handleSaveSleep} data-testid="save-sleep-btn"
            aria-label="Save sleep entry"
            className="w-full py-2 rounded-xl bdy-bg text-white text-sm font-semibold flex items-center justify-center gap-2 active:scale-95">
            {sleepSaved ? <><Check className="w-4 h-4" /> Saved!</> : <><Save className="w-4 h-4" /> Save Sleep Entry</>}
          </button>
        </div>
      </Card>

      {/* Bedtime Planner */}
      <Card>
        <h3 className="font-display font-bold text-sm">Bedtime Planner</h3>
        {bedtimeGoal && (
          <p className="text-xs text-emerald-600 font-semibold mt-1">Current goal: {bedtimeGoal}</p>
        )}
        <div className="mt-2 grid grid-cols-3 gap-2">
          {["10:30pm", "11:00pm", "11:30pm"].map((t) => (
            <button key={t}
              onClick={() => handleBedtimeGoal(t)}
              disabled={saving}
              data-testid={`bedtime-${t}`}
              className={`p-2 rounded-xl text-xs font-semibold transition ${bedtimeGoal === t ? "bdy-bg text-white" : "bg-slate-50 text-slate-700 hover:bdy-soft"}`}>
              {t}
            </button>
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
    api.get("/wellness/scores").then((r) => setScore(r.data.burnout_score)).catch(() => { });
    api.get("/sleep/weekly").then((r) => setSleeps(r.data)).catch(() => { });
  }, []);
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
  const isPhq2 = card.kind === "phq2_response";
  return (
    <div className={`rounded-2xl p-4 ${isPhq2 ? "bg-blue-50 border border-blue-100" : isPlan ? "bg-emerald-50 border border-emerald-100" : "bdy-soft border border-[color:var(--bdy)]/15"}`}>
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${isPhq2 ? "bg-blue-500" : isPlan ? "bg-emerald-500" : "bdy-bg"} text-white`}>
          <Sparkles className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
            {isPhq2 ? "PHQ-2 Response" : isPlan ? "Plan" : "Motivation"}
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
    api.get("/mood/weekly").then((r) => setData(r.data)).catch(() => { });
    api.get("/wellness/cards?kind=stress").then((r) => { setCards(r.data); setLoadingCards(false); }).catch(() => setLoadingCards(false));
  }, []);
  const moodEmoji = { great: "😄", good: "🙂", okay: "😐", bad: "🙁", terrible: "😢" };
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
  useEffect(() => { api.get("/routine/habits").then((r) => setHabits(r.data)).catch(() => { }); }, []);
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

const CheckIns = () => {
  const [answers, setAnswers] = useState([null, null]);
  const [submitting, setSubmitting] = useState(false);
  const [responseCard, setResponseCard] = useState(null);
  const [reflection, setReflection] = useState("");
  const [reflectionSaved, setReflectionSaved] = useState(false);

  const questions = ["Felt little interest or pleasure?", "Felt down or hopeless?"];
  const options = ["Never", "Some days", "Most days", "Daily"];

  const handleAnswer = (qIdx, optIdx) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[qIdx] = optIdx;
      return next;
    });
  };

  const handleSubmitPHQ2 = async () => {
    if (answers[0] === null || answers[1] === null) return;
    setSubmitting(true);
    try {
      const res = await api.post("/wellness/phq2", { q1: answers[0], q2: answers[1] });
      if (res.data.ai_card) {
        setResponseCard(res.data.ai_card);
      }
    } catch (e) { /* ignore */ }
    setSubmitting(false);
  };

  const handleSaveReflection = async () => {
    if (!reflection.trim()) return;
    setReflectionSaved(false);
    try {
      await api.post("/journal", { text: reflection, sentiment: null });
      setReflectionSaved(true);
      setTimeout(() => setReflectionSaved(false), 3000);
    } catch (e) { /* ignore */ }
  };

  const canSubmit = answers[0] !== null && answers[1] !== null;

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">PHQ-2 Check-In</h3>
        <p className="text-xs text-slate-500">Over the last 2 weeks…</p>
        {questions.map((q, i) => (
          <div key={i} className="mt-3">
            <p className="text-sm font-semibold">{q}</p>
            <div className="grid grid-cols-4 gap-1.5 mt-2">
              {options.map((o, j) => (
                <button key={j} data-testid={`phq-${i}-${j}`}
                  onClick={() => handleAnswer(i, j)}
                  aria-label={`${o} for question ${i + 1}`}
                  className={`py-1.5 rounded-lg text-[11px] font-semibold transition ${answers[i] === j ? "bdy-bg text-white" : "bg-slate-50 hover:bdy-soft"}`}>
                  {o}
                </button>
              ))}
            </div>
          </div>
        ))}
        <button
          onClick={handleSubmitPHQ2}
          disabled={!canSubmit || submitting}
          data-testid="phq2-submit"
          aria-label="Submit PHQ-2 check-in"
          className={`w-full mt-4 py-2.5 rounded-xl text-sm font-semibold transition ${canSubmit ? "bdy-bg text-white active:scale-95" : "bg-slate-100 text-slate-400 cursor-not-allowed"}`}>
          {submitting ? "Submitting..." : "Submit Check-In"}
        </button>
      </Card>

      {responseCard && <AICard card={responseCard} />}

      <Card>
        <h3 className="font-display font-bold text-sm">Reflection</h3>
        <p className="text-xs text-slate-500 mt-1">Write 1 thing you're proud of today.</p>
        <textarea
          data-testid="reflection-text"
          rows={3}
          value={reflection}
          onChange={(e) => setReflection(e.target.value)}
          aria-label="Write your daily reflection"
          className="w-full mt-2 bg-slate-50 rounded-xl p-2 text-sm border border-slate-200 outline-none"
          placeholder="I'm proud that..."
        />
        <button
          onClick={handleSaveReflection}
          disabled={!reflection.trim()}
          data-testid="save-reflection-btn"
          aria-label="Save daily reflection"
          className={`w-full mt-2 py-2 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition ${reflection.trim() ? "bdy-bg text-white active:scale-95" : "bg-slate-100 text-slate-400 cursor-not-allowed"}`}>
          {reflectionSaved ? <><Check className="w-4 h-4" /> Saved!</> : <><Save className="w-4 h-4" /> Save Reflection</>}
        </button>
      </Card>
    </div>
  );
};

const Focus = () => {
  const [running, setRunning] = useState(false);
  const [time, setTime] = useState(25 * 60);
  const [todaySessions, setTodaySessions] = useState(0);
  const [todayMinutes, setTodayMinutes] = useState(0);

  useEffect(() => {
    api.get("/focus/today").then((r) => {
      setTodaySessions(r.data.count);
      setTodayMinutes(r.data.total_minutes);
    }).catch(() => { });
  }, []);

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
            aria-label={running ? "Pause focus timer" : "Start focus timer"}
            className="mt-3 bdy-bg text-white font-semibold px-6 py-2.5 rounded-full flex items-center gap-2 mx-auto active:scale-95">
            {running ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />} {running ? "Pause" : "Start"}
          </button>
        </div>
        <div className="mt-4">
          <div className="text-xs font-semibold text-slate-500" data-testid="focus-session-count">
            Today: {todaySessions} session{todaySessions !== 1 ? "s" : ""} completed ({todayMinutes} min) {todaySessions > 0 ? "🎉" : ""}
          </div>
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

const Social = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/wellness/social-summary").then((r) => {
      setData(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="mx-5 mt-4"><Card><div className="text-xs text-slate-500">Loading social data…</div></Card></div>
  );

  const hasData = data && (data.connections_this_week > 0 || data.groups?.length > 0);

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Social Balance</h3>
        {hasData ? (
          <>
            <p className="text-xs text-slate-500 mt-1">
              You connected with {data.connections_this_week} {data.connections_this_week === 1 ? "person" : "people"} this week.
            </p>
            {data.groups?.length > 0 && (
              <div className="mt-3 space-y-2">
                {data.groups.map((g, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-50 flex justify-between">
                    <span className="text-sm font-semibold">{g.name}</span>
                    <span className="text-xs text-slate-500">{g.member_count} members</span>
                  </div>
                ))}
              </div>
            )}
            {data.upcoming_events?.length > 0 && (
              <div className="mt-3">
                <h4 className="text-xs font-semibold text-slate-500">Upcoming</h4>
                <div className="mt-1 space-y-1.5">
                  {data.upcoming_events.map((e, i) => (
                    <div key={i} className="p-2 rounded-lg bg-slate-50 flex justify-between">
                      <span className="text-xs font-semibold">{e.name}</span>
                      <span className="text-[10px] text-slate-500">{e.deadline}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="mt-3 text-center py-6">
            <Users className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="text-sm text-slate-500 mt-2">No social connections yet</p>
            <p className="text-xs text-slate-400 mt-1">Join a study group to connect with peers</p>
          </div>
        )}
      </Card>
    </div>
  );
};

const Support = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base">Guided Practices</h3>
      <div className="mt-3 space-y-2">
        {[{ n: "Box Breathing", d: "3 min" }, { n: "Body Scan", d: "10 min" }, { n: "Sleep Wind-down", d: "8 min" }, { n: "Gratitude Pause", d: "2 min" }].map((p, i) => (
          <button key={i} data-testid={`practice-${i}`} aria-label={`${p.n}, ${p.d}`} className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-50">
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
  const ActiveTab = TABS.find((t) => t.key === tab);
  const Active = ActiveTab.C;

  // Pass onNavigate to Dashboard so action buttons can switch tabs
  const renderActive = () => {
    if (tab === "dash") return <Dashboard onNavigate={setTab} />;
    return <Active />;
  };

  return (
    <PageTransition className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Wellness Buddy ☁️" subtitle="Mind. Body. Balance." gradient />
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="well-tab" />
      {renderActive()}
    </PageTransition>
  );
}
