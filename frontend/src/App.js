import React, { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { DomainProvider, useDomain } from "./context/DomainContext";
import { PhoneFrame } from "./components/PhoneFrame";
import { BottomNav } from "./components/BottomNav";
import DailyHub from "./pages/DailyHub";
import FinanceBuddy from "./pages/FinanceBuddy";
import WellnessBuddy from "./pages/WellnessBuddy";
import DiscoverBuddy from "./pages/DiscoverBuddy";
import ChatCenter from "./pages/ChatCenter";
import BuddyChat from "./pages/BuddyChat";
import Profile from "./pages/Profile";
import Onboarding from "./pages/Onboarding";
import { api } from "./lib/api";

const ROUTE_DOMAIN = {
  "/": "daily",
  "/finance": "finance",
  "/wellness": "wellness",
  "/discover": "discover",
  "/chat": "helper",
  "/profile": "helper",
};

const Shell = () => {
  const loc = useLocation();
  const { setDomain } = useDomain();
  const isChat = loc.pathname.startsWith("/chat/");
  const isProfile = loc.pathname === "/profile";
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (isChat || isProfile) return;
    const d = ROUTE_DOMAIN[loc.pathname] || "daily";
    setDomain(d);
  }, [loc.pathname, isChat, isProfile, setDomain]);

  useEffect(() => {
    api.get("/profile").then((r) => setProfile(r.data)).catch(() => setProfile({ onboarded: true }));
  }, []);

  const showOnboarding = profile && !profile.onboarded;
  const showNav = !isChat && !isProfile && !showOnboarding;

  return (
    <PhoneFrame>
      {showOnboarding ? (
        <Onboarding onDone={() => api.get("/profile").then((r) => setProfile(r.data))} />
      ) : (
        <Routes>
          <Route path="/" element={<DailyHub />} />
          <Route path="/finance" element={<FinanceBuddy />} />
          <Route path="/wellness" element={<WellnessBuddy />} />
          <Route path="/discover" element={<DiscoverBuddy />} />
          <Route path="/chat" element={<ChatCenter />} />
          <Route path="/chat/:buddy" element={<BuddyChat />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      )}
      {showNav && <BottomNav />}
    </PhoneFrame>
  );
};

function App() {
  return (
    <DomainProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </DomainProvider>
  );
}

export default App;
