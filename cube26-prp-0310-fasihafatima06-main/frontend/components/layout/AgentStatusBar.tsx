"use client";
import React, { useEffect, useState } from "react";
import { Cpu, ShieldCheck } from "lucide-react";
import { fetchAgentStatus } from "@/lib/api";
import { AgentStatus } from "@/lib/types";

export const AgentStatusBar: React.FC = () => {
  const [status, setStatus] = useState<AgentStatus | null>(null);

  useEffect(() => {
    fetchAgentStatus()
      .then(setStatus)
      .catch((err) => console.error("Status fetch error:", err));
  }, []);

  return (
    <footer className="h-10 bg-[#1F2937] border-t border-slate-700 px-6 flex items-center justify-between text-xs text-slate-300 fixed bottom-0 left-0 right-0 z-40">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#00A09D] animate-pulse"></span>
          <span className="font-semibold text-slate-200">Agent status:</span>
          <span className="text-[#00A09D] font-bold">{status?.agent_status || "Ready / Active"}</span>
        </div>

        <div className="hidden sm:flex items-center gap-2 border-l border-slate-700 pl-6">
          <Cpu className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-semibold text-slate-200">Vision engine:</span>
          <span className="text-slate-200 font-mono text-[11px] bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            {status?.vision_engine || "Local AI Engine"}
          </span>
        </div>

        <div className="hidden md:flex items-center gap-2 border-l border-slate-700 pl-6">
          <ShieldCheck className="w-3.5 h-3.5 text-[#00A09D]" />
          <span className="font-semibold text-slate-200">Active Workers:</span>
          <span className="text-slate-300">6 Subagents Online</span>
        </div>
      </div>

      <div className="flex items-center gap-4 text-[11px] text-slate-400">
        <span>CUBE Prep Manager Standard</span>
        <span className="border-l border-slate-700 pl-4">Strict 3-State Model</span>
      </div>
    </footer>
  );
};
