import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { SubTabs, Card, InsightCard } from "../components/SubTabs";
import { Star, MapPin, Train, Bike, Car, Footprints, Shield, Phone, Apple, Activity, GraduationCap, Sparkles, Users, WifiOff } from "lucide-react";
import { api } from "../lib/api";
import { useOffline } from "../context/OfflineContext";

const Dashboard = () => {
  const [food, setFood] = useState([]);
  const [budget, setBudget] = useState(null);
  const [messMenu, setMessMenu] = useState(null);

  useEffect(() => {
    api.get("/discover/food").then((r) => setFood(r.data)).catch(() => { });
    api.get("/budget").then((r) => setBudget(r.data)).catch(() => { });
    api.get("/discover/mess-menu").then((r) => setMessMenu(r.data)).catch(() => { });
  }, []);

  const foodBudget = budget?.categories?.find(c => c.name.toLowerCase() === "food");
  const foodLeft = foodBudget ? (foodBudget.allocated - foodBudget.spent) : null;

  return (
    <div className="mx-5 mt-4 space-y-3">
      {/* Budget Context Card */}
      {foodLeft !== null && (
        <Card className={foodLeft < 100 ? "bg-rose-50 border-rose-100" : "bg-emerald-50 border-emerald-100"}>
          <div className="flex justify-between items-center">
            <div>
              <div className="text-[10px] font-semibold text-slate-500 uppercase">Food Budget Left</div>
              <div className={`font-display font-bold text-lg ${foodLeft < 100 ? "text-rose-700" : "text-emerald-700"}`}>₹{Math.max(0, foodLeft).toLocaleString()}</div>
            </div>
            {foodLeft < 100 && <div className="text-[10px] text-rose-600 font-semibold">⚠ Running low</div>}
          </div>
        </Card>
      )}

      {/* Today's Mess Quick View */}
      {messMenu?.today && (
        <Card>
          <div className="flex items-center gap-2">
            <span className="text-lg">🍽️</span>
            <div>
              <div className="text-xs font-semibold capitalize">{messMenu.today.meal} today</div>
              <div className="text-[11px] text-slate-500">{(messMenu.today.items || []).join(", ")} · ₹{messMenu.today.price}</div>
            </div>
          </div>
        </Card>
      )}
      <Card>
        <div className="flex items-center justify-between">
          <h3 className="font-display font-bold text-base">Popular Near You</h3>
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
  const [messMenu, setMessMenu] = useState(null);
  const [prefs, setPrefs] = useState(null);
  const [showPrefs, setShowPrefs] = useState(false);
  const [prefForm, setPrefForm] = useState({ dietary: "any", budget_per_meal: "100", cuisines: [], allergies: [] });
  const [messSub, setMessSub] = useState(null);
  const [showMessForm, setShowMessForm] = useState(false);
  const [messForm, setMessForm] = useState({ day: "", meal: "lunch", items: "", price: "" });
  const [subForm, setSubForm] = useState({ type: "monthly", monthly_cost: "", per_meal_cost: "", mess_name: "" });

  useEffect(() => {
    api.get("/discover/food").then((r) => setItems(r.data)).catch(() => { });
    api.get("/discover/mess-menu").then((r) => { setMessMenu(r.data); setMessSub(r.data.subscription); }).catch(() => { });
    api.get("/discover/food-preferences").then((r) => { setPrefs(r.data); setPrefForm(r.data); }).catch(() => { });
  }, []);

  const savePrefs = async () => {
    const data = { ...prefForm, budget_per_meal: parseFloat(prefForm.budget_per_meal) || 100 };
    await api.post("/discover/food-preferences", data);
    setPrefs(data);
    setShowPrefs(false);
    // Refresh food with new preferences
    const r = await api.get("/discover/food");
    setItems(r.data);
  };

  const saveMessMenu = async () => {
    const itemsList = messForm.items.split(",").map(s => s.trim()).filter(Boolean);
    await api.post("/discover/mess-menu", { day: messForm.day, meal: messForm.meal, items: itemsList, price: parseFloat(messForm.price) || 0 });
    setShowMessForm(false);
    const r = await api.get("/discover/mess-menu");
    setMessMenu(r.data);
  };

  const saveSubscription = async () => {
    await api.post("/discover/mess-subscription", {
      type: subForm.type,
      monthly_cost: parseFloat(subForm.monthly_cost) || 0,
      per_meal_cost: parseFloat(subForm.per_meal_cost) || 0,
      mess_name: subForm.mess_name,
    });
    const r = await api.get("/discover/mess-menu");
    setMessSub(r.data.subscription);
  };

  const DIETARY_OPTIONS = ["any", "veg", "non-veg", "vegan", "jain"];
  const CUISINE_OPTIONS = ["North Indian", "South Indian", "Chinese", "Street Food", "Continental"];

  return (
    <div className="mx-5 mt-4 space-y-3">
      {/* Today's Mess Menu */}
      <Card>
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-base">🍽️ Today's Mess</h3>
          <button onClick={() => setShowMessForm(!showMessForm)} className="text-xs bdy-text font-semibold">
            {showMessForm ? "Close" : "+ Add Menu"}
          </button>
        </div>
        {messSub && (
          <div className="mt-1 text-[11px] text-slate-500">
            {messSub.mess_name || "Mess"} · {messSub.type === "monthly" ? `₹${messSub.monthly_cost}/mo` : `₹${messSub.per_meal_cost}/meal`}
          </div>
        )}
        {messMenu?.today ? (
          <div className="mt-2 p-3 rounded-xl bg-emerald-50 border border-emerald-100">
            <div className="text-xs font-semibold text-emerald-700 capitalize">{messMenu.today.meal}</div>
            <div className="text-sm font-bold mt-0.5">{(messMenu.today.items || []).join(", ")}</div>
            <div className="text-[11px] text-emerald-600 mt-0.5">₹{messMenu.today.price}</div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 mt-2">No menu set for today. Add your mess menu above.</p>
        )}
        {showMessForm && (
          <div className="mt-3 p-3 rounded-xl bg-slate-50 space-y-2">
            <div className="flex gap-2">
              <select value={messForm.day} onChange={(e) => setMessForm({ ...messForm, day: e.target.value })}
                className="flex-1 text-xs bg-white rounded-lg px-2 py-2 border border-slate-200 outline-none">
                <option value="">Day</option>
                {["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].map(d => (
                  <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                ))}
              </select>
              <select value={messForm.meal} onChange={(e) => setMessForm({ ...messForm, meal: e.target.value })}
                className="flex-1 text-xs bg-white rounded-lg px-2 py-2 border border-slate-200 outline-none">
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
              </select>
            </div>
            <input value={messForm.items} onChange={(e) => setMessForm({ ...messForm, items: e.target.value })}
              placeholder="Items (comma separated: dal, rice, roti)" className="w-full text-xs bg-white rounded-lg px-3 py-2 border border-slate-200 outline-none" />
            <div className="flex gap-2">
              <input type="number" min="0" value={messForm.price} onChange={(e) => setMessForm({ ...messForm, price: e.target.value })}
                placeholder="₹ Price" className="flex-1 text-xs bg-white rounded-lg px-3 py-2 border border-slate-200 outline-none" />
              <button onClick={saveMessMenu} disabled={!messForm.day} className="px-4 py-2 rounded-lg bdy-bg text-white text-xs font-semibold disabled:opacity-50">Save</button>
            </div>
            <div className="border-t border-slate-200 pt-2 mt-2">
              <div className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Subscription</div>
              <div className="flex gap-2">
                <input value={subForm.mess_name} onChange={(e) => setSubForm({ ...subForm, mess_name: e.target.value })}
                  placeholder="Mess name" className="flex-1 text-xs bg-white rounded-lg px-2 py-1.5 border border-slate-200 outline-none" />
                <select value={subForm.type} onChange={(e) => setSubForm({ ...subForm, type: e.target.value })}
                  className="text-xs bg-white rounded-lg px-2 py-1.5 border border-slate-200 outline-none">
                  <option value="monthly">Monthly</option>
                  <option value="per_meal">Per Meal</option>
                </select>
              </div>
              <div className="flex gap-2 mt-1">
                {subForm.type === "monthly" ? (
                  <input type="number" min="0" value={subForm.monthly_cost} onChange={(e) => setSubForm({ ...subForm, monthly_cost: e.target.value })}
                    placeholder="₹ Monthly cost" className="flex-1 text-xs bg-white rounded-lg px-2 py-1.5 border border-slate-200 outline-none" />
                ) : (
                  <input type="number" min="0" value={subForm.per_meal_cost} onChange={(e) => setSubForm({ ...subForm, per_meal_cost: e.target.value })}
                    placeholder="₹ Per meal" className="flex-1 text-xs bg-white rounded-lg px-2 py-1.5 border border-slate-200 outline-none" />
                )}
                <button onClick={saveSubscription} className="px-3 py-1.5 rounded-lg bdy-bg text-white text-xs font-semibold">Set</button>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Food Preferences */}
      {!prefs || prefs.dietary === "any" ? (
        <Card className="bdy-soft border border-[color:var(--bdy)]/15">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-display font-bold text-sm">Set Food Preferences</h3>
              <p className="text-[11px] text-slate-500">Get personalized recommendations</p>
            </div>
            <button onClick={() => setShowPrefs(!showPrefs)} className="text-xs bdy-text font-semibold">{showPrefs ? "Close" : "Set up"}</button>
          </div>
          {showPrefs && (
            <div className="mt-3 space-y-2">
              <div>
                <div className="text-[10px] font-semibold text-slate-500 mb-1">DIETARY</div>
                <div className="flex flex-wrap gap-1.5">
                  {DIETARY_OPTIONS.map(d => (
                    <button key={d} onClick={() => setPrefForm({ ...prefForm, dietary: d })}
                      className={`px-2.5 py-1 rounded-full text-[11px] font-semibold capitalize ${prefForm.dietary === d ? "bdy-bg text-white" : "bg-white border border-slate-200 text-slate-600"}`}>
                      {d}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-semibold text-slate-500 mb-1">BUDGET PER MEAL</div>
                <input type="number" min="10" max="500" value={prefForm.budget_per_meal} onChange={(e) => setPrefForm({ ...prefForm, budget_per_meal: e.target.value })}
                  className="w-full text-xs bg-white rounded-lg px-3 py-2 border border-slate-200 outline-none" placeholder="₹ max per meal" />
              </div>
              <div>
                <div className="text-[10px] font-semibold text-slate-500 mb-1">CUISINES (tap to select)</div>
                <div className="flex flex-wrap gap-1.5">
                  {CUISINE_OPTIONS.map(c => (
                    <button key={c} onClick={() => {
                      const cuisines = prefForm.cuisines || [];
                      setPrefForm({ ...prefForm, cuisines: cuisines.includes(c) ? cuisines.filter(x => x !== c) : [...cuisines, c] });
                    }}
                      className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${(prefForm.cuisines || []).includes(c) ? "bdy-bg text-white" : "bg-white border border-slate-200 text-slate-600"}`}>
                      {c}
                    </button>
                  ))}
                </div>
              </div>
              <button onClick={savePrefs} className="w-full py-2 rounded-lg bdy-bg text-white text-xs font-semibold mt-2">Save Preferences</button>
            </div>
          )}
        </Card>
      ) : (
        <div className="flex justify-between items-center px-1">
          <div className="text-[11px] text-slate-500">
            Showing: <span className="font-semibold capitalize">{prefs.dietary}</span> · Under ₹{prefs.budget_per_meal}/meal
          </div>
          <button onClick={() => setShowPrefs(!showPrefs)} className="text-[11px] bdy-text font-semibold">Edit</button>
        </div>
      )}
      {showPrefs && prefs?.dietary !== "any" && (
        <Card>
          <div className="space-y-2">
            <div>
              <div className="text-[10px] font-semibold text-slate-500 mb-1">DIETARY</div>
              <div className="flex flex-wrap gap-1.5">
                {DIETARY_OPTIONS.map(d => (
                  <button key={d} onClick={() => setPrefForm({ ...prefForm, dietary: d })}
                    className={`px-2.5 py-1 rounded-full text-[11px] font-semibold capitalize ${prefForm.dietary === d ? "bdy-bg text-white" : "bg-white border border-slate-200 text-slate-600"}`}>
                    {d}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-semibold text-slate-500 mb-1">BUDGET PER MEAL</div>
              <input type="number" min="10" max="500" value={prefForm.budget_per_meal} onChange={(e) => setPrefForm({ ...prefForm, budget_per_meal: e.target.value })}
                className="w-full text-xs bg-white rounded-lg px-3 py-2 border border-slate-200 outline-none" />
            </div>
            <button onClick={savePrefs} className="w-full py-2 rounded-lg bdy-bg text-white text-xs font-semibold">Update</button>
          </div>
        </Card>
      )}

      {/* Filtered Food Recommendations */}
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
        {items.length === 0 && <p className="text-xs text-slate-400 text-center py-4">No matches for your preferences. Try adjusting budget or dietary type.</p>}
        <InsightCard icon={Sparkles} title="Nutrition per ₹" text="Student Thali offers the highest protein per rupee — 8g for ₹60." />
      </Card>
    </div>
  );
};

const Travel = () => {
  const [data, setData] = useState(null);
  const [places, setPlaces] = useState([]);
  const [fromPlace, setFromPlace] = useState("");
  const [toPlace, setToPlace] = useState("");
  const [showAddPlace, setShowAddPlace] = useState(false);
  const [newPlace, setNewPlace] = useState({ name: "", type: "other" });
  const ICONS = { Metro: Train, Cycle: Bike, Rideshare: Car, Walk: Footprints, Auto: Car };
  const PLACE_TYPES = ["hostel", "college", "library", "market", "hospital", "other"];

  useEffect(() => {
    api.get("/discover/travel").then((r) => {
      setData(r.data);
      setFromPlace(r.data.from);
      setToPlace(r.data.to);
      setPlaces(r.data.saved_places || []);
    }).catch(() => { });
  }, []);

  const addPlace = async () => {
    if (!newPlace.name.trim()) return;
    const res = await api.post("/discover/saved-places", newPlace);
    setPlaces([...places, res.data]);
    setNewPlace({ name: "", type: "other" });
    setShowAddPlace(false);
  };

  const deletePlace = async (id) => {
    await api.delete(`/discover/saved-places/${id}`);
    setPlaces(places.filter(p => p.id !== id));
  };

  return (
    <div className="mx-5 mt-4 space-y-3">
      {/* Route Selector */}
      <Card>
        <h3 className="font-display font-bold text-base">Route Comparison</h3>
        <div className="flex items-center gap-2 mt-2">
          <select value={fromPlace} onChange={(e) => setFromPlace(e.target.value)}
            className="flex-1 text-xs bg-slate-50 rounded-lg px-2 py-2 border border-slate-200 outline-none" aria-label="From location">
            <option value="">From...</option>
            {places.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
            {!places.find(p => p.name === fromPlace) && fromPlace && <option value={fromPlace}>{fromPlace}</option>}
          </select>
          <span className="text-xs text-slate-400 font-bold">→</span>
          <select value={toPlace} onChange={(e) => setToPlace(e.target.value)}
            className="flex-1 text-xs bg-slate-50 rounded-lg px-2 py-2 border border-slate-200 outline-none" aria-label="To location">
            <option value="">To...</option>
            {places.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
            {!places.find(p => p.name === toPlace) && toPlace && <option value={toPlace}>{toPlace}</option>}
          </select>
        </div>
        <p className="text-[10px] text-slate-400 mt-1">{fromPlace || "?"} → {toPlace || "?"}</p>

        {data?.routes && (
          <div className="grid grid-cols-2 gap-2 mt-3" data-testid="travel-grid">
            {data.routes.map((t, i) => {
              const Icon = ICONS[t.mode] || Car;
              return (
                <div key={i} className="p-3 rounded-2xl bg-slate-50 relative">
                  <Icon className="w-5 h-5 bdy-text" />
                  <div className="text-sm font-display font-bold mt-1">{t.mode}</div>
                  <div className="text-[11px] text-slate-500">₹{t.cost} · {t.time}</div>
                  {t.eco && <span className="absolute top-2 right-2 text-[8px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full font-bold">ECO</span>}
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Saved Places */}
      <Card>
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-sm">Saved Places</h3>
          <button onClick={() => setShowAddPlace(!showAddPlace)} className="text-xs bdy-text font-semibold">
            {showAddPlace ? "Close" : "+ Add"}
          </button>
        </div>
        {showAddPlace && (
          <div className="mt-2 flex gap-2">
            <input value={newPlace.name} onChange={(e) => setNewPlace({ ...newPlace, name: e.target.value })}
              placeholder="Place name" className="flex-1 text-xs bg-slate-50 rounded-lg px-2 py-2 border border-slate-200 outline-none" />
            <select value={newPlace.type} onChange={(e) => setNewPlace({ ...newPlace, type: e.target.value })}
              className="text-xs bg-slate-50 rounded-lg px-2 py-2 border border-slate-200 outline-none">
              {PLACE_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
            <button onClick={addPlace} disabled={!newPlace.name.trim()} className="px-3 py-2 rounded-lg bdy-bg text-white text-xs font-semibold disabled:opacity-50">Add</button>
          </div>
        )}
        {places.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {places.map(p => (
              <span key={p.id} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-50 text-xs font-semibold text-slate-700 border border-slate-200">
                {p.name}
                <button onClick={() => deletePlace(p.id)} className="text-slate-400 hover:text-rose-500 ml-0.5" aria-label={`Remove ${p.name}`}>×</button>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 mt-2">Add your hostel, college, library etc. for quick route comparison.</p>
        )}
      </Card>
    </div>
  );
};

const SafeNight = () => {
  const [notifying, setNotifying] = useState(false);
  const [notifyMsg, setNotifyMsg] = useState("");
  const [location, setLocation] = useState(null);
  const [locLoading, setLocLoading] = useState(true);
  const [contact, setContact] = useState(null);
  const [showSetup, setShowSetup] = useState(false);
  const [contactForm, setContactForm] = useState({ name: "", phone: "" });

  useEffect(() => {
    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => { setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }); setLocLoading(false); },
        () => setLocLoading(false),
        { timeout: 5000 }
      );
    } else { setLocLoading(false); }
    // Get emergency contact
    api.get("/profile").then((r) => {
      setContact(r.data.emergency_contact || null);
    }).catch(() => { });
  }, []);

  const handleNotifyContact = async () => {
    setNotifying(true);
    setNotifyMsg("");
    try {
      const res = await api.post("/safety/notify-contact", { lat: location?.lat, lng: location?.lng });
      setNotifyMsg(res.data.message || "Contact notified!");
    } catch (err) {
      setNotifyMsg(err.response?.data?.detail || "Set an emergency contact first.");
    } finally { setNotifying(false); }
  };

  const handleSOS = () => {
    if (window.confirm("This will call emergency services (112). Continue?")) {
      window.location.href = "tel:112";
    }
  };

  const saveContact = async () => {
    if (!contactForm.name.trim() || !contactForm.phone.trim()) return;
    await api.patch("/profile", { emergency_contact: `${contactForm.name.trim()} (${contactForm.phone.trim()})` });
    setContact(`${contactForm.name.trim()} (${contactForm.phone.trim()})`);
    setShowSetup(false);
  };

  const shareLocationUrl = location ? `https://maps.google.com/?q=${location.lat},${location.lng}` : null;

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <h3 className="font-display font-bold text-base flex items-center gap-2"><Shield className="w-4 h-4" /> Safe Night Travel</h3>

        {/* Live Location */}
        <div className="mt-3 rounded-xl bg-gradient-to-br from-indigo-900 to-purple-900 p-4 text-white">
          {locLoading ? (
            <div className="text-center py-4"><div className="text-xs opacity-70">Getting your location...</div></div>
          ) : location ? (
            <div className="text-center">
              <MapPin className="w-6 h-6 mx-auto mb-1" />
              <div className="text-xs opacity-80">Your Location</div>
              <div className="text-[10px] font-mono mt-1 opacity-60">{location.lat.toFixed(5)}, {location.lng.toFixed(5)}</div>
              <a href={shareLocationUrl} target="_blank" rel="noopener noreferrer"
                className="inline-block mt-2 px-3 py-1.5 bg-white/20 rounded-full text-xs font-semibold hover:bg-white/30 transition">
                Open in Maps ↗
              </a>
            </div>
          ) : (
            <div className="text-center py-4">
              <MapPin className="w-6 h-6 mx-auto mb-1 opacity-50" />
              <div className="text-xs opacity-70">Location unavailable</div>
              <div className="text-[10px] opacity-50 mt-1">Enable location services to share with contacts</div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <button data-testid="notify-contact" onClick={handleNotifyContact} disabled={notifying || !contact}
            className="bdy-bg text-white font-semibold py-2.5 rounded-xl text-sm disabled:opacity-50" aria-label="Notify emergency contact">
            {notifying ? "Sending..." : "Notify Contact"}
          </button>
          <button data-testid="sos-btn" onClick={handleSOS}
            className="bg-rose-600 text-white font-semibold py-2.5 rounded-xl text-sm flex items-center justify-center gap-1" aria-label="Call 112">
            <Phone className="w-4 h-4" /> SOS
          </button>
        </div>
        {notifyMsg && <p className="text-xs mt-2 text-center text-slate-600">{notifyMsg}</p>}
      </Card>

      {/* Emergency Contact Setup */}
      <Card>
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-sm">Emergency Contact</h3>
          <button onClick={() => setShowSetup(!showSetup)} className="text-xs bdy-text font-semibold">
            {contact ? "Edit" : "Set up"}
          </button>
        </div>
        {contact ? (
          <div className="mt-2 p-2.5 rounded-xl bg-emerald-50 border border-emerald-100">
            <div className="text-sm font-semibold text-emerald-800">{contact}</div>
            <div className="text-[10px] text-emerald-600 mt-0.5">Will be notified with your location</div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 mt-2">No emergency contact set. Add one to enable "Notify Contact".</p>
        )}
        {showSetup && (
          <div className="mt-2 space-y-2">
            <input value={contactForm.name} onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
              placeholder="Contact name" className="w-full text-xs bg-slate-50 rounded-lg px-3 py-2 border border-slate-200 outline-none" />
            <input value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
              placeholder="Phone number" type="tel" className="w-full text-xs bg-slate-50 rounded-lg px-3 py-2 border border-slate-200 outline-none" />
            <button onClick={saveContact} disabled={!contactForm.name.trim() || !contactForm.phone.trim()}
              className="w-full py-2 rounded-lg bdy-bg text-white text-xs font-semibold disabled:opacity-50">Save Contact</button>
          </div>
        )}
      </Card>
    </div>
  );
};

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

const Campus = () => {
  const [items, setItems] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newResource, setNewResource] = useState({ name: "", type: "other", hours: "" });

  const load = () => api.get("/discover/campus").then((r) => setItems(r.data)).catch(() => { });
  useEffect(() => { load(); }, []);

  const addResource = async () => {
    if (!newResource.name.trim()) return;
    await api.post("/discover/campus", newResource);
    setNewResource({ name: "", type: "other", hours: "" });
    setShowAdd(false);
    load();
  };

  const deleteResource = async (id) => {
    await api.delete(`/discover/campus/${id}`);
    load();
  };

  const TYPE_ICONS = { wellness: "🏥", study: "📚", aid: "🤝", other: "📌" };

  return (
    <div className="mx-5 mt-4 space-y-3">
      <Card>
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-base">Campus Resources</h3>
          <button onClick={() => setShowAdd(!showAdd)} className="text-xs bdy-text font-semibold">
            {showAdd ? "Close" : "+ Add"}
          </button>
        </div>
        {showAdd && (
          <div className="mt-2 space-y-2">
            <input value={newResource.name} onChange={(e) => setNewResource({ ...newResource, name: e.target.value })}
              placeholder="Resource name" className="w-full text-xs bg-slate-50 rounded-lg px-3 py-2 border border-slate-200 outline-none" />
            <div className="flex gap-2">
              <select value={newResource.type} onChange={(e) => setNewResource({ ...newResource, type: e.target.value })}
                className="flex-1 text-xs bg-slate-50 rounded-lg px-2 py-2 border border-slate-200 outline-none">
                <option value="wellness">Wellness</option>
                <option value="study">Study</option>
                <option value="aid">Aid</option>
                <option value="other">Other</option>
              </select>
              <input value={newResource.hours} onChange={(e) => setNewResource({ ...newResource, hours: e.target.value })}
                placeholder="Hours (e.g. 9AM-5PM)" className="flex-1 text-xs bg-slate-50 rounded-lg px-2 py-2 border border-slate-200 outline-none" />
            </div>
            <button onClick={addResource} disabled={!newResource.name.trim()}
              className="w-full py-2 rounded-lg bdy-bg text-white text-xs font-semibold disabled:opacity-50">Add Resource</button>
          </div>
        )}
        <div className="mt-3 space-y-2" data-testid="campus-list">
          {items.map((r, i) => (
            <div key={r.id || i} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
              <div className="flex items-center gap-2 flex-1">
                <span className="text-base">{TYPE_ICONS[r.type] || "📌"}</span>
                <div>
                  <span className="text-sm font-semibold">{r.name}</span>
                  {r.hours && <div className="text-[10px] text-slate-500">{r.hours}</div>}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${r.available ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500"}`}>
                  {r.available ? "Open" : "Closed"}
                </span>
                {r.id && (
                  <button onClick={() => deleteResource(r.id)} className="text-slate-400 hover:text-rose-500 text-xs" aria-label={`Remove ${r.name}`}>×</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

const TABS = [
  { key: "dash", label: "Dashboard", C: Dashboard },
  { key: "food", label: "Food", C: Food },
  { key: "travel", label: "Travel", C: Travel },
  { key: "safe", label: "Safe Night", C: SafeNight },
  { key: "camp", label: "Campus", C: Campus },
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
