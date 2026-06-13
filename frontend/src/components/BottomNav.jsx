import React from "react";
import { Home, Wallet, Cloud, Compass, MessageCircle } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useDomain } from "../context/DomainContext";

const tabs = [
  { to: "/", label: "Home", icon: Home, domain: "daily", testid: "nav-home" },
  { to: "/finance", label: "Finance", icon: Wallet, domain: "finance", testid: "nav-finance" },
  { to: "/wellness", label: "Wellness", icon: Cloud, domain: "wellness", testid: "nav-wellness" },
  { to: "/discover", label: "Discover", icon: Compass, domain: "discover", testid: "nav-discover" },
  { to: "/chat", label: "Chat", icon: MessageCircle, domain: "helper", testid: "nav-chat" },
];

export const BottomNav = () => {
  const { setDomain } = useDomain();
  return (
    <nav
      data-testid="bottom-nav"
      className="sticky bottom-0 left-0 right-0 h-16 bg-white/95 backdrop-blur border-t border-slate-200 flex items-center justify-around z-40"
    >
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.to === "/"}
          onClick={() => setDomain(t.domain)}
          data-testid={t.testid}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 px-3 py-1.5 no-tap-highlight transition-all ${
              isActive ? "text-[color:var(--bdy)] scale-105" : "text-slate-400"
            }`
          }
        >
          <t.icon className="w-5 h-5" />
          <span className="text-[10px] font-semibold tracking-wide">{t.label}</span>
        </NavLink>
      ))}
    </nav>
  );
};
