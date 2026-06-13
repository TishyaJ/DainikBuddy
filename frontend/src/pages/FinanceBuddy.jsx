import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Wallet, TrendingUp, Camera, AlertTriangle, CreditCard, Plane, ShieldCheck, PiggyBank, Users, Sparkles, Plus, Pencil, Check, X, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer, LineChart, Line, Cell } from "recharts";

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
          <button data-testid="scan-receipt-btn" className="text-xs font-semibold bdy-text flex items-center gap-1">
            <Camera className="w-3.5 h-3.5" /> Scan
          </button>
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
        </div>
      </Card>
    </div>
  );
};

const CashFlow = () => {
  const trend = [
    { d: "1", v: 80 }, { d: "2", v: 120 }, { d: "3", v: 60 }, { d: "4", v: 140 },
    { d: "5", v: 90 }, { d: "6", v: 200 }, { d: "7", v: 110 }, { d: "8", v: 85 },
    { d: "9", v: 130 }, { d: "10", v: 95 }, { d: "11", v: 70 }, { d: "12", v: 180 },
    { d: "13", v: 100 }, { d: "14", v: 120 },
  ];
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Month-End Forecast</h3>
        <div className="font-display font-bold text-3xl mt-2 bdy-text">₹2,450</div>
        <p className="text-xs text-slate-500">Predicted leftover by month end</p>
        <div className="h-28 mt-3" data-testid="trend-chart">
          <ResponsiveContainer>
            <LineChart data={trend}>
              <XAxis dataKey="d" hide />
              <Line type="monotone" dataKey="v" stroke="var(--bdy)" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="p-3 rounded-xl bg-emerald-50">
            <div className="text-[10px] text-emerald-700 font-semibold">UNDERSPEND</div>
            <div className="font-bold text-emerald-700">₹620</div>
          </div>
          <div className="p-3 rounded-xl bg-rose-50">
            <div className="text-[10px] text-rose-700 font-semibold">OVERSPEND</div>
            <div className="font-bold text-rose-700">₹180</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

const Alerts = () => {
  const [threshold, setThreshold] = useState(75);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex items-center gap-2 text-rose-600">
          <AlertTriangle className="w-4 h-4" />
          <span className="font-display font-bold">2 Alerts Active</span>
        </div>
        <div className="mt-3 space-y-2">
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-100">
            <div className="text-sm font-semibold text-rose-700">Food category at 71%</div>
            <div className="text-xs text-rose-600">₹4,230 of ₹6,000 used</div>
          </div>
          <div className="p-3 rounded-xl bg-amber-50 border border-amber-100">
            <div className="text-sm font-semibold text-amber-700">Education at 70%</div>
            <div className="text-xs text-amber-600">Approaching limit — review purchases</div>
          </div>
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
            <div className="text-sm font-semibold text-emerald-700">Transport on track</div>
          </div>
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-sm">Alert threshold</h3>
        <p className="text-xs text-slate-500">Notify me when category exceeds {threshold}%</p>
        <input type="range" min="50" max="100" value={threshold} onChange={(e) => setThreshold(parseInt(e.target.value))}
          className="bdy-slider mt-3" style={{ "--val": `${(threshold - 50) * 2}%` }}
          data-testid="alert-threshold" />
      </Card>
    </div>
  );
};

const Subs = () => {
  const [data, setData] = useState({ items: [], monthly_total: 0 });
  useEffect(() => { api.get("/subscriptions").then((r) => setData(r.data)); }, []);
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
            </div>
          ))}
        </div>
        <InsightCard icon={Users} title="Sharing tip" text="Split Netflix with 2 friends → save ₹133/month." />
      </Card>
    </div>
  );
};

const FoodTravel = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base">Food & Travel</h3>
      <div className="grid grid-cols-2 gap-2 mt-3">
        <div className="p-3 rounded-2xl bdy-soft border border-[color:var(--bdy)]/15">
          <div className="text-[10px] font-semibold uppercase text-slate-600">Food</div>
          <div className="font-display font-bold text-xl mt-1">₹4,230</div>
          <div className="text-[11px] text-slate-500">71% of ₹6,000</div>
        </div>
        <div className="p-3 rounded-2xl bg-emerald-50 border border-emerald-100">
          <div className="text-[10px] font-semibold uppercase text-emerald-700">Travel</div>
          <div className="font-display font-bold text-xl mt-1">₹1,650</div>
          <div className="text-[11px] text-emerald-600">55% of ₹3,000</div>
        </div>
      </div>
      <InsightCard icon={Plane} title="Mode comparison" text="Metro saves ₹90/day vs rideshare for the same route." />
    </Card>
  </div>
);

const Emergency = () => {
  const target = 30000, saved = 21000, pct = Math.round((saved / target) * 100);
  const r = 70, c = Math.PI * r;
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base text-center">Emergency Fund</h3>
        <div className="relative w-48 h-28 mx-auto mt-3">
          <svg width="192" height="112" viewBox="0 0 192 112">
            <path d={`M 16 96 A ${r} ${r} 0 0 1 176 96`} stroke="#E2E8F0" strokeWidth="14" fill="none" strokeLinecap="round" />
            <path d={`M 16 96 A ${r} ${r} 0 0 1 176 96`} stroke="var(--bdy)" strokeWidth="14" fill="none"
              strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)} />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
            <div className="font-display font-bold text-3xl">{pct}%</div>
            <div className="text-[11px] text-slate-500">₹{saved} / ₹{target}</div>
          </div>
        </div>
        <InsightCard icon={ShieldCheck} title="Almost there!" text="Save ₹3,000/month to hit 1-month emergency goal in 3 months." />
      </Card>
    </div>
  );
};

const Savings = () => {
  const [g, setG] = useState([]);
  useEffect(() => { api.get("/savings").then((r) => setG(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Savings Goals</h3>
        <div className="mt-3 space-y-3" data-testid="savings-list">
          {g.map((s) => {
            const pct = Math.round((s.saved / s.target) * 100);
            return (
              <div key={s.id} className="p-3 rounded-xl bg-slate-50">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-semibold">{s.emoji} {s.name}</span>
                  <span className="text-xs font-bold bdy-text">{pct}%</span>
                </div>
                <div className="h-2 mt-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full bdy-bg" style={{ width: `${pct}%` }} />
                </div>
                <div className="text-[11px] text-slate-500 mt-1">₹{s.saved.toLocaleString()} of ₹{s.target.toLocaleString()}</div>
              </div>
            );
          })}
        </div>
        <InsightCard icon={PiggyBank} title="Simulation tip" text="Skip 2 cafe visits/week → laptop fund 5 weeks sooner." />
      </Card>
    </div>
  );
};

const Splits = () => {
  const [data, setData] = useState({ items: [], net_balance: 0 });
  useEffect(() => { api.get("/splits").then((r) => setData(r.data)); }, []);
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
              <div>
                <div className="text-sm font-semibold">{s.title}</div>
                <div className="text-[11px] text-slate-500">with {s.with_person}</div>
              </div>
              <span className={`font-bold text-sm ${s.owes_you >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                {s.owes_you >= 0 ? "+" : ""}₹{s.owes_you}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

const BudgetEditor = () => {
  const [cats, setCats] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ name: "", allocated: "" });
  const [newCat, setNewCat] = useState({ name: "", allocated: "" });
  const [busy, setBusy] = useState(false);

  const load = async () => setCats((await api.get("/budget")).data.categories);
  useEffect(() => { load(); }, []);

  const totalAlloc = cats.reduce((s, c) => s + c.allocated, 0);

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

  return (
    <div className="mx-5 mt-4 space-y-3">
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
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Finance Buddy 🦉" subtitle="Track. Plan. Achieve." gradient />
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="fin-tab" />
      <Active />
    </div>
  );
}
