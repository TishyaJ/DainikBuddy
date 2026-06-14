import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { Card, InsightCard } from "../components/SubTabs";
import { api } from "../lib/api";
import { Sparkles, ChevronRight, WifiOff, AlertTriangle, RefreshCw, Info } from "lucide-react";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from "recharts";
import { useOffline } from "../context/OfflineContext";

const BUDDIES = [
  { key: "finance", name: "Finance Buddy", emoji: "🦉", tag: "Savings. Budgeting. Smart choices.", color: "#3B82F6", bg: "#EFF6FF" },
  { key: "wellness", name: "Wellness Buddy", emoji: "☁️", tag: "Here for your mind and body.", color: "#A78BFA", bg: "#F5F3FF" },
  { key: "discover", name: "Discover Buddy", emoji: "🧭", tag: "Food, travel & student hacks.", color: "#F43F5E", bg: "#FFF1F2" },
  { key: "helper", name: "Helper Buddy", emoji: "✨", tag: "Orchestrator — cross-domain reasoning", color: "#A855F7", bg: "#FAF5FF" },
];

export default function ChatCenter() {
  const nav = useNavigate();
  const { isOnline } = useOffline();
  const [lb, setLb] = useState(null);
  const [lbError, setLbError] = useState(false);
  const [insights, setInsights] = useState([]);
  const [insightsError, setInsightsError] = useState(false);
  const [weekly, setWeekly] = useState(null);
  const [weeklyError, setWeeklyError] = useState(false);

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

  const fetchWeekly = useCallback(async () => {
    try {
      setWeeklyError(false);
      const res = await api.get("/insights/weekly");
      setWeekly(res.data);
    } catch {
      setWeeklyError(true);
    }
  }, []);

  useEffect(() => {
    fetchLifeBalance();
    fetchInsights();
    fetchWeekly();
  }, [fetchLifeBalance, fetchInsights, fetchWeekly]);

  if (!isOnline) {
    return (
      <div className="flex-1 overflow-auto scroll-area pb-4">
        <Header title="Chat with your buddies ✨" subtitle="Pick a buddy to start chatting" gradient />
        <div className="flex flex-col items-center justify-center px-5 py-16" data-testid="chat-offline-message">
          <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mb-4">
            <WifiOff className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="font-display font-bold text-lg text-slate-800">Chat requires internet</h2>
          <p className="text-sm text-slate-500 text-center mt-2 max-w-xs">
            AI chat features need an active internet connection. Your data is saved locally and will sync when you're back online.
          </p>
        </div>
      </div>
    );
  }

  // Identify domains with no data (score 0) to encourage user input
  const missingDomains = lb?.domains?.filter((d) => d.score === 0) || [];
  const hasPartialData = lb?.partial_data === true;

  return (
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Chat with your buddies ✨" subtitle="Pick a buddy to start chatting" gradient />
      <div className="px-5 mt-4 space-y-2.5">
        {BUDDIES.map((b) => (
          <button
            key={b.key} onClick={() => nav(`/chat/${b.key}`)}
            data-testid={`buddy-card-${b.key}`}
            aria-label={`Chat with ${b.name}`}
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

        {/* Life-Balance Section */}
        {lbError ? (
          <Card data-testid="chat-lb-error">
            <div className="flex flex-col items-center py-4 gap-2">
              <AlertTriangle className="w-6 h-6 text-rose-500" />
              <p className="text-sm text-slate-600">Could not load life-balance data</p>
              <button
                onClick={fetchLifeBalance}
                data-testid="chat-lb-retry-btn"
                aria-label="Retry loading life-balance data"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
              >
                <RefreshCw className="w-3 h-3" /> Retry
              </button>
            </div>
          </Card>
        ) : lb ? (
          <Card data-testid="chat-life-balance">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-500 font-semibold">LIFE BALANCE</div>
                <div className="font-display font-bold text-4xl mt-0.5 bdy-text">{lb.overall}</div>
                {hasPartialData && (
                  <div className="flex items-center gap-1 mt-1">
                    <Info className="w-3 h-3 text-amber-500" />
                    <span className="text-[10px] text-amber-600 font-medium">
                      Based on {lb.days_used ? Math.max(...Object.values(lb.days_used)) : "< 7"} days of data
                    </span>
                  </div>
                )}
              </div>
              <div className="w-28 h-28">
                <ResponsiveContainer>
                  <RadarChart data={lb.domains} outerRadius={40}>
                    <PolarGrid stroke="#E2E8F0" />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 9, fill: "#64748B" }} />
                    <Radar dataKey="score" stroke="var(--bdy)" fill="var(--bdy)" fillOpacity={0.35} />
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
            {/* Missing domain data encouragement */}
            {missingDomains.length > 0 && (
              <div className="mt-3 p-2.5 rounded-xl bg-amber-50 border border-amber-100" data-testid="chat-missing-domains">
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
        ) : (
          <Card>
            <div className="h-[120px] flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-slate-300 border-t-[color:var(--bdy)] rounded-full animate-spin" />
            </div>
          </Card>
        )}

        {/* Daily Insights Section */}
        {insightsError ? (
          <Card data-testid="chat-insights-error">
            <div className="flex flex-col items-center py-4 gap-2">
              <AlertTriangle className="w-6 h-6 text-rose-500" />
              <p className="text-sm text-slate-600">Could not load daily insights</p>
              <button
                onClick={fetchInsights}
                data-testid="chat-insights-retry-btn"
                aria-label="Retry loading daily insights"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
              >
                <RefreshCw className="w-3 h-3" /> Retry
              </button>
            </div>
          </Card>
        ) : (
          <Card data-testid="chat-daily-insights">
            <h4 className="font-display font-bold text-sm">Daily Insights</h4>
            <div className="space-y-2 mt-2">
              {insights.length > 0 ? (
                insights.map((i, idx) => (
                  <InsightCard key={idx} icon={Sparkles} title={i.title} text={i.detail} />
                ))
              ) : (
                <div className="flex items-start gap-2 py-3" data-testid="chat-insights-empty">
                  <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-slate-500">
                    No insights yet. Log your mood, expenses, and sleep to get personalized AI recommendations based on your data.
                  </p>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Weekly Review Section */}
        {weeklyError ? (
          <Card data-testid="chat-weekly-error">
            <div className="flex flex-col items-center py-4 gap-2">
              <AlertTriangle className="w-6 h-6 text-rose-500" />
              <p className="text-sm text-slate-600">Could not load weekly review</p>
              <button
                onClick={fetchWeekly}
                data-testid="chat-weekly-retry-btn"
                aria-label="Retry loading weekly review"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bdy-bg text-white active:scale-95 transition"
              >
                <RefreshCw className="w-3 h-3" /> Retry
              </button>
            </div>
          </Card>
        ) : weekly ? (
          <Card data-testid="chat-weekly-review">
            <h4 className="font-display font-bold text-sm">Weekly Review</h4>
            <div className="grid grid-cols-2 gap-2 mt-3">
              {weekly.scorecard.map((s) => (
                <div key={s.domain} className="p-2 rounded-xl bg-slate-50">
                  <div className="text-[10px] text-slate-500 font-semibold uppercase">{s.domain}</div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-bold text-lg">{s.score ?? "—"}</span>
                    {s.trend != null && (
                      <span className={`text-[11px] font-bold ${s.trend >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                        {s.trend > 0 ? `+${s.trend}` : s.trend}
                      </span>
                    )}
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
        ) : (
          <Card>
            <div className="h-[80px] flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-slate-300 border-t-[color:var(--bdy)] rounded-full animate-spin" />
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
