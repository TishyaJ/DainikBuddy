import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { Card, InsightCard } from "../components/SubTabs";
import { api } from "../lib/api";
import { Sparkles, ChevronRight } from "lucide-react";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from "recharts";

const BUDDIES = [
  { key: "finance", name: "Finance Buddy", emoji: "🦉", tag: "Savings. Budgeting. Smart choices.", color: "#3B82F6", bg: "#EFF6FF" },
  { key: "wellness", name: "Wellness Buddy", emoji: "☁️", tag: "Here for your mind and body.", color: "#A78BFA", bg: "#F5F3FF" },
  { key: "discover", name: "Discover Buddy", emoji: "🧭", tag: "Food, travel & student hacks.", color: "#F43F5E", bg: "#FFF1F2" },
  { key: "helper", name: "Helper Buddy", emoji: "✨", tag: "Orchestrator — cross-domain reasoning", color: "#A855F7", bg: "#FAF5FF" },
];

export default function ChatCenter() {
  const nav = useNavigate();
  const [lb, setLb] = useState(null);
  const [insights, setInsights] = useState([]);
  const [weekly, setWeekly] = useState(null);
  useEffect(() => {
    api.get("/life-balance").then((r) => setLb(r.data));
    api.get("/insights/daily").then((r) => setInsights(r.data));
    api.get("/insights/weekly").then((r) => setWeekly(r.data));
  }, []);
  return (
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Chat with your buddies ✨" subtitle="Pick a buddy to start chatting" gradient />
      <div className="px-5 mt-4 space-y-2.5">
        {BUDDIES.map((b) => (
          <button
            key={b.key} onClick={() => nav(`/chat/${b.key}`)}
            data-testid={`buddy-card-${b.key}`}
            className="w-full flex items-center gap-3 p-3.5 rounded-2xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition active:scale-[0.98]"
          >
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" style={{ background: b.bg }}>
              {b.emoji}
            </div>
            <div className="flex-1 text-left">
              <div className="font-display font-bold text-sm" style={{ color: b.color }}>{b.name}</div>
              <div className="text-[11px] text-slate-500">{b.tag}</div>
            </div>
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </button>
        ))}
      </div>

      {/* Helper Buddy command center inline */}
      <div data-domain="helper" className="mt-4 px-5 space-y-3">
        <h3 className="font-display font-bold text-base text-slate-700">Helper Buddy · Command Center</h3>
        {lb && (
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-500 font-semibold">LIFE BALANCE</div>
                <div className="font-display font-bold text-4xl mt-0.5 bdy-text">{lb.overall}</div>
              </div>
              <div className="w-28 h-28">
                <ResponsiveContainer>
                  <RadarChart data={lb.domains} outerRadius={40}>
                    <PolarGrid stroke="#E2E8F0" />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 9, fill: "#64748B" }} />
                    <Radar dataKey="score" stroke="#A855F7" fill="#A855F7" fillOpacity={0.35} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="mt-2 space-y-1.5">
              {lb.domains.map((d) => (
                <div key={d.name}>
                  <div className="flex justify-between text-[11px]"><span className="font-semibold text-slate-600">{d.name}</span><span className="text-slate-500">{d.score}</span></div>
                  <div className="h-1.5 rounded-full bg-slate-100 mt-0.5"><div className="h-full bdy-bg rounded-full" style={{ width: `${d.score}%` }} /></div>
                </div>
              ))}
            </div>
          </Card>
        )}

        <Card>
          <h4 className="font-display font-bold text-sm">Daily Insights</h4>
          <div className="space-y-2 mt-2">
            {insights.map((i, idx) => (
              <InsightCard key={idx} icon={Sparkles} title={i.title} text={i.detail} />
            ))}
          </div>
        </Card>

        {weekly && (
          <Card>
            <h4 className="font-display font-bold text-sm">Weekly Review</h4>
            <div className="grid grid-cols-2 gap-2 mt-3">
              {weekly.scorecard.map((s) => (
                <div key={s.domain} className="p-2 rounded-xl bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">{s.domain}</div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-bold text-lg">{s.score}</span>
                    <span className={`text-[11px] font-bold ${s.trend.startsWith("+") ? "text-emerald-600" : "text-rose-600"}`}>{s.trend}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3">
              <div className="text-[11px] text-slate-500 font-semibold">HIGHLIGHTS</div>
              <ul className="text-xs text-slate-700 mt-1 space-y-0.5">{weekly.highlights.map((h, i) => <li key={i}>• {h}</li>)}</ul>
            </div>
            <div className="mt-3 p-2.5 rounded-xl bdy-soft">
              <div className="text-[11px] font-bold bdy-text">NEXT WEEK FOCUS</div>
              <p className="text-xs text-slate-700 mt-1">{weekly.next_week_focus}</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
