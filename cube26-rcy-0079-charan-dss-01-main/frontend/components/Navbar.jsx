"use client";
import React, { useState, useRef, useEffect } from "react";
import { useWorkspace } from "../context/WorkspaceContext";
import { Building2, ChevronDown, Check, RefreshCw, Shield } from "lucide-react";
import { api } from "../lib/api";

export default function Navbar({ onRefresh }) {
  const { companies, currentCompany, currentCompanyName, switchCompany } = useWorkspace();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [runningBatch, setRunningBatch] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleBatchAnalyze = async () => {
    try {
      setRunningBatch(true);
      setBatchResult(null);
      const res = await api.batchInvestigate(currentCompany);
      setBatchResult(res);
      if (onRefresh) onRefresh();
      setTimeout(() => setBatchResult(null), 8000);
    } catch (err) {
      console.error("Batch investigation failed:", err);
      alert(`Recovery Agent run failed: ${err.message}`);
    } finally {
      setRunningBatch(false);
    }
  };

  return (
    <header className="h-16 w-full bg-[#0a0f1b] border-b border-slate-800/60 sticky top-0 z-20 shrink-0 select-none">
      <div className="w-full h-full px-8 flex items-center justify-between">
        {/* Left Side: Enterprise Tenant Switcher & Security Status */}
        <div className="flex items-center space-x-3">
          {/* Tenant Switcher Button */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="h-9 px-3.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 flex items-center space-x-2.5 text-xs font-semibold text-slate-100 transition-all duration-150 shadow-sm group"
            >
              <div className="w-5 h-5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform duration-200 shrink-0">
                <Building2 className="w-3.5 h-3.5" />
              </div>
              <span className="font-semibold text-slate-100 tracking-tight">{currentCompanyName}</span>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {dropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-72 rounded-2xl bg-slate-900/95 backdrop-blur-2xl border border-slate-700 shadow-modal p-2 z-50 animate-scale-in">
                <div className="px-3 py-2 text-[10px] font-bold tracking-wider uppercase text-slate-400 border-b border-slate-800 flex items-center justify-between">
                  <span>Enterprise Workspaces</span>
                  <span className="text-[9px] font-mono text-emerald-400 font-semibold">RLS ENABLED</span>
                </div>
                <div className="space-y-1 mt-1.5">
                  {companies.map((comp) => {
                    const isSelected = comp.id === currentCompany;
                    return (
                      <button
                        key={comp.id}
                        onClick={() => {
                          switchCompany(comp.id);
                          setDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2.5 rounded-xl text-xs flex items-center justify-between transition-all duration-150 ${
                          isSelected
                            ? "bg-emerald-500/15 text-emerald-300 font-semibold border border-emerald-500/30"
                            : "text-slate-300 hover:bg-slate-800/60 hover:text-slate-100"
                        }`}
                      >
                        <div>
                          <div className="font-medium text-slate-200">{comp.name}</div>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">{comp.id}</div>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-emerald-400 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Tenant Isolation Status Pill */}
          <div className="h-9 hidden sm:flex items-center space-x-2 px-3 rounded-xl bg-emerald-950/25 border border-emerald-800/30 text-xs text-emerald-400/90 font-medium select-none">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
            <Shield className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="tracking-tight text-[11px] font-semibold">Tenant Isolated RLS</span>
          </div>
        </div>

        {/* Right Side: Hero Recovery Action, Divider & User Profile */}
        <div className="flex items-center space-x-3.5">
          {/* Run Recovery Agent Button */}
          <button
            onClick={handleBatchAnalyze}
            disabled={runningBatch}
            className="h-9 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:from-emerald-700 active:to-teal-700 text-white font-semibold text-xs flex items-center space-x-2 shadow-sm shadow-emerald-950/40 hover:shadow-emerald-900/40 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <RefreshCw className={`w-3.5 h-3.5 shrink-0 ${runningBatch ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
            <span>{runningBatch ? "Evaluating Evidence..." : "Run Recovery Agent"}</span>
          </button>

          {/* Vertical Separator */}
          <div className="h-5 w-px bg-slate-800/80 mx-0.5" />

          {/* User Profile Area */}
          <div className="h-9 flex items-center space-x-2.5 pl-1 cursor-default select-none">
            <div className="relative shrink-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500/25 via-slate-800 to-slate-900 border border-emerald-500/40 flex items-center justify-center font-bold text-xs text-emerald-300 shadow-sm">
                SC
              </div>
              <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-[#0a0f1b]" />
            </div>
            <div className="text-left hidden md:block">
              <div className="text-xs font-semibold text-slate-200 leading-tight">Sarah Chen</div>
              <div className="text-[10px] text-slate-400 leading-tight">Claims Analyst</div>
            </div>
          </div>
        </div>
      </div>

      {/* Batch run result toast */}
      {batchResult && (
        <div className="absolute top-16 right-8 mt-2 p-4 bg-slate-900/95 backdrop-blur-2xl border border-emerald-600/50 rounded-2xl shadow-modal text-xs text-emerald-200 z-50 flex items-center space-x-3 animate-fade-in-down max-w-lg">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-400">
            <Check className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-emerald-300">Recovery Agent Evaluation Complete</div>
            <div className="text-[11px] text-slate-300 font-mono mt-0.5">
              {batchResult.processed} evaluated &bull;{" "}
              <span className="text-emerald-400 font-bold">{batchResult.contradicted} Recoverable</span> &bull;{" "}
              {batchResult.silent} Silent &bull; {batchResult.uncertain} Uncertain &bull;{" "}
              {batchResult.supported} Supported
            </div>
          </div>
          <button
            onClick={() => setBatchResult(null)}
            className="text-slate-400 hover:text-white text-base ml-2 shrink-0 p-1"
          >
            &times;
          </button>
        </div>
      )}
    </header>
  );
}
