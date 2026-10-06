"use client";
import React from "react";
import {
  PackageCheck,
  CheckCircle,
  Truck,
  RotateCcw,
  Receipt,
  AlertTriangle,
  Clock,
  Layers,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

export default function EvidenceTimeline({ timeline = [] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="p-12 text-center bg-slate-900/30 rounded-2xl border border-slate-800/50 text-slate-500 text-xs">
        No chronological operational events recorded for this unit.
      </div>
    );
  }

  const getIcon = (type) => {
    switch (type) {
      case "RECEIVING":
        return <PackageCheck className="w-4 h-4 text-sky-400" />;
      case "PREP":
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case "PACK":
        return <Layers className="w-4 h-4 text-indigo-400" />;
      case "RETURNS":
        return <RotateCcw className="w-4 h-4 text-purple-400" />;
      case "FINANCIAL_CHARGE":
        return <Receipt className="w-4 h-4 text-rose-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getCardStyle = (type) => {
    switch (type) {
      case "RECEIVING":
        return "border-sky-500/30 bg-sky-950/15 hover:border-sky-500/50";
      case "PREP":
        return "border-emerald-500/30 bg-emerald-950/15 hover:border-emerald-500/50";
      case "PACK":
        return "border-indigo-500/30 bg-indigo-950/15 hover:border-indigo-500/50";
      case "RETURNS":
        return "border-purple-500/30 bg-purple-950/15 hover:border-purple-500/50";
      case "FINANCIAL_CHARGE":
        return "border-rose-500/30 bg-rose-950/15 hover:border-rose-500/50";
      default:
        return "border-slate-800/50 bg-slate-900/60 hover:border-slate-700/60";
    }
  };

  const getNodeColor = (type) => {
    switch (type) {
      case "RECEIVING":
        return "bg-sky-400 ring-sky-400/20";
      case "PREP":
        return "bg-emerald-400 ring-emerald-400/20";
      case "PACK":
        return "bg-indigo-400 ring-indigo-400/20";
      case "RETURNS":
        return "bg-purple-400 ring-purple-400/20";
      case "FINANCIAL_CHARGE":
        return "bg-rose-400 ring-rose-400/20";
      default:
        return "bg-slate-400 ring-slate-400/20";
    }
  };

  return (
    <div className="relative pl-8 space-y-6 before:absolute before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-emerald-500/50 before:via-slate-800 before:to-slate-800">
      {timeline.map((event, idx) => (
        <div key={idx} className="relative flex items-start space-x-4 group">
          {/* Node Dot with Glow */}
          <div className="absolute -left-8 top-1.5 w-7 h-7 rounded-full bg-slate-950 border-2 border-slate-800 flex items-center justify-center group-hover:border-slate-700 transition-colors duration-200">
            <span className={`w-2.5 h-2.5 rounded-full ${getNodeColor(event.type)} ring-4`} />
          </div>

          {/* Event Content Card */}
          <div className={`flex-1 p-5 rounded-2xl border ${getCardStyle(event.type)} transition-all duration-200 shadow-card card-hover`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mb-2">
              <div className="flex items-center space-x-2.5">
                <div className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
                  {getIcon(event.type)}
                </div>
                <h4 className="font-semibold text-xs text-slate-100">{event.title}</h4>
              </div>
              <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-1.5 bg-slate-950/50 px-2.5 py-1 rounded-lg border border-slate-800/50">
                <Clock className="w-3 h-3 text-slate-500" />
                <span>{event.timestamp || "Undated"}</span>
              </div>
            </div>

            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              {event.description}
            </p>

            {event.finding && (
              <div className="mt-3 flex items-center space-x-2">
                <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Custody Status:</span>
                <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold border ${
                  event.finding === "PASS"
                    ? "bg-emerald-950/60 text-emerald-400 border-emerald-800/50"
                    : event.finding === "FAIL"
                    ? "bg-rose-950/60 text-rose-400 border-rose-800/50"
                    : "bg-slate-900 text-slate-300 border-slate-700/60"
                }`}>
                  <span>{event.finding}</span>
                </span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
