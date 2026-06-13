import React from "react";

export const SubTabs = ({ tabs, active, onChange, testid = "subtab" }) => (
  <div className="px-5">
    <div className="flex gap-2 overflow-x-auto hide-sb py-2 -mx-1 px-1">
      {tabs.map((t) => {
        const isActive = active === t.key;
        return (
          <button
            key={t.key}
            data-testid={`${testid}-${t.key}`}
            onClick={() => onChange(t.key)}
            className={`shrink-0 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all active:scale-95 ${
              isActive ? "bdy-bg text-white shadow-sm" : "bg-white text-slate-600 border border-slate-200"
            }`}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  </div>
);

export const Card = ({ children, className = "", ...rest }) => (
  <div
    className={`bg-white rounded-2xl p-4 shadow-sm border border-slate-100 ${className}`}
    {...rest}
  >
    {children}
  </div>
);

export const InsightCard = ({ icon: Icon, title, text, accent = true }) => (
  <div
    data-testid="insight-card"
    className={`rounded-2xl p-4 ${accent ? "bdy-soft border border-[color:var(--bdy)]/15" : "bg-slate-50"}`}
  >
    <div className="flex items-start gap-3">
      {Icon && (
        <div className="w-9 h-9 rounded-xl bdy-bg text-white flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4" />
        </div>
      )}
      <div className="flex-1">
        <div className="text-sm font-semibold text-slate-900 font-display">{title}</div>
        <div className="text-xs text-slate-600 mt-1 leading-relaxed">{text}</div>
      </div>
    </div>
  </div>
);
