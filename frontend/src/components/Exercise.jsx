import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { Card, InsightCard } from "./SubTabs";
import { Plus, Play, Pause, Trash2, X, MessageSquare, Clock, CheckCircle2, Dumbbell, AlertTriangle, Sparkles } from "lucide-react";

const fmtElapsed = (s) => {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return `${h ? h + "h " : ""}${m}m ${sec}s`;
};

const BODY_PARTS = [
  { v: "upper", t: "Upper" },
  { v: "lower", t: "Lower" },
  { v: "cardio", t: "Cardio" },
  { v: "full", t: "Full body" },
];

const ExerciseDetail = ({ exercise, onClose, onChanged }) => {
  const [sessions, setSessions] = useState([]);
  const [active, setActive] = useState(null);
  const [totalSec, setTotalSec] = useState(0);
  const [comment, setComment] = useState("");
  const [progress, setProgress] = useState(exercise.progress);
  const [, setTick] = useState(0);
  const timerRef = useRef(null);

  const load = async () => {
    const { data } = await api.get(`/exercises/${exercise.id}/sessions`);
    setSessions(data.sessions);
    setTotalSec(data.total_seconds);
    setActive(data.active);
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [exercise.id]);
  useEffect(() => {
    clearInterval(timerRef.current);
    if (active) timerRef.current = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(timerRef.current);
  }, [active]);

  const liveElapsed = active ? Math.floor((Date.now() - new Date(active.started_at).getTime()) / 1000) : 0;

  const start = async () => { await api.post(`/exercises/${exercise.id}/start`); setComment(""); load(); };
  const stop = async () => { await api.post(`/exercises/${exercise.id}/stop`, { comment }); setComment(""); load(); onChanged?.(); };
  const updateProgress = async (val) => { setProgress(val); await api.patch(`/exercises/${exercise.id}`, { progress: val }); onChanged?.(); };
  const remove = async () => { if (!window.confirm("Delete this exercise and all its sessions?")) return; await api.delete(`/exercises/${exercise.id}`); onChanged?.(); onClose(); };

  return (
    <div className="absolute inset-0 z-50 bg-black/40 flex items-end" onClick={onClose} data-testid="exercise-detail-modal">
      <div className="w-full bg-white rounded-t-3xl p-5 max-h-[85%] overflow-auto scroll-area" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="font-display font-bold text-lg leading-tight">{exercise.name}</h3>
            <p className="text-xs text-slate-500 capitalize">{exercise.body_part} · Target {exercise.target_minutes} min · Logged {fmtElapsed(totalSec + (active ? liveElapsed : 0))}</p>
          </div>
          <div className="flex gap-1">
            <button onClick={remove} data-testid="exercise-delete-btn" className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center"><Trash2 className="w-4 h-4" /></button>
            <button onClick={onClose} data-testid="exercise-close-btn" className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center"><X className="w-4 h-4" /></button>
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5"><span>Progress</span><span className="text-[color:var(--bdy)]">{progress}%</span></div>
          <input type="range" min="0" max="100" value={progress} onChange={(e) => updateProgress(parseInt(e.target.value))} className="bdy-slider" style={{ "--val": `${progress}%` }} data-testid="exercise-progress-slider" />
        </div>
        <div className="mt-4 p-4 rounded-2xl bdy-soft border border-[color:var(--bdy)]/15 text-center">
          <div className="text-[10px] font-bold uppercase text-slate-600">Live Session</div>
          <div className="font-display font-bold text-3xl mt-1 bdy-text" data-testid="exercise-live-timer">{active ? fmtElapsed(liveElapsed) : fmtElapsed(0)}</div>
          {active && (
            <textarea data-testid="exercise-comment-input" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Reps / sets / how it felt" rows={2}
              className="w-full mt-3 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)] resize-none" />
          )}
          {active ? (
            <button onClick={stop} data-testid="exercise-stop-btn" className="mt-3 w-full bg-rose-600 text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 active:scale-95"><Pause className="w-4 h-4" /> Stop & Save</button>
          ) : (
            <button onClick={start} data-testid="exercise-start-btn" className="mt-3 w-full bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 active:scale-95"><Play className="w-4 h-4" /> Start workout</button>
          )}
        </div>
        <div className="mt-4">
          <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5" /> SESSION LOG</div>
          {sessions.length === 0 && <p className="text-xs text-slate-400">No sessions yet.</p>}
          <div className="space-y-2" data-testid="exercise-session-list">
            {sessions.filter(s => s.ended_at).map((s) => (
              <div key={s.id} className="p-2.5 rounded-xl bg-slate-50">
                <div className="flex justify-between items-center text-[11px] text-slate-500">
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{fmtElapsed(s.elapsed_seconds)}</span>
                  <span>{new Date(s.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                </div>
                {s.comment && <p className="text-xs text-slate-700 mt-1">{s.comment}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const ExerciseTracker = () => {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(null);
  const [summary, setSummary] = useState(null);
  const [newName, setNewName] = useState("");
  const [newPart, setNewPart] = useState("upper");
  const [newMin, setNewMin] = useState("");

  const load = async () => {
    const [list, sum] = await Promise.all([api.get("/exercises"), api.get("/exercises/summary")]);
    setItems(list.data);
    setSummary(sum.data);
  };
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!newName.trim()) return;
    await api.post("/exercises", { name: newName.trim(), body_part: newPart, target_minutes: parseInt(newMin) || 30 });
    setNewName(""); setNewMin("");
    load();
  };

  return (
    <div className="mx-5 mt-4 space-y-3 relative">
      {summary && (
        <Card className={summary.sedentary ? "bg-rose-50 border-rose-100" : "bg-emerald-50 border-emerald-100"}>
          <div className="flex items-start gap-2">
            {summary.sedentary
              ? <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              : <Dumbbell className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />}
            <div className="flex-1">
              <div className="text-sm font-display font-bold">
                {summary.today_minutes} min active today
              </div>
              <p className={`text-xs mt-0.5 ${summary.sedentary ? "text-rose-700" : "text-emerald-700"}`} data-testid="sedentary-warning">{summary.sedentary_warning}</p>
              {!summary.balanced_7d && (
                <p className="text-xs text-amber-700 mt-1.5" data-testid="imbalance-note">⚠ {summary.imbalance_note}</p>
              )}
            </div>
          </div>
          <div className="mt-3">
            <div className="text-[10px] font-semibold text-slate-500 uppercase">7-day Body Split (min)</div>
            <div className="flex items-end gap-2 mt-2 h-16">
              {Object.entries(summary.by_part_7d).map(([k, v]) => {
                const max = Math.max(1, ...Object.values(summary.by_part_7d));
                return (
                  <div key={k} className="flex-1 flex flex-col items-center">
                    <div className="w-full rounded-t bg-white border border-[color:var(--bdy)]/30" style={{ height: `${(v / max) * 100 || 4}%` }} />
                    <span className="text-[9px] mt-1 capitalize text-slate-600">{k}</span>
                    <span className="text-[10px] font-bold">{v}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      )}

      <Card>
        <h3 className="font-display font-bold text-base">Your Exercises</h3>
        <p className="text-xs text-slate-500">Track yoga, gym, cardio. Tap to log a set with comments.</p>
        <div className="mt-3 space-y-2" data-testid="exercise-list">
          {items.map((t) => (
            <button key={t.id} onClick={() => setOpen(t)} data-testid={`exercise-row-${t.id}`} className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-slate-100 active:scale-[0.99]">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2 flex-1">
                  {t.progress >= 100
                    ? <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    : <Dumbbell className="w-4 h-4 text-slate-400 shrink-0" />}
                  <div>
                    <div className={`text-sm font-semibold ${t.progress >= 100 ? "line-through text-slate-400" : ""}`}>{t.name}</div>
                    <div className="text-[10px] text-slate-500 capitalize">{t.body_part} · {t.target_minutes} min</div>
                  </div>
                </div>
                <span className="text-xs font-bold bdy-text">{t.progress}%</span>
              </div>
              <div className="h-1.5 mt-2 rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bdy-bg transition-all" style={{ width: `${t.progress}%` }} />
              </div>
            </button>
          ))}
          {items.length === 0 && <p className="text-xs text-slate-400 py-3">No exercises yet. Add one below.</p>}
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
          <div className="flex gap-2">
            <input data-testid="new-exercise-name" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Exercise (e.g. Squats)"
              className="flex-1 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            <input data-testid="new-exercise-min" type="number" value={newMin} onChange={(e) => setNewMin(e.target.value)} placeholder="min"
              className="w-16 bg-slate-50 rounded-xl px-2 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
          </div>
          <div className="flex gap-1.5">
            {BODY_PARTS.map((p) => (
              <button key={p.v} onClick={() => setNewPart(p.v)} data-testid={`bp-${p.v}`}
                className={`flex-1 px-2 py-1.5 rounded-lg text-[11px] font-semibold ${newPart === p.v ? "bdy-bg text-white" : "bg-slate-100 text-slate-600"}`}>
                {p.t}
              </button>
            ))}
          </div>
          <button onClick={add} disabled={!newName.trim()} data-testid="add-exercise-btn"
            className="w-full bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 disabled:opacity-50 active:scale-95">
            <Plus className="w-4 h-4" /> Add exercise
          </button>
        </div>
        <InsightCard icon={Sparkles} title="Balance is everything" text="Aim for 2 upper, 2 lower and 1 cardio session per week. Mix it up so nothing gets neglected." />
      </Card>

      {open && <ExerciseDetail exercise={open} onClose={() => setOpen(null)} onChanged={load} />}
    </div>
  );
};
