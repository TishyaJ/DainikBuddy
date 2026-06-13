import React, { createContext, useContext, useState } from "react";

const DomainContext = createContext({ domain: "daily", setDomain: () => {} });

export const DomainProvider = ({ children }) => {
  const [domain, setDomain] = useState("daily");
  return (
    <DomainContext.Provider value={{ domain, setDomain }}>
      {children}
    </DomainContext.Provider>
  );
};

export const useDomain = () => useContext(DomainContext);

export const DOMAIN_META = {
  daily:    { label: "Daily",    accent: "#A855F7", emoji: "☀️" },
  finance:  { label: "Finance",  accent: "#3B82F6", emoji: "🦉" },
  wellness: { label: "Wellness", accent: "#A78BFA", emoji: "☁️" },
  discover: { label: "Discover", accent: "#F43F5E", emoji: "🧭" },
  helper:   { label: "Helper",   accent: "#A855F7", emoji: "✨" },
};
