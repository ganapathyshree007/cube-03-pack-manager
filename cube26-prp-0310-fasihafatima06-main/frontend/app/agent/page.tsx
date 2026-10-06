"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, Clock } from "lucide-react";
import { fetchAgentActivity, fetchAgentStatus } from "@/lib/api";
import { AgentEvent, AgentStatus } from "@/lib/types";

export default function AgentActivityPage() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [status, setStatus] = useState<AgentStatus | null>(null);

  useEffect(() => {
    fetchAgentActivity().then(setEvents).catch(console.error);
    fetchAgentStatus().then(setStatus).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 max-w-[1500px] mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-[#714B67]" />
          Prep Manager Agent Activity & Orchestration Audit Trail
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Granular event trace showing multi-agent coordinator execution, worker subagent invocations, and evidence reasoning.
        </p>
      </div>

      {/* Active Subagents Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {status?.active_subagents.map((sub, idx) => (
          <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center justify-between shadow-sm">
            <div>
              <div className="font-extrabold text-xs text-slate-900">{sub.name}</div>
              <div className="text-[10px] text-slate-500 font-medium">{sub.role}</div>
            </div>
            <span className="bg-[#E6F6F6] text-[#00A09D] text-[10px] font-mono px-2.5 py-0.5 rounded-full border border-[#BCE7E6] font-bold">
              {sub.status}
            </span>
          </div>
        ))}
      </div>

      {/* Timeline List */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
        <h3 className="text-sm font-extrabold text-slate-900 border-b border-slate-100 pb-3 flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#714B67]" />
          Event Execution Timeline ({events.length})
        </h3>

        {events.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 font-mono">
            No agent events logged yet. Perform an inspection to see the event timeline populate.
          </div>
        ) : (
          <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {events.map((ev) => {
              const dateStr = new Date(ev.timestamp).toLocaleTimeString();

              return (
                <div key={ev.id} className="relative group">
                  {/* Timeline Bullet */}
                  <span className={`absolute -left-6 top-1 w-3 h-3 rounded-full border-2 border-white ${
                    ev.status === "SUCCESS"
                      ? "bg-emerald-500"
                      : ev.status === "WARNING"
                      ? "bg-amber-500"
                      : ev.status === "ERROR"
                      ? "bg-rose-500"
                      : "bg-[#714B67]"
                  }`}></span>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1.5 hover:border-slate-300 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-xs text-[#714B67] font-mono">{ev.agent_name}</span>
                        <span className="text-[10px] uppercase font-mono bg-slate-200 text-slate-800 font-bold px-2 py-0.5 rounded">
                          {ev.stage}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">{dateStr}</span>
                    </div>

                    <p className="text-xs text-slate-800 leading-relaxed font-sans font-medium">{ev.message}</p>

                    <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500 font-mono">
                      <span>Inspection: <Link href={`/inspection/${ev.inspection_id}`} className="text-[#714B67] font-bold hover:underline">{ev.inspection_id}</Link></span>
                      <span className="text-slate-400">Event ID: {ev.id}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
