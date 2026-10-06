"use client";
import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Receipt,
  FileCheck2,
  TrendingUp,
  FolderSync,
  Database,
  ShieldCheck,
  Scale,
  ChevronLeft,
  ChevronRight,
  Activity,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Operations Center", href: "/dashboard", icon: LayoutDashboard },
  { name: "Charges Explorer", href: "/charges", icon: Receipt },
  { name: "Recovery Pipeline", href: "/recovery", icon: TrendingUp },
  { name: "Evidence Records", href: "/evidence", icon: FolderSync },
  { name: "Claims & Audit", href: "/claims", icon: FileCheck2 },
  { name: "Data Ingestion", href: "/data-sources", icon: Database },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`${
        collapsed ? "w-[72px]" : "w-64"
      } h-screen bg-[#0a0f1b] border-r border-slate-800/60 flex flex-col justify-between shrink-0 select-none z-30 transition-all duration-300 ease-in-out`}
    >
      <div className="flex flex-col">
        {/* Brand Header: exactly h-16 (64px) with border-b, matching the header */}
        <div
          className={`h-16 border-b border-slate-800/60 flex items-center ${
            collapsed ? "justify-center px-2" : "px-5 space-x-3.5"
          }`}
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/25 via-emerald-600/10 to-transparent border border-emerald-500/35 flex items-center justify-center text-emerald-400 shadow-glow shrink-0">
            <Scale className="w-4 h-4 drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
          </div>
          {!collapsed && (
            <div className="animate-fade-in min-w-0">
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-slate-100 tracking-tight text-sm font-sans">
                  RCY RECOVERY
                </span>
                <span className="text-[10px] bg-emerald-500/15 text-emerald-300 font-mono px-1.5 py-0.5 rounded-md font-semibold border border-emerald-500/25">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium truncate mt-0.5">
                Evidence Operations Center
              </p>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {!collapsed && (
            <div className="px-3 pt-3 pb-2 text-[10px] font-semibold tracking-widest text-slate-500 uppercase flex items-center justify-between">
              <span>Platform Systems</span>
              <Activity className="w-3 h-3 text-slate-600" />
            </div>
          )}
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.name : undefined}
                className={`relative flex items-center ${
                  collapsed ? "justify-center px-2" : "space-x-3 px-3.5"
                } py-2.5 rounded-xl text-xs font-medium transition-all duration-200 group ${
                  isActive
                    ? "bg-emerald-500/12 text-emerald-300 border border-emerald-500/25 shadow-sm shadow-emerald-950/40 font-semibold"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40 border border-transparent"
                }`}
              >
                {/* Active indicator bar */}
                {isActive && !collapsed && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-emerald-400 rounded-r-full shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                )}
                <Icon
                  className={`w-4 h-4 shrink-0 transition-transform duration-200 group-hover:scale-105 ${
                    isActive
                      ? "text-emerald-400 drop-shadow-[0_0_6px_rgba(16,185,129,0.5)]"
                      : "text-slate-400 group-hover:text-slate-200"
                  }`}
                />
                {!collapsed && <span className="truncate">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section */}
      <div className="space-y-3 p-3">
        {/* Conservative AI Engine card */}
        {!collapsed && (
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900/80 to-slate-950/90 border border-slate-800/80 text-xs shadow-card animate-fade-in relative overflow-hidden group">
            {/* Ambient inner glow */}
            <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />

            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2 text-slate-200 font-semibold text-xs">
                <div className="w-6 h-6 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                </div>
                <span>Conservative AI</span>
              </div>
              {/* Animated Live Beacon */}
              <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-800/50">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[9px] font-mono text-emerald-400 font-bold tracking-wider">ACTIVE</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed mt-2">
              Zero hallucinated claims. Missing physical proof strictly yields{" "}
              <span className="font-mono text-slate-200 font-bold bg-slate-800/80 px-1 py-0.5 rounded text-[10px] border border-slate-700/60">
                SILENT
              </span>.
            </p>
          </div>
        )}

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="w-full flex items-center justify-center py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-all duration-200 border border-transparent hover:border-slate-800"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
