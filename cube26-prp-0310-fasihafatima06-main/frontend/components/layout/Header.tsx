"use client";
import React from "react";
import { ShieldAlert, Search, User, SlidersHorizontal } from "lucide-react";
import Link from "next/link";

export const Header: React.FC = () => {
  return (
    <header className="h-16 bg-[#714B67] border-b border-[#5B3B53] px-6 flex items-center justify-between sticky top-0 z-30 shadow-md">
      {/* Brand Logo & Title */}
      <div className="flex items-center gap-3">
        <div className="bg-[#00A09D] text-white p-2 rounded-xl font-bold shadow-md shadow-[#00A09D]/20">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-extrabold text-white tracking-tight text-lg">AgentPrep</h1>
            <span className="text-[10px] font-bold uppercase tracking-wider bg-white/15 text-purple-100 px-2.5 py-0.5 rounded-full border border-white/20">
              CUBE AI Agent
            </span>
          </div>
          <p className="text-xs text-purple-200 tracking-tight font-medium">Visual Prep Compliance Agent</p>
        </div>
      </div>

      {/* Quick Lookup Bar */}
      <div className="hidden md:flex items-center gap-2 bg-white/10 border border-white/20 rounded-xl px-3.5 py-1.5 w-80 focus-within:border-[#00A09D] focus-within:bg-white/15 transition-all">
        <Search className="w-4 h-4 text-purple-200" />
        <input
          type="text"
          placeholder="Lookup Inspection ID or ASIN..."
          className="bg-transparent text-xs text-white placeholder-purple-200 focus:outline-none w-full font-sans"
        />
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-white/10 px-3.5 py-1.5 rounded-xl border border-white/20">
          <div className="w-2 h-2 rounded-full bg-[#00A09D] animate-pulse"></div>
          <User className="w-3.5 h-3.5 text-[#00A09D]" />
          <span className="text-xs text-white font-semibold">Operator #104</span>
        </div>
        <Link
          href="/rules"
          className="p-2 text-purple-200 hover:text-white hover:bg-white/10 rounded-xl transition-all"
          title="System Settings & Rules"
        >
          <SlidersHorizontal className="w-4 h-4" />
        </Link>
      </div>
    </header>
  );
};
