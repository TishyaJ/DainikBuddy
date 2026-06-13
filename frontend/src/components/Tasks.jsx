import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { Card, InsightCard } from "./SubTabs";
import { Plus, Play, Pause, Trash2, X, MessageSquare, Clock, CheckCircle2, Sparkles } from "lucide-react";

const fmtElapsed = (s) => {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return `${h ? h + "h " : ""}${m}m ${sec}s`;
};

const TaskDetail = ({ task, onClose, onChanged }) => {
  const [sessions, setSessions] = useState([]);
  const [active, setActive] = useState(null);
  const [totalSec, setTotalSec] = useState(0);
  const [comment, setComment] = useState("");
  const [progress, setProgress] = useState(task.progress);
  const [tick, setTick] = useState(0);
  const timerRef = useRef(null);

  const load = async () => {
    const { data } = await api.get(`/tasks/${task.id}/sessions`);
    setSessions(data.sessions);
    setTotalSec(data.total_seconds);
    setActive(data.active);
  };

  useEffect(() => { load(); }, [task.id]);

  useEffect(() => {
    clearInterval(timerRef.current);
    if (active) {
      timerRef.current = setInterval(() => setTick((t) => t + 1), 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [active]);

  const liveElapsed = active
    ? Math.floor((Date.now() - new Date(active.started_at).getTime()) / 1000)
    : 0;

  const start = async () => {
    await api.post(`/tasks/${task.id}/start`);
    setComment("");
    await load();
  };

  const stop = async () => {
    await api.post(`/tasks/${task.id}/stop`, { comment });
    setComment("");
    await load();
    onChanged?.();
  };

  const updateProgress = async (val) => {
    setProgress(val);
    await api.patch(`/tasks/${task.id}`, { progress: val });
    onChanged?.();
  };

  const removeTask = async () => {
    if (!window.confirm("Delete this task and all its sessions?")) return;
    await api.delete(`/tasks/${task.id}`);
    onChanged?.();
    onClose();
  };

  return (
    <div
      className="absolute inset-0 z-50 bg-black/40 flex items-end"
      onClick={onClose}
      data-testid="task-detail-modal"
    >
      <div
        className="w-full bg-white rounded-t-3xl p-5 max-h-[85%] overflow-auto scroll-area"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="font-display font-bold text-lg leading-tight">{task.title}</h3>
            <p className="text-xs text-slate-500">Target: {task.target_minutes} min · Logged: {fmtElapsed(totalSec + (active ? liveElapsed : 0))}</p>
          </div>
          <div className="flex gap-1">
            <button onClick={removeTask} data-testid="task-delete-btn" className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <Trash2 className="w-4 h-4" />
            </button>
            <button onClick={onClose} data-testid="task-close-btn" className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
            <span>Progress</span>
            <span className="text-[color:var(--bdy)]">{progress}%</span>
          </div>
          <input
            type="range" min="0" max="100" value={progress}
            onChange={(e) => updateProgress(parseInt(e.target.value))}
            className="bdy-slider" style={{ "--val": `${progress}%` }}
            data-testid="task-progress-slider"
          />
        </div>

        {/* Live timer */}
        <div className="mt-4 p-4 rounded-2xl bdy-soft border border-[color:var(--bdy)]/15 text-center">
          <div className="text-[10px] font-bold uppercase text-slate-600">Live Session</div>
          <div className="font-display font-bold text-3xl mt-1 bdy-text" data-testid="task-live-timer">
            {active ? fmtElapsed(liveElapsed) : fmtElapsed(0)}
          </div>
          {active && (
            <textarea
              data-testid="task-comment-input"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="What did you do this session? (optional)"
              rows={2}
              className="w-full mt-3 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)] resize-none"
            />
          )}
          {active ? (
            <button onClick={stop} data-testid="task-stop-btn"
              className="mt-3 w-full bg-rose-600 text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 active:scale-95">
              <Pause className="w-4 h-4" /> Stop & Save
            </button>
          ) : (
            <button onClick={start} data-testid="task-start-btn"
              className="mt-3 w-full bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 active:scale-95">
              <Play className="w-4 h-4" /> Start working
            </button>
          )}
        </div>

        {/* History */}
        <div className="mt-4">
          <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
            <MessageSquare className="w-3.5 h-3.5" /> SESSION LOG
          </div>
          {sessions.length === 0 && <p className="text-xs text-slate-400">No sessions yet. Hit Start to log one.</p>}
          <div className="space-y-2" data-testid="task-session-list">
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

export const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [open, setOpen] = useState(null);
  const [newTitle, setNewTitle] = useState("");
  const [newMin, setNewMin] = useState("");

  const load = async () => setTasks((await api.get("/tasks")).data);
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!newTitle.trim()) return;
    await api.post("/tasks", { title: newTitle.trim(), target_minutes: parseInt(newMin) || 60 });
    setNewTitle(""); setNewMin("");
    load();
  };

  const doneCount = tasks.filter((t) => t.progress >= 100).length;

  return (
    <Card className="mx-5 mt-4 relative">
      <div className="flex justify-between items-center">
        <h3 className="font-display font-bold text-lg">Today's Tasks</h3>
        <span className="text-xs font-bold bdy-text">{doneCount}/{tasks.length} done</span>
      </div>
      <p className="text-xs text-slate-500">Tap a task to log time, add comments, edit progress.</p>

      <div className="mt-3 space-y-2" data-testid="task-list">
        {tasks.map((t) => (
          <button
            key={t.id}
            onClick={() => setOpen(t)}
            data-testid={`task-row-${t.id}`}
            className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition active:scale-[0.99]"
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 flex-1">
                {t.progress >= 100 ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-slate-300 shrink-0" />
                )}
                <span className={`text-sm font-semibold truncate ${t.progress >= 100 ? "line-through text-slate-400" : ""}`}>
                  {t.title}
                </span>
              </div>
              <span className="text-xs font-bold bdy-text">{t.progress}%</span>
            </div>
            <div className="h-1.5 mt-2 rounded-full bg-slate-200 overflow-hidden">
              <div className="h-full bdy-bg transition-all" style={{ width: `${t.progress}%` }} />
            </div>
          </button>
        ))}
        {tasks.length === 0 && <p className="text-xs text-slate-400 py-3">No tasks yet. Add one below.</p>}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100">
        <div className="flex gap-2">
          <input
            data-testid="new-task-title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="New task..."
            className="flex-1 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
          />
          <input
            data-testid="new-task-min"
            value={newMin}
            onChange={(e) => setNewMin(e.target.value)}
            type="number"
            placeholder="min"
            className="w-16 bg-slate-50 rounded-xl px-2 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
          />
          <button
            onClick={add}
            data-testid="add-task-btn"
            disabled={!newTitle.trim()}
            className="w-10 h-10 rounded-xl bdy-bg text-white flex items-center justify-center disabled:opacity-50 active:scale-95"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      <InsightCard
        icon={Sparkles}
        title="Tip"
        text="Break big tasks into 25-min focused sessions. Each Start/Stop saves a comment so you can review what worked."
      />

      {open && <TaskDetail task={open} onClose={() => setOpen(null)} onChanged={load} />}
    </Card>
  );
};
