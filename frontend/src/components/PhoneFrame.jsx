import React from "react";
import { useDomain } from "../context/DomainContext";

export const PhoneFrame = ({ children }) => {
  const { domain } = useDomain();
  return (
    <div className="min-h-screen w-full flex items-start lg:items-center justify-center bg-slate-200 py-4 lg:py-10">
      <div
        data-domain={domain}
        data-testid="phone-frame"
        className="relative mx-auto w-full max-w-[420px] lg:h-[860px] lg:rounded-[44px] lg:border-[12px] lg:border-slate-900 lg:shadow-2xl overflow-hidden bg-[#FAFAFA] flex flex-col"
        style={{ minHeight: "100vh" }}
      >
        {children}
      </div>
    </div>
  );
};
