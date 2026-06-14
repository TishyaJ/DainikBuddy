import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { ExerciseTracker } from "../components/Exercise";
import { Star, MapPin, Train, Bike, Car, Footprints, Shield, Phone, Apple, Activity, GraduationCap, Sparkles, Users, WifiOff } from "lucide-react";
import { api } from "../lib/api";
import { useOffline } from "../context/OfflineContext";

const Dashboard = () => {
  const [food, setFood] = useState([]);
  useEffect(() => { api.get("/discover/food").then((r) => setFood(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex items-center justify-between">
          <h3 className="font-display font-bold text-base">Popular Near You</h3>
          <span className="text-xs bdy-text font-semibold">See all</span>
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2" data-testid="food-grid">
          {food.slice(0, 3).map((f, i) => (
            <div key={i} className="rounded-xl overflow-hidden bg-slate-50">
              <div className="h-16 bg-cover bg-center" style={{ backgroundImage: `url(${f.image})` }} />
              <div className="p-2">
                <div className="text-[11px] font-bold truncate">{f.name}</div>
                <div className="text-[10px] text-slate-500">₹{f.price} · {f.distance}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <h3 className="font-display font-bold text-base">Student Deals</h3>
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="p-3 rounded-2xl bdy-soft">
            <div className="text-[10px] font-bold text-slate-600">FLAT 20% OFF</div>
            <div className="text-sm font-display font-bold mt-1">Local Cafés</div>
            <div className="text-[10px] text-slate-500 mt-1">ID required</div>
          </div>
          <div className="p-3 rounded-2xl bg-orange-50">
            <div className="text-[10px] font-bold text-orange-600">BUY 1 GET 1</div>
            <div className="text-sm font-display font-bold mt-1">All Meals</div>
            <div className="text-[10px] text-slate-500 mt-1">Hostel special</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

const Food = () => {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/discover/food").then((r) => setItems(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Cheap Eats Nearby</h3>
        <div className="mt-3 grid grid-cols-2 gap-2" data-testid="food-list">
          {items.map((f, i) => (
            <div key={i} className="rounded-xl overflow-hidden bg-slate-50">
              <div className="h-20 bg-cover bg-center" style={{ backgroundImage: `url(${f.image})` }} />
              <div className="p-2">
                <div className="text-[12px] font-bold truncate">{f.name}</div>
                <div className="flex items-center gap-1 mt-0.5">
                  <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                  <span className="text-[10px] text-slate-500">{f.rating} · ₹{f.price}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <InsightCard icon={Sparkles} title="Nutrition per ₹" text="Student Thali offers the highest protein per rupee — 8g for ₹60." />
      </Card>
    </div>
  );
};

const Travel = () => {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/discover/travel").then((r) => setItems(r.data)); }, []);
  const ICONS = { Metro: Train, Cycle: Bike, Rideshare: Car, Walk: Footprints };
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Route Comparison</h3>
        <p className="text-xs text-slate-500">Hostel → College</p>
        <div className="grid grid-cols-2 gap-2 mt-3" data-testid="travel-grid">
          {items.map((t, i) => {
            const Icon = ICONS[t.mode] || Car;
            return (
              <div key={i} className="p-3 rounded-2xl bg-slate-50">
                <Icon className="w-5 h-5 bdy-text" />
                <div className="text-sm font-display font-bold mt-1">{t.mode}</div>
                <div className="text-[11px] text-slate-500">₹{t.cost} · {t.time}</div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

const SafeNight = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base flex items-center gap-2"><Shield className="w-4 h-4" /> Safe Night Travel</h3>
      <div className="mt-3 h-32 rounded-xl bg-gradient-to-br from-indigo-900 to-purple-900 flex items-center justify-center text-white">
        <MapPin className="w-8 h-8" />
        <span className="ml-2 font-display font-bold">Live route map</span>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-3">
        <button data-testid="notify-contact" className="bdy-bg text-white font-semibold py-2.5 rounded-xl text-sm">Notify Contact</button>
        <button data-testid="sos-btn" className="bg-rose-600 text-white font-semibold py-2.5 rounded-xl text-sm flex items-center justify-center gap-1">
          <Phone className="w-4 h-4" /> SOS
        </button>
      </div>
    </Card>
  </div>
);

const Snacks = () => {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/discover/snacks").then((r) => setItems(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Brain-Friendly Snacks</h3>
        <div className="mt-3 space-y-2" data-testid="snack-list">
          {items.map((s, i) => (
            <div key={i} className="p-3 rounded-xl bg-slate-50">
              <div className="flex justify-between">
                <span className="text-sm font-semibold">{s.name}</span>
                <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">{s.tag}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div className="text-[11px]">Nutrition <span className="font-bold">{s.nutrition}/10</span></div>
                <div className="text-[11px]">Budget <span className="font-bold">{s.budget}/10</span></div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

const Activities = () => {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/discover/activities").then((r) => setItems(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Quick Stress Breaks</h3>
        <div className="grid grid-cols-2 gap-2 mt-3">
          {items.map((a, i) => (
            <div key={i} className="p-3 rounded-2xl bdy-soft">
              <Activity className="w-4 h-4 bdy-text" />
              <div className="text-sm font-display font-bold mt-1">{a.name}</div>
              <div className="text-[11px] text-slate-500">{a.duration}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

const Campus = () => {
  const [items, setItems] = useState([]);
  useEffect(() => { api.get("/discover/campus").then((r) => setItems(r.data)); }, []);
  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base">Campus Resources</h3>
        <div className="mt-3 space-y-2" data-testid="campus-list">
          {items.map((r, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4 bdy-text" />
                <span className="text-sm font-semibold">{r.name}</span>
              </div>
              <button disabled={!r.available} className={`text-[11px] font-bold px-3 py-1 rounded-full ${r.available ? "bdy-bg text-white" : "bg-slate-200 text-slate-500"}`}>
                {r.available ? "Book" : "Closed"}
              </button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

const Goals = () => (
  <div className="mx-5 mt-4 space-y-3">
    <Card>
      <h3 className="font-display font-bold text-base">My Discovery Goals</h3>
      <div className="mt-3 space-y-3">
        {[{ n: "Try 5 cheap eats", p: 60 }, { n: "Bike to college 10x", p: 40 }, { n: "Visit campus library 5x", p: 80 }].map((g, i) => (
          <div key={i}>
            <div className="flex justify-between text-sm"><span className="font-semibold">{g.n}</span><span className="bdy-text font-bold">{g.p}%</span></div>
            <div className="h-2 mt-1 rounded-full bg-slate-100"><div className="h-full bdy-bg rounded-full" style={{ width: `${g.p}%` }} /></div>
          </div>
        ))}
      </div>
      <a href="#" className="mt-4 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-2.5 rounded-xl text-sm" data-testid="discord-link">
        <Users className="w-4 h-4" /> Join like-minded community
      </a>
    </Card>
  </div>
);

const Fitness = () => <ExerciseTracker />;

const TABS = [
  { key: "dash", label: "Dashboard", C: Dashboard },
  { key: "food", label: "Food", C: Food },
  { key: "travel", label: "Travel", C: Travel },
  { key: "safe", label: "Safe Night", C: SafeNight },
  { key: "snack", label: "Snacks", C: Snacks },
  { key: "act", label: "Activities", C: Activities },
  { key: "camp", label: "Campus", C: Campus },
  { key: "goals", label: "Goals", C: Goals },
  { key: "fit", label: "Fitness", C: Fitness },
];

export default function DiscoverBuddy() {
  const [tab, setTab] = useState("dash");
  const { isOnline } = useOffline();
  const Active = TABS.find((t) => t.key === tab).C;

  if (!isOnline) {
    return (
      <div className="flex-1 overflow-auto scroll-area pb-4">
        <Header title="Discover Buddy 🧭" subtitle="Eat well. Travel smart. Save more." gradient />
        <div className="flex flex-col items-center justify-center px-5 py-16" data-testid="discover-offline-message">
          <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mb-4">
            <WifiOff className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="font-display font-bold text-lg text-slate-800">Discover requires internet</h2>
          <p className="text-sm text-slate-500 text-center mt-2 max-w-xs">
            Discover features need an active internet connection to find nearby places and deals. Check back when you're online.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto scroll-area pb-4">
      <Header title="Discover Buddy 🧭" subtitle="Eat well. Travel smart. Save more." gradient />
      <SubTabs tabs={TABS} active={tab} onChange={setTab} testid="disc-tab" />
      <Active />
    </div>
  );
}
