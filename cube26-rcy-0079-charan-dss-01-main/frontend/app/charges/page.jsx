"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../components/Navbar";
import { useWorkspace } from "../../context/WorkspaceContext";
import { api } from "../../lib/api";
import Link from "next/link";
import {
  Search,
  Filter,
  ExternalLink,
  RefreshCw,
  TrendingUp,
  FileQuestion,
  AlertCircle,
  Receipt,
  Download,
} from "lucide-react";
import { TableSkeletonRows } from "../../components/LoadingSkeleton";

export default function ChargesPage() {
  const { currentCompany } = useWorkspace();
  const [charges, setCharges] = useState([]);
  const [search, setSearch] = useState("");
  const [assessmentFilter, setAssessmentFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  const loadCharges = async () => {
    try {
      setLoading(true);
      const data = await api.getCharges(currentCompany, {
        search: search || undefined,
        assessment: assessmentFilter !== "ALL" ? assessmentFilter : undefined,
      });
      setCharges(data);
    } catch (err) {
      console.error("Failed to load charges:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCharges();
  }, [currentCompany, assessmentFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadCharges();
  };

  const getBadgeClass = (assessment) => {
    if (assessment === "CONTRADICTED") return "badge-contradicted";
    if (assessment === "SILENT") return "badge-silent";
    if (assessment === "UNCERTAIN") return "badge-uncertain";
    if (assessment === "SUPPORTED") return "badge-supported";
    return "bg-slate-800 text-slate-300 border border-slate-700";
  };

  return (
    <div className="flex-1 flex flex-col">
      <Navbar onRefresh={loadCharges} />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">Charges Explorer</h1>
            <p className="text-sm text-slate-500 mt-1.5">
              Filter and investigate channel deductions across inbound, inventory loss, and returns.
            </p>
          </div>
          <div className="text-xs text-slate-500">
            {loading ? (
              <div className="h-4 w-28 bg-slate-800/60 rounded-md" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
            ) : (
              <>Showing <span className="font-semibold text-slate-200">{charges.length}</span> charges</>
            )}
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 glass-surface-strong p-3 rounded-2xl">
          <form onSubmit={handleSearchSubmit} className="flex-1 relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by Charge ID, Unit ID, Shipment ID, or Reason..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950/50 border border-slate-800/50 rounded-xl text-xs text-slate-200 placeholder-slate-600 input-focus"
            />
          </form>

          {/* Assessment Filter Pills */}
          <div className="flex items-center space-x-1 overflow-x-auto pb-1 md:pb-0">
            {["ALL", "CONTRADICTED", "SILENT", "UNCERTAIN", "SUPPORTED"].map((f) => (
              <button
                key={f}
                onClick={() => setAssessmentFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap ${
                  assessmentFilter === f
                    ? "bg-emerald-600 text-white font-semibold shadow-sm shadow-emerald-950/30"
                    : "text-slate-500 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/50 overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/40 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-800/50">
                <tr>
                  <th className="py-3 px-4">Charge ID</th>
                  <th className="py-3 px-4">Unit ID</th>
                  <th className="py-3 px-4">Shipment / Order</th>
                  <th className="py-3 px-4">SKU / FNSKU</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4">Posted Date</th>
                  <th className="py-3 px-4">Verdict</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-300">
                {loading ? (
                  <TableSkeletonRows rows={7} cols={9} />
                ) : charges.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-16 text-center text-slate-500">
                      No charges match the selected filter.
                    </td>
                  </tr>
                ) : (
                  charges.map((c) => (
                    <tr key={c.id} className="table-row-hover">
                      <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                        {c.charge_id}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-emerald-400">
                        {c.unit_id || "\u2014"}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-400">
                        {c.shipment_id || c.order_id || "\u2014"}
                      </td>
                      <td className="py-3.5 px-4 text-slate-300">
                        <div>{c.sku || "\u2014"}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{c.fnsku || ""}</div>
                      </td>
                      <td className="py-3.5 px-4 capitalize text-slate-200 font-medium">
                        {c.reason.replace(/_/g, " ")}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-slate-100 tabular-nums">
                        ${c.amount.toFixed(2)}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {c.charge_date || "\u2014"}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${getBadgeClass(c.assessment)}`}>
                          {c.assessment}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/investigations/${c.charge_id}`}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 text-xs font-medium border border-emerald-500/20 transition-all duration-200"
                        >
                          <span>Investigate</span>
                          <ExternalLink className="w-3 h-3 ml-0.5" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
