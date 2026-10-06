"use client";
import React from "react";
import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";

export default function AppShell({ children }) {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  // When visiting the landing page (/), render full-width without the dashboard sidebar
  if (isLanding) {
    return (
      <div className="min-h-screen w-full bg-[#080c15] text-slate-100 overflow-x-hidden selection:bg-emerald-500/20 selection:text-emerald-300">
        {children}
      </div>
    );
  }

  // When visiting dashboard or internal routes, render the fixed sidebar + main area shell
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#080c15]">
      {/* 1. FIXED SIDEBAR: Fixed to LEFT, full viewport height, non-scrolling, w-64 */}
      <Sidebar />

      {/* 2. MAIN AREA: Begins exactly at sidebar right edge, width = viewport - sidebar */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto overflow-x-hidden">
        {children}
      </div>
    </div>
  );
}
