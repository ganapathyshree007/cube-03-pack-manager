"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { History, Filter, Search } from "lucide-react";
import { fetchInspections } from "@/lib/api";
import { InspectionResponse } from "@/lib/types";
import { StatusBadge } from "@/components/common/StatusBadge";

export default function HistoryPage() {
  const [inspections, setInspections] = useState<InspectionResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    fetchInspections().then(setInspections).catch(console.error);
  }, []);

  const filtered = inspections.filter((ins) => {
    if (statusFilter !== "ALL" && ins.overall_status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchId = ins.inspection_id.toLowerCase().includes(q);
      const matchProd = (ins.product_name || ins.product_id).toLowerCase().includes(q);
      if (!matchId && !matchProd) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 max-w-[1500px] mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <History className="w-5 h-5 text-[#714B67]" />
            Inspection Audit History
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Complete historical database of inbound prep inspections, decisions, and evidence logs.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-1.5 text-xs">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID or Product..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-slate-900 placeholder-slate-400 focus:outline-none w-40 font-sans"
            />
          </div>

          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 p-1 rounded-xl text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            {["ALL", "PASS", "FAIL", "UNCERTAIN"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg text-[11px] font-bold transition-all ${
                  statusFilter === st
                    ? "bg-[#714B67] text-white shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs font-mono">
            No inspection records match the current filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="p-3.5 font-bold">Inspection ID</th>
                  <th className="p-3.5 font-bold">Product Name</th>
                  <th className="p-3.5 font-bold">Work Order</th>
                  <th className="p-3.5 font-bold">Date & Time</th>
                  <th className="p-3.5 font-bold">Status</th>
                  <th className="p-3.5 font-bold">Operator</th>
                  <th className="p-3.5 font-bold">Engine Mode</th>
                  <th className="p-3.5 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {filtered.map((ins) => (
                  <tr key={ins.inspection_id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-3.5 font-bold text-slate-900">{ins.inspection_id}</td>
                    <td className="p-3.5 font-sans text-slate-900 font-bold">
                      {ins.product_name || ins.product_id}
                    </td>
                    <td className="p-3.5 text-slate-500">{ins.work_order_id || "WO-88902"}</td>
                    <td className="p-3.5 text-slate-500 font-sans">
                      {new Date(ins.created_at).toLocaleString()}
                    </td>
                    <td className="p-3.5">
                      <StatusBadge status={ins.overall_status} size="sm" />
                    </td>
                    <td className="p-3.5 text-slate-700 font-sans font-medium">{ins.operator_name}</td>
                    <td className="p-3.5 text-slate-600 font-sans">
                      <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md text-[10px] border border-slate-200 font-medium">
                        {ins.mode}
                      </span>
                    </td>
                    <td className="p-3.5 text-right font-sans">
                      <Link
                        href={`/inspection/${ins.inspection_id}`}
                        className="text-[#714B67] hover:text-[#5B3B53] font-bold hover:underline"
                      >
                        View Record →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
