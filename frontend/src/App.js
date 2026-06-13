import React, { useEffect } from "react";
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

const ROUTE_DOMAIN = {
  "/": "daily",
  "/finance": "finance",
  "/wellness": "wellness",
  "/discover": "discover",
  "/chat": "helper",
};

const Shell = () => {
  const loc = useLocation();
  const { setDomain } = useDomain();
  const isChat = loc.pathname.startsWith("/chat/");

  useEffect(() => {
    if (isChat) return;
    const d = ROUTE_DOMAIN[loc.pathname] || "daily";
    setDomain(d);
  }, [loc.pathname, isChat, setDomain]);

  return (
    <PhoneFrame>
      <Routes>
        <Route path="/" element={<DailyHub />} />
        <Route path="/finance" element={<FinanceBuddy />} />
        <Route path="/wellness" element={<WellnessBuddy />} />
        <Route path="/discover" element={<DiscoverBuddy />} />
        <Route path="/chat" element={<ChatCenter />} />
        <Route path="/chat/:buddy" element={<BuddyChat />} />
      </Routes>
      {!isChat && <BottomNav />}
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
