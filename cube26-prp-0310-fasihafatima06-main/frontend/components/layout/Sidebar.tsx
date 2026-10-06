"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PlusCircle,
  History,
  Package,
  FileCheck2,
  Activity,
  ChevronRight,
  Sparkles
} from "lucide-react";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "New Inspection", href: "/inspect", icon: PlusCircle },
  { name: "Inspection History", href: "/history", icon: History },
  { name: "Products & Rules", href: "/products", icon: Package },
  { name: "Preparation Rules", href: "/rules", icon: FileCheck2 },
  { name: "Agent Activity", href: "/agent", icon: Activity },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between h-[calc(100vh-4rem-2.5rem)] sticky top-16 shadow-sm">
      <div className="p-4 space-y-1">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2 flex items-center justify-between">
          <span>Inbound Operations</span>
          <Sparkles className="w-3.5 h-3.5 text-[#00A09D]" />
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                isActive
                  ? "bg-[#F3EDF2] text-[#714B67] border border-[#E4D6E2] shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-[#714B67]" : "text-slate-400"}`} />
                <span>{item.name}</span>
              </div>
              {isActive && <ChevronRight className="w-3.5 h-3.5 text-[#714B67]" />}
            </Link>
          );
        })}
      </div>

      {/* Quick Status Box */}
      <div className="p-4 border border-[#E4D6E2] bg-[#F3EDF2]/50 rounded-2xl m-3">
        <div className="text-[11px] font-bold text-[#714B67] mb-1 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#00A09D] animate-pulse"></span>
          Prep Manager Orchestrator
        </div>
        <p className="text-[10px] text-slate-600 leading-relaxed font-medium">
          6 Worker Subagents active. Strict 3-State Decision Model.
        </p>
      </div>
    </aside>
  );
};
