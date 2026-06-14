import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { EmptyState } from "../components/EmptyState";
import { Wallet, TrendingUp, AlertTriangle, CreditCard, Plane, ShieldCheck, PiggyBank, Users, Sparkles, Plus, Pencil, Check, X, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, LineChart, Line, Cell } from "recharts";
import PageTransition from "../components/PageTransition";

const Ring = ({ pct, value, label }) => {
  const r = 60, c = 2 * Math.PI * r;
  return (
    <div className="relative w-44 h-44 mx-auto">
      <svg width="176" height="176" className="transform -rotate-90">
        <circle cx="88" cy="88" r={r} stroke="#E2E8F0" strokeWidth="14" fill="none" />
        <circle cx="88" cy="88" r={r} stroke="var(--bdy)" strokeWidth="14" fill="none"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-xs text-slate-500">{label}</div>
        <div className="font-display font-bold text-2xl">{value}</div>
        <div className="text-xs font-semibold text-[color:var(--bdy)]">{pct}%</div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [b, setB] = useState(null);
  useEffect(() => { api.get("/budget").then((r) => setB(r.data)); }, []);
  if (!b) return null;
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="text-center">
          <div className="text-xs text-slate-500 font-semibold">MONTHLY BUDGET</div>
        </div>
        <Ring pct={b.percent_used} value={`₹${b.total_spent.toLocaleString()}`} label={`of ₹${b.total_allocated.toLocaleString()}`} />
        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="p-2 rounded-xl bg-slate-50 text-center">
            <div className="text-[10px] text-slate-500">Spent</div>
            <div className="font-bold text-sm">₹{b.total_spent}</div>
          </div>
          <div className="p-2 rounded-xl bg-slate-50 text-center">
            <div className="text-[10px] text-slate-500">Left</div>
            <div className="font-bold text-sm text-emerald-600">₹{b.remaining}</div>
          </div>
          <div className="p-2 rounded-xl bg-slate-50 text-center">
            <div className="text-[10px] text-slate-500">Used</div>
            <div className="font-bold text-sm">{b.percent_used}%</div>
          </div>
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-base">Categories</h3>
        <div className="space-y-2.5 mt-3" data-testid="budget-categories">
          {b.categories.map((c) => {
            const pct = Math.round((c.spent / c.allocated) * 100);
            return (
              <div key={c.id}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-700">{c.name}</span>
                  <span className="text-slate-500">₹{c.spent} / ₹{c.allocated}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className={`h-full rounded-full ${pct > 90 ? "bg-rose-500" : pct > 70 ? "bg-amber-500" : "bdy-bg"}`}
                    style={{ width: `${Math.min(pct, 100)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </Card>
      <InsightCard icon={Sparkles} title="AI Insight" text="You spent 22% more on snacks this week. Hostel mess twice could save ~₹250." />
    </div>
  );
};

const Expenses = () => {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/expenses").then((r) => setList(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-base">Transactions</h3>
        </div>
        <div className="mt-3 space-y-2" data-testid="transaction-feed">
          {list.map((e) => (
            <div key={e.id} className="flex items-center gap-3 py-2 border-b border-slate-100">
              <div className="w-9 h-9 rounded-xl bdy-soft flex items-center justify-center text-[color:var(--bdy)] font-bold text-xs">
                {(e.merchant || e.category).slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold">{e.merchant || "Expense"}</div>
                <div className="text-[11px] text-slate-500 capitalize">{e.category}</div>
              </div>
              <div className="font-bold text-sm">-₹{e.amount}</div>
            </div>
          ))}
          {list.length === 0 && (
            <EmptyState
              icon={Wallet}
              title="No transactions yet"
              description="Log your first expense from the Daily Hub to start tracking spending."
              useCard={false}
              testid="expenses-empty-state"
            />
          )}
        </div>
      </Card>
    </div>
  );
};

const CashFlow = () => {
  const [data, setData] = useState({ forecast_remaining: 0, overspend: 0, underspend: 0, days_left: 0, trend: [] });
  useEffect(() => { api.get("/cashflow").then((r) => setData(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Month-End Forecast</h3>
        <div className={`font-display font-bold text-3xl mt-2 ${data.forecast_remaining >= 0 ? "bdy-text" : "text-rose-600"}`} data-testid="forecast-value">
          {data.forecast_remaining >= 0 ? "₹" : "-₹"}{Math.abs(data.forecast_remaining).toLocaleString()}
        </div>
        <p className="text-xs text-slate-500">
          {data.forecast_remaining >= 0 ? "Predicted leftover by month end" : "Projected overshoot"} · {data.days_left} days left
        </p>
        <div className="h-28 mt-3" data-testid="trend-chart">
          <ResponsiveContainer>
            <LineChart data={data.trend}>
              <XAxis dataKey="d" hide />
              <Line type="monotone" dataKey="v" stroke="var(--bdy)" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="p-3 rounded-xl bg-emerald-50">
            <div className="text-[10px] text-emerald-700 font-semibold">UNDERSPEND</div>
            <div className="font-bold text-emerald-700">₹{data.underspend.toLocaleString()}</div>
          </div>
          <div className="p-3 rounded-xl bg-rose-50">
            <div className="text-[10px] text-rose-700 font-semibold">OVERSPEND</div>
            <div className="font-bold text-rose-700">₹{data.overspend.toLocaleString()}</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

const Alerts = () => {
  const [threshold, setThreshold] = useState(75);
  const [budget, setBudget] = useState(null);
  useEffect(() => { api.get("/budget").then((r) => setBudget(r.data)); }, []);

  const alerts = budget ? budget.categories
    .map((c) => ({ ...c, pct: c.allocated ? Math.round((c.spent / c.allocated) * 100) : 0 }))
    .filter((c) => c.pct >= threshold)
    .sort((a, b) => b.pct - a.pct) : [];

  const onTrack = budget ? budget.categories
    .map((c) => ({ ...c, pct: c.allocated ? Math.round((c.spent / c.allocated) * 100) : 0 }))
    .filter((c) => c.pct < threshold) : [];

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex items-center gap-2 text-rose-600">
          <AlertTriangle className="w-4 h-4" />
          <span className="font-display font-bold">{alerts.length} Alert{alerts.length !== 1 ? "s" : ""} Active</span>
        </div>
        <div className="mt-3 space-y-2">
          {alerts.map((c) => (
            <div key={c.id} className={`p-3 rounded-xl ${c.pct > 90 ? "bg-rose-50 border border-rose-100" : "bg-amber-50 border border-amber-100"}`}>
              <div className={`text-sm font-semibold ${c.pct > 90 ? "text-rose-700" : "text-amber-700"}`}>{c.name} at {c.pct}%</div>
              <div className={`text-xs ${c.pct > 90 ? "text-rose-600" : "text-amber-600"}`}>₹{c.spent.toLocaleString()} of ₹{c.allocated.toLocaleString()} used</div>
            </div>
          ))}
          {onTrack.slice(0, 3).map((c) => (
            <div key={c.id} className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
              <div className="text-sm font-semibold text-emerald-700">{c.name} on track ({c.pct}%)</div>
            </div>
          ))}
          {!budget && <p className="text-xs text-slate-400 text-center py-4">Loading budget data…</p>}
          {budget && alerts.length === 0 && <p className="text-xs text-emerald-600 text-center py-2">All categories within budget. 🎉</p>}
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-sm">Alert threshold</h3>
        <p className="text-xs text-slate-500">Notify me when category exceeds {threshold}%</p>
        <input type="range" min="50" max="100" value={threshold} onChange={(e) => setThreshold(parseInt(e.target.value))}
          className="bdy-slider mt-3" style={{ "--val": `${(threshold - 50) * 2}%` }}
          data-testid="alert-threshold"
          aria-label={`Alert threshold at ${threshold} percent`} />
      </Card>
    </div>
  );
};

const Subs = () => {
  const [data, setData] = useState({ items: [], monthly_total: 0 });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", amount: "", renews_on: "", icon: "credit-card" });
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/subscriptions").then((r) => setData(r.data));
  useEffect(() => { load(); }, []);

  const addSub = async () => {
    if (!form.name.trim() || !form.amount) return;
    setBusy(true);
    await api.post("/subscriptions", { name: form.name.trim(), amount: parseFloat(form.amount), renews_on: form.renews_on, icon: form.icon });
    setForm({ name: "", amount: "", renews_on: "", icon: "credit-card" });
    setShowForm(false);
    await load();
    setBusy(false);
  };

  const removeSub = async (id) => {
    if (!window.confirm("Remove this subscription?")) return;
    await api.delete(`/subscriptions/${id}`);
    await load();
  };

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-base">Subscriptions</h3>
          <span className="font-bold text-sm">₹{data.monthly_total}/mo</span>
        </div>
        <div className="mt-3 space-y-2" data-testid="sub-list">
          {data.items.map((s) => (
            <div key={s.id} className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-50">
              <CreditCard className="w-4 h-4 bdy-text" />
              <div className="flex-1">
                <div className="text-sm font-semibold">{s.name}</div>
                <div className="text-[11px] text-slate-500">Renews {s.renews_on}</div>
              </div>
              <span className="font-bold text-sm">₹{s.amount}</span>
              <button onClick={() => removeSub(s.id)} data-testid={`delete-sub-${s.id}`}
                aria-label={`Remove subscription ${s.name}`}
                className="w-7 h-7 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-rose-500 hover:bg-rose-50">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          {data.items.length === 0 && (
            <EmptyState
              icon={CreditCard}
              title="No subscriptions tracked"
              description="Add your recurring subscriptions to keep track of monthly commitments."
              useCard={false}
              testid="subs-empty-state"
            />
          )}
        </div>

        {!showForm ? (
          <button onClick={() => setShowForm(true)} data-testid="add-sub-toggle"
            aria-label="Add a new subscription"
            className="w-full mt-3 py-2.5 rounded-xl border border-dashed border-slate-300 text-sm font-semibold text-slate-600 flex items-center justify-center gap-1 hover:border-[color:var(--bdy)] hover:bdy-text">
            <Plus className="w-4 h-4" /> Add Subscription
          </button>
        ) : (
          <div className="mt-3 p-3 rounded-xl bg-slate-50 space-y-2" data-testid="add-sub-form">
            <input data-testid="sub-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Subscription name" aria-label="Enter subscription name" className="w-full bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            <div className="flex gap-2">
              <input data-testid="sub-amount" type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="₹ Amount" aria-label="Enter subscription amount" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
              <input data-testid="sub-renews" type="date" value={form.renews_on} onChange={(e) => setForm({ ...form, renews_on: e.target.value })}
                aria-label="Select renewal date" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            </div>
            <div className="flex gap-2">
              <button onClick={addSub} disabled={busy || !form.name.trim()} data-testid="save-sub-btn"
                aria-label="Save subscription"
                className="flex-1 bdy-bg text-white font-semibold py-2 rounded-xl text-sm disabled:opacity-50 active:scale-95">
                Save
              </button>
              <button onClick={() => setShowForm(false)}
                aria-label="Cancel adding subscription"
                className="px-4 py-2 rounded-xl bg-slate-200 text-slate-700 text-sm font-semibold">
                Cancel
              </button>
            </div>
          </div>
        )}
        <InsightCard icon={Users} title="Sharing tip" text="Split Netflix with 2 friends → save ₹133/month." />
      </Card>
    </div>
  );
};

const FoodTravel = () => {
  const [budget, setBudget] = useState(null);
  useEffect(() => { api.get("/budget").then((r) => setBudget(r.data)); }, []);

  const foodCat = budget?.categories.find((c) => c.name.toLowerCase() === "food");
  const travelCat = budget?.categories.find((c) => c.name.toLowerCase() === "transport");
  const foodSpent = foodCat?.spent || 0;
  const foodAlloc = foodCat?.allocated || 1;
  const travelSpent = travelCat?.spent || 0;
  const travelAlloc = travelCat?.allocated || 1;
  const foodPct = Math.round((foodSpent / foodAlloc) * 100);
  const travelPct = Math.round((travelSpent / travelAlloc) * 100);

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Food & Travel</h3>
        {!budget ? (
          <p className="text-xs text-slate-400 text-center py-4">Loading…</p>
        ) : (
          <div className="grid grid-cols-2 gap-2 mt-3">
            <div className="p-3 rounded-2xl bdy-soft border border-[color:var(--bdy)]/15">
              <div className="text-[10px] font-semibold uppercase text-slate-600">Food</div>
              <div className="font-display font-bold text-xl mt-1">₹{foodSpent.toLocaleString()}</div>
              <div className="text-[11px] text-slate-500">{foodPct}% of ₹{foodAlloc.toLocaleString()}</div>
            </div>
            <div className="p-3 rounded-2xl bg-emerald-50 border border-emerald-100">
              <div className="text-[10px] font-semibold uppercase text-emerald-700">Travel</div>
              <div className="font-display font-bold text-xl mt-1">₹{travelSpent.toLocaleString()}</div>
              <div className="text-[11px] text-emerald-600">{travelPct}% of ₹{travelAlloc.toLocaleString()}</div>
            </div>
          </div>
        )}
        <InsightCard icon={Plane} title="Mode comparison" text="Metro saves ₹90/day vs rideshare for the same route." />
      </Card>
    </div>
  );
};

const Emergency = () => {
  const [fund, setFund] = useState(null);
  useEffect(() => {
    api.get("/savings").then((r) => {
      const goals = r.data || [];
      const emergency = goals.find((g) => g.name.toLowerCase().includes("emergency")) || goals[0];
      setFund(emergency || null);
    });
  }, []);

  if (!fund) {
    return (
      <div className="mx-5 mt-4 space-y-3">
        <Card>
          <h3 className="font-display font-bold text-base text-center">Emergency Fund</h3>
          <p className="text-xs text-slate-400 text-center py-6">No savings goals found. Create one in the Savings tab to track your emergency fund.</p>
        </Card>
      </div>
    );
  }

  const target = fund.target || 1;
  const saved = fund.saved || 0;
  const pct = Math.round((saved / target) * 100);
  const r = 70, c = Math.PI * r;
  const remaining = target - saved;
  const monthsLeft = remaining > 0 ? Math.ceil(remaining / 3000) : 0;

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base text-center">{fund.emoji} {fund.name}</h3>
        <div className="relative w-48 h-28 mx-auto mt-3">
          <svg width="192" height="112" viewBox="0 0 192 112">
            <path d={`M 16 96 A ${r} ${r} 0 0 1 176 96`} stroke="#E2E8F0" strokeWidth="14" fill="none" strokeLinecap="round" />
            <path d={`M 16 96 A ${r} ${r} 0 0 1 176 96`} stroke="var(--bdy)" strokeWidth="14" fill="none"
              strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - Math.min(pct, 100) / 100)} />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
            <div className="font-display font-bold text-3xl">{pct}%</div>
            <div className="text-[11px] text-slate-500">₹{saved.toLocaleString()} / ₹{target.toLocaleString()}</div>
          </div>
        </div>
        {remaining > 0 && (
          <InsightCard icon={ShieldCheck} title="Almost there!"
            text={`Save ₹3,000/month to hit your goal in ~${monthsLeft} month${monthsLeft > 1 ? "s" : ""}.`} />
        )}
        {remaining <= 0 && (
          <InsightCard icon={ShieldCheck} title="Goal reached! 🎉" text="You've hit your target. Consider setting a higher goal." />
        )}
      </Card>
    </div>
  );
};

const Savings = () => {
  const [g, setG] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", target: "", saved: "", emoji: "🎯" });
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/savings").then((r) => setG(r.data));
  useEffect(() => { load(); }, []);

  const addGoal = async () => {
    if (!form.name.trim() || !form.target) return;
    setBusy(true);
    await api.post("/savings", { name: form.name.trim(), target: parseFloat(form.target), saved: parseFloat(form.saved) || 0, emoji: form.emoji });
    setForm({ name: "", target: "", saved: "", emoji: "🎯" });
    setShowForm(false);
    await load();
    setBusy(false);
  };

  const removeGoal = async (id) => {
    if (!window.confirm("Delete this savings goal?")) return;
    await api.delete(`/savings/${id}`);
    await load();
  };

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Savings Goals</h3>
        <div className="mt-3 space-y-3" data-testid="savings-list">
          {g.map((s) => {
            const pct = s.target ? Math.round((s.saved / s.target) * 100) : 0;
            return (
              <div key={s.id} className="p-3 rounded-xl bg-slate-50">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-semibold">{s.emoji} {s.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold bdy-text">{pct}%</span>
                    <button onClick={() => removeGoal(s.id)} data-testid={`delete-savings-${s.id}`}
                      className="w-6 h-6 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-rose-500 hover:bg-rose-50">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <div className="h-2 mt-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full bdy-bg" style={{ width: `${Math.min(pct, 100)}%` }} />
                </div>
                <div className="text-[11px] text-slate-500 mt-1">₹{s.saved.toLocaleString()} of ₹{s.target.toLocaleString()}</div>
              </div>
            );
          })}
          {g.length === 0 && (
            <EmptyState
              icon={PiggyBank}
              title="No savings goals yet"
              description="Create a savings goal below to start tracking your progress toward what matters."
              useCard={false}
              testid="savings-empty-state"
            />
          )}
        </div>

        {!showForm ? (
          <button onClick={() => setShowForm(true)} data-testid="add-savings-toggle"
            aria-label="Create a new savings goal"
            className="w-full mt-3 py-2.5 rounded-xl border border-dashed border-slate-300 text-sm font-semibold text-slate-600 flex items-center justify-center gap-1 hover:border-[color:var(--bdy)] hover:bdy-text">
            <Plus className="w-4 h-4" /> New Savings Goal
          </button>
        ) : (
          <div className="mt-3 p-3 rounded-xl bg-slate-50 space-y-2" data-testid="add-savings-form">
            <div className="flex gap-2">
              <input data-testid="savings-emoji" value={form.emoji} onChange={(e) => setForm({ ...form, emoji: e.target.value })}
                aria-label="Choose emoji for savings goal" className="w-12 bg-white rounded-xl px-2 py-2 text-center text-sm border border-slate-200 outline-none" maxLength={2} />
              <input data-testid="savings-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Goal name" aria-label="Enter savings goal name" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            </div>
            <div className="flex gap-2">
              <input data-testid="savings-target" type="number" value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value })}
                placeholder="₹ Target amount" aria-label="Enter target savings amount" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
              <input data-testid="savings-saved" type="number" value={form.saved} onChange={(e) => setForm({ ...form, saved: e.target.value })}
                placeholder="₹ Already saved" aria-label="Enter amount already saved" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            </div>
            <div className="flex gap-2">
              <button onClick={addGoal} disabled={busy || !form.name.trim() || !form.target} data-testid="save-savings-btn"
                aria-label="Create savings goal"
                className="flex-1 bdy-bg text-white font-semibold py-2 rounded-xl text-sm disabled:opacity-50 active:scale-95">
                Create Goal
              </button>
              <button onClick={() => setShowForm(false)}
                aria-label="Cancel creating savings goal"
                className="px-4 py-2 rounded-xl bg-slate-200 text-slate-700 text-sm font-semibold">
                Cancel
              </button>
            </div>
          </div>
        )}
        <InsightCard icon={PiggyBank} title="Simulation tip" text="Skip 2 cafe visits/week → laptop fund 5 weeks sooner." />
      </Card>
    </div>
  );
};

const Splits = () => {
  const [data, setData] = useState({ items: [], net_balance: 0 });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", total: "", with_person: "", you_paid: "" });
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/splits").then((r) => setData(r.data));
  useEffect(() => { load(); }, []);

  const addSplit = async () => {
    if (!form.title.trim() || !form.total || !form.with_person.trim()) return;
    const total = parseFloat(form.total);
    const youPaid = parseFloat(form.you_paid) || 0;
    const owesYou = youPaid - (total / 2);
    setBusy(true);
    await api.post("/splits", { title: form.title.trim(), total, with_person: form.with_person.trim(), you_paid: youPaid, owes_you: Math.round(owesYou) });
    setForm({ title: "", total: "", with_person: "", you_paid: "" });
    setShowForm(false);
    await load();
    setBusy(false);
  };

  const removeSplit = async (id) => {
    if (!window.confirm("Remove this split?")) return;
    await api.delete(`/splits/${id}`);
    await load();
  };

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Split Bills</h3>
        <div className={`mt-2 p-3 rounded-xl ${data.net_balance >= 0 ? "bg-emerald-50" : "bg-rose-50"}`}>
          <div className="text-[11px] font-semibold text-slate-600">NET BALANCE</div>
          <div className={`font-display font-bold text-xl ${data.net_balance >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
            {data.net_balance >= 0 ? "+" : ""}₹{data.net_balance}
          </div>
          <p className="text-[11px] text-slate-600 mt-1">
            {data.net_balance >= 0 ? "Friends owe you" : "You owe friends"}
          </p>
        </div>
        <div className="mt-3 space-y-2" data-testid="splits-list">
          {data.items.map((s) => (
            <div key={s.id} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl">
              <div className="flex-1">
                <div className="text-sm font-semibold">{s.title}</div>
                <div className="text-[11px] text-slate-500">with {s.with_person}</div>
              </div>
              <span className={`font-bold text-sm ${s.owes_you >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                {s.owes_you >= 0 ? "+" : ""}₹{s.owes_you}
              </span>
              <button onClick={() => removeSplit(s.id)} data-testid={`delete-split-${s.id}`}
                className="w-7 h-7 ml-2 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-rose-500 hover:bg-rose-50">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          {data.items.length === 0 && (
            <EmptyState
              icon={Users}
              title="No splits yet"
              description="Split a bill with friends to track who owes what."
              useCard={false}
              testid="splits-empty-state"
            />
          )}
        </div>

        {!showForm ? (
          <button onClick={() => setShowForm(true)} data-testid="add-split-toggle"
            aria-label="Add a new split bill"
            className="w-full mt-3 py-2.5 rounded-xl border border-dashed border-slate-300 text-sm font-semibold text-slate-600 flex items-center justify-center gap-1 hover:border-[color:var(--bdy)] hover:bdy-text">
            <Plus className="w-4 h-4" /> Add Split Bill
          </button>
        ) : (
          <div className="mt-3 p-3 rounded-xl bg-slate-50 space-y-2" data-testid="add-split-form">
            <input data-testid="split-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="What was it for?" aria-label="Enter split bill description" className="w-full bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            <div className="flex gap-2">
              <input data-testid="split-total" type="number" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })}
                placeholder="₹ Total bill" aria-label="Enter total bill amount" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
              <input data-testid="split-person" value={form.with_person} onChange={(e) => setForm({ ...form, with_person: e.target.value })}
                placeholder="Split with" aria-label="Enter person to split with" className="flex-1 bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            </div>
            <input data-testid="split-you-paid" type="number" value={form.you_paid} onChange={(e) => setForm({ ...form, you_paid: e.target.value })}
              placeholder="₹ You paid (0 if they paid)" aria-label="Enter amount you paid" className="w-full bg-white rounded-xl px-3 py-2 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]" />
            <div className="flex gap-2">
              <button onClick={addSplit} disabled={busy || !form.title.trim() || !form.total || !form.with_person.trim()} data-testid="save-split-btn"
                aria-label="Save split bill"
                className="flex-1 bdy-bg text-white font-semibold py-2 rounded-xl text-sm disabled:opacity-50 active:scale-95">
                Save Split
              </button>
              <button onClick={() => setShowForm(false)}
                aria-label="Cancel adding split"
                className="px-4 py-2 rounded-xl bg-slate-200 text-slate-700 text-sm font-semibold">
                Cancel
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

const BudgetEditor = () => {
  const [cats, setCats] = useState([]);
  const [profile, setProfile] = useState({ monthly_income: 0 });
  const [income, setIncome] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ name: "", allocated: "" });
  const [newCat, setNewCat] = useState({ name: "", allocated: "" });
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [b, p] = await Promise.all([api.get("/budget"), api.get("/profile")]);
    setCats(b.data.categories);
    setProfile(p.data);
    setIncome(String(p.data.monthly_income || ""));
  };
  useEffect(() => { load(); }, []);

  const totalAlloc = cats.reduce((s, c) => s + c.allocated, 0);

  const autoBalance = async () => {
    const v = parseFloat(income);
    if (!v || v <= 0) return;
    setBusy(true);
    await api.post("/budget/auto-balance", { income: v });
    await load();
    setBusy(false);
  };

  const startEdit = (c) => {
    setEditingId(c.id);
    setDraft({ name: c.name, allocated: c.allocated });
  };

  const saveEdit = async () => {
    if (!draft.name.trim()) return;
    setBusy(true);
    await api.patch(`/budget/${editingId}`, { name: draft.name.trim(), allocated: parseFloat(draft.allocated) || 0 });
    setEditingId(null);
    await load();
    setBusy(false);
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this category? Tracked expenses will remain.")) return;
    await api.delete(`/budget/${id}`);
    await load();
  };

  const addCat = async () => {
    if (!newCat.name.trim()) return;
    setBusy(true);
    await api.post("/budget", { name: newCat.name.trim(), allocated: parseFloat(newCat.allocated) || 0 });
    setNewCat({ name: "", allocated: "" });
    await load();
    setBusy(false);
  };

  const incomeDiff = totalAlloc - (parseFloat(income) || 0);

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card className="bdy-soft border border-[color:var(--bdy)]/15">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 bdy-text" />
          <h3 className="font-display font-bold text-base">Auto-balance with 50/30/20</h3>
        </div>
        <p className="text-xs text-slate-600 mt-1">Tell us your monthly income — we'll split allocations across Needs (50%), Wants (30%), Savings (20%).</p>
        <div className="flex gap-2 mt-3">
          <div className="flex-1 relative">
            <span className="absolute left-3 top-2.5 text-slate-500 text-sm font-semibold">₹</span>
            <input
              data-testid="income-input"
              type="number" value={income} onChange={(e) => setIncome(e.target.value)}
              placeholder="Monthly income"
              className="w-full bg-white rounded-xl pl-7 pr-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
            />
          </div>
          <button
            onClick={autoBalance}
            disabled={busy || !income}
            data-testid="auto-balance-btn"
            className="px-4 py-2.5 rounded-xl bdy-bg text-white font-semibold text-sm disabled:opacity-50 active:scale-95"
          >
            Apply
          </button>
        </div>
        {parseFloat(income) > 0 && (
          <div className={`mt-2 text-[11px] font-semibold ${Math.abs(incomeDiff) < 1 ? "text-emerald-600" : incomeDiff > 0 ? "text-rose-600" : "text-amber-600"}`}>
            {Math.abs(incomeDiff) < 1
              ? "Balanced ✓ Total matches income"
              : incomeDiff > 0
                ? `Over income by ₹${incomeDiff.toLocaleString()}`
                : `Under income by ₹${Math.abs(incomeDiff).toLocaleString()} — extra savings room`}
          </div>
        )}
      </Card>

      <Card>
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-display font-bold text-base">Envelope Budgeting</h3>
            <p className="text-xs text-slate-500">Allocate per category. Edit anytime.</p>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-slate-500 font-semibold">TOTAL</div>
            <div className="font-display font-bold text-lg bdy-text">₹{totalAlloc.toLocaleString()}</div>
          </div>
        </div>

        <div className="mt-4 space-y-2" data-testid="budget-edit-list">
          {cats.map((c) => {
            const isEditing = editingId === c.id;
            const pct = c.allocated ? Math.round((c.spent / c.allocated) * 100) : 0;
            return (
              <div key={c.id} className="p-3 rounded-xl bg-slate-50" data-testid={`budget-row-${c.id}`}>
                {isEditing ? (
                  <div className="flex items-center gap-2">
                    <input
                      data-testid="edit-cat-name"
                      value={draft.name}
                      onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                      className="flex-1 bg-white rounded-lg px-2.5 py-1.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
                      placeholder="Name"
                    />
                    <input
                      data-testid="edit-cat-amount"
                      type="number"
                      value={draft.allocated}
                      onChange={(e) => setDraft({ ...draft, allocated: e.target.value })}
                      className="w-24 bg-white rounded-lg px-2.5 py-1.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
                      placeholder="₹"
                    />
                    <button
                      onClick={saveEdit}
                      disabled={busy}
                      data-testid={`save-edit-${c.id}`}
                      className="w-8 h-8 rounded-lg bdy-bg text-white flex items-center justify-center active:scale-95"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      data-testid={`cancel-edit-${c.id}`}
                      className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="text-sm font-semibold">{c.name}</div>
                        <div className="text-[11px] text-slate-500">
                          ₹{c.spent.toLocaleString()} of ₹{c.allocated.toLocaleString()}
                        </div>
                      </div>
                      <button
                        onClick={() => startEdit(c)}
                        data-testid={`edit-cat-${c.id}`}
                        className="w-7 h-7 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:bdy-text"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => remove(c.id)}
                        data-testid={`delete-cat-${c.id}`}
                        className="w-7 h-7 ml-1 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-rose-500 hover:bg-rose-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="h-1.5 mt-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        className={`h-full ${pct > 90 ? "bg-rose-500" : pct > 70 ? "bg-amber-500" : "bdy-bg"}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </>
                )}
              </div>
            );
          })}
          {cats.length === 0 && (
            <p className="text-xs text-slate-400 text-center py-4">No categories yet. Add your first one below.</p>
          )}
        </div>
      </Card>

      <Card>
        <h4 className="font-display font-bold text-sm">Add Custom Category</h4>
        <p className="text-xs text-slate-500">Books, gym, subscriptions, anything you track.</p>
        <div className="flex gap-2 mt-3">
          <input
            data-testid="new-cat-name"
            value={newCat.name}
            onChange={(e) => setNewCat({ ...newCat, name: e.target.value })}
            placeholder="Category name"
            className="flex-1 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
          />
          <input
            data-testid="new-cat-amount"
            type="number"
            value={newCat.allocated}
            onChange={(e) => setNewCat({ ...newCat, allocated: e.target.value })}
            placeholder="₹"
            className="w-24 bg-slate-50 rounded-xl px-3 py-2.5 text-sm border border-slate-200 outline-none focus:border-[color:var(--bdy)]"
          />
        </div>
        <button
          onClick={addCat}
          disabled={busy || !newCat.name.trim()}
          data-testid="add-cat-btn"
          className="w-full mt-3 bdy-bg text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-1 disabled:opacity-50 active:scale-95"
        >
          <Plus className="w-4 h-4" /> Add Category
        </button>
        <InsightCard
          icon={Sparkles}
          title="Wizard tip"
          text="Use the 50/30/20 rule — 50% needs, 30% wants, 20% savings. Adjust allocations till total matches your monthly income."
        />
      </Card>
    </div>
  );
};

const TABS = [
  { key: "dash", label: "Dashboard", C: Dashboard },
  { key: "budget", label: "Budget", C: BudgetEditor },
  { key: "exp", label: "Expenses", C: Expenses },
  { key: "cash", label: "Cash Flow", C: CashFlow },
  { key: "alerts", label: "Alerts", C: Alerts },
  { key: "subs", label: "Subs", C: Subs },
  { key: "ft", label: "Food/Travel", C: FoodTravel },
  { key: "emerg", label: "Emergency", C: Emergency },
  { key: "save", label: "Savings", C: Savings },
  { key: "split", label: "Splits", C: Splits },
];

export default function FinanceBuddy() {
  const [tab, setTab] = useState("dash");
  const Active = TABS.find((t) => t.key === tab).C;
  return (
    <PageTransition className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Finance Buddy 🦉" subtitle="Track. Plan. Achieve." gradient />
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="fin-tab" />
      <Active />
    </PageTransition>
  );
}
