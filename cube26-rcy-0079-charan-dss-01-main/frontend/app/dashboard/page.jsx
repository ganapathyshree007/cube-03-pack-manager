"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../components/Navbar";
import { useWorkspace } from "../../context/WorkspaceContext";
import { api } from "../../lib/api";
import Link from "next/link";
import {
  DollarSign,
  ShieldCheck,
  AlertCircle,
  FileQuestion,
  HelpCircle,
  ArrowUpRight,
  TrendingUp,
  Layers,
  CheckCircle2,
  ExternalLink,
  Shield,
  Activity,
  Zap,
  Scale,
  Sparkles,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { MetricCardSkeleton, TableSkeletonRows } from "../../components/LoadingSkeleton";

export default function DashboardPage() {
  const { currentCompany, currentCompanyName } = useWorkspace();
  const [metrics, setMetrics] = useState(null);
  const [recentCharges, setRecentCharges] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [m, c] = await Promise.all([
        api.getDashboardSummary(currentCompany),
        api.getCharges(currentCompany, { limit: 6 }),
      ]);
      setMetrics(m);
      setRecentCharges(c);
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentCompany]);

  // Financial currency formatting helper
  const formatAmount = (amt) => {
    if (amt === undefined || amt === null) return "$0.00";
    if (amt < 0) return `-$${Math.abs(amt).toFixed(2)}`;
    return `$${amt.toFixed(2)}`;
  };

  // Enterprise status token styling with semantic indicators
  const getBadgeClass = (assessment) => {
    switch (assessment) {
      case "CONTRADICTED":
        return {
          pill: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.15)]",
          dot: "bg-emerald-400",
        };
      case "SUPPORTED":
        return {
          pill: "bg-rose-500/10 text-rose-300 border-rose-500/30",
          dot: "bg-rose-400",
        };
      case "SILENT":
        return {
          pill: "bg-slate-800/80 text-slate-400 border-slate-700/60",
          dot: "bg-slate-500",
        };
      case "UNCERTAIN":
        return {
          pill: "bg-amber-500/10 text-amber-300 border-amber-500/30",
          dot: "bg-amber-400",
        };
      case "DUPLICATE":
        return {
          pill: "bg-orange-500/10 text-orange-300 border-orange-500/30",
          dot: "bg-orange-400",
        };
      case "ALREADY_REIMBURSED":
        return {
          pill: "bg-sky-500/10 text-sky-300 border-sky-500/30",
          dot: "bg-sky-400",
        };
      default:
        return {
          pill: "bg-slate-800 text-slate-300 border-slate-700",
          dot: "bg-slate-400",
        };
    }
  };

  // Aggregate verdict total for donut center display
  const totalVerdicts = metrics?.status_distribution?.reduce(
    (acc, curr) => acc + (curr.value || 0),
    0
  );

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#080c15]">
      <Navbar onRefresh={loadData} />

      <main className="p-8 space-y-8 w-full page-enter">
        {/* ============================================================ */}
        {/* 1. HERO PAGE HEADER                                          */}
        {/* ============================================================ */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2 border-b border-slate-800/50">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2.5">
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/50 border border-emerald-800/40 text-[10px] font-mono text-emerald-400 font-bold uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>Forensic Engine Online</span>
              </span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-[11px] font-mono text-slate-400">
                Audit Trail: <span className="text-emerald-400/90 font-semibold">Active RLS</span>
              </span>
            </div>

            <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-slate-100 font-sans">
              Recovery Operations Center
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
              Forensic operational evidence matching against channel fee deductions.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <Link
              href="/recovery"
              className="btn-primary group relative overflow-hidden"
            >
              <span>View Recoverable Claims</span>
              <ArrowUpRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
          </div>
        </div>

        {/* ============================================================ */}
        {/* 2. FINANCIAL RECOVERY INTELLIGENCE (KPI DECK)                */}
        {/* ============================================================ */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center space-x-2 text-[11px] uppercase tracking-wider font-bold text-slate-400 font-mono">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span>Financial Recovery Intelligence</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              Live Ledger Status
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {loading ? (
              <>
                <MetricCardSkeleton />
                <MetricCardSkeleton />
                <MetricCardSkeleton />
                <MetricCardSkeleton />
              </>
            ) : (
              <>
                {/* CARD 1: Total Deductions Assessed */}
                <div className="command-card p-5 rounded-2xl relative overflow-hidden group">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <span className="text-[11px] font-medium text-slate-400 tracking-wide uppercase">
                        Total Deductions Assessed
                      </span>
                      <h3 className="text-2xl lg:text-3xl font-bold text-slate-100 font-mono tabular-nums tracking-tight pt-1">
                        ${metrics?.total_fees?.toLocaleString("en-US", { minimumFractionDigits: 2 }) || "0.00"}
                      </h3>
                    </div>
                    <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 group-hover:text-slate-200 group-hover:border-slate-600 transition-all duration-200">
                      <DollarSign className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center text-xs text-slate-400">
                    <span>
                      Across <strong className="font-semibold text-slate-200 font-mono">{metrics?.total_charges_count || 0}</strong> financial line items
                    </span>
                  </div>
                </div>

                {/* CARD 2: Defensible Recovery Pipeline (Hero Card) */}
                <div className="command-card-hero p-5 rounded-2xl relative overflow-hidden group">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-[11px] font-semibold text-emerald-400 tracking-wide uppercase">
                          Defensible Recovery Pipeline
                        </span>
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      </div>
                      <h3 className="text-2xl lg:text-3xl font-extrabold text-emerald-300 font-mono tabular-nums tracking-tight pt-1 drop-shadow-[0_0_12px_rgba(16,185,129,0.3)]">
                        ${metrics?.potential_recovery?.toLocaleString("en-US", { minimumFractionDigits: 2 }) || "0.00"}
                      </h3>
                    </div>
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-300 group-hover:scale-105 transition-transform duration-200 shadow-glow">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-emerald-800/40 flex items-center text-xs text-emerald-400/90 font-medium">
                    <span>
                      <strong className="font-bold text-emerald-300 font-mono">{metrics?.contradicted_count || 0}</strong> charges contradicted by proof
                    </span>
                  </div>
                </div>

                {/* CARD 3: Claim Precision Rate */}
                <div className="command-card p-5 rounded-2xl relative overflow-hidden group">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <span className="text-[11px] font-medium text-slate-400 tracking-wide uppercase">
                        Claim Precision Rate
                      </span>
                      <h3 className="text-2xl lg:text-3xl font-bold text-slate-100 font-mono tabular-nums tracking-tight pt-1">
                        {metrics?.claim_precision_rate || 100}%
                      </h3>
                    </div>
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform duration-200">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center text-xs text-slate-400">
                    <span>Zero ungrounded disputes submitted</span>
                  </div>
                </div>

                {/* CARD 4: Conservative Skips */}
                <div className="command-card p-5 rounded-2xl relative overflow-hidden group">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <span className="text-[11px] font-medium text-slate-400 tracking-wide uppercase">
                        Conservative Skips
                      </span>
                      <h3 className="text-2xl lg:text-3xl font-bold text-amber-300 font-mono tabular-nums tracking-tight pt-1">
                        {(metrics?.silent_count || 0) + (metrics?.uncertain_count || 0)}
                      </h3>
                    </div>
                    <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 group-hover:scale-105 transition-transform duration-200">
                      <FileQuestion className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center text-xs text-slate-400 font-mono">
                    <span>
                      <strong className="text-slate-300">{metrics?.silent_count || 0}</strong> Silent &bull;{" "}
                      <strong className="text-amber-400">{metrics?.uncertain_count || 0}</strong> Uncertain
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* ============================================================ */}
        {/* 3. FORENSIC ANALYTICS GRID (DONUT & CATEGORY BAR)            */}
        {/* ============================================================ */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* CHART 1: Assessment Verdicts (Donut) */}
          <div className="command-card p-6 rounded-2xl flex flex-col justify-between">
            <div className="flex items-start justify-between border-b border-slate-800/60 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                    Evidence Assessment Verdicts
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Distribution of forensic match verdicts across all processed deductions.
                </p>
              </div>
              {totalVerdicts !== undefined && (
                <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800/80">
                  {totalVerdicts} Audited
                </span>
              )}
            </div>

            <div className="py-4 relative flex items-center justify-center min-h-[260px]">
              {metrics?.status_distribution ? (
                <div className="w-full h-64 relative flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={metrics.status_distribution}
                        innerRadius={70}
                        outerRadius={95}
                        paddingAngle={4}
                        dataKey="value"
                        stroke="none"
                        animationDuration={800}
                      >
                        {metrics.status_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "rgba(10, 15, 27, 0.95)",
                          borderColor: "rgba(51, 65, 85, 0.6)",
                          borderRadius: "12px",
                          fontSize: "12px",
                          color: "#f8fafc",
                          boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
                          backdropFilter: "blur(12px)",
                        }}
                        itemStyle={{ color: "#f1f5f9" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>

                  {/* Centered Donut Summary */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none">
                    <span className="text-2xl font-extrabold text-slate-100 font-mono tracking-tight">
                      {totalVerdicts ?? "--"}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest mt-0.5">
                      Verdicts
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center space-y-3 text-slate-500 py-16">
                  <div className="w-8 h-8 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                  <span className="text-xs font-mono">Synthesizing verdicts...</span>
                </div>
              )}
            </div>

            {/* Custom Interactive Legend Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-4 border-t border-slate-800/60 mt-2">
              {metrics?.status_distribution?.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center space-x-2.5 p-2 rounded-xl bg-slate-900/60 border border-slate-800/60 text-xs transition-colors hover:border-slate-700"
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0 shadow-sm"
                    style={{ backgroundColor: item.color }}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] text-slate-400 truncate">{item.name}</div>
                    <div className="font-bold text-slate-200 font-mono text-xs">{item.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CHART 2: Deductions by Category (Horizontal Bar) */}
          <div className="command-card p-6 rounded-2xl flex flex-col justify-between">
            <div className="flex items-start justify-between border-b border-slate-800/60 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-teal-400" />
                  <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                    Deductions by Category
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Top marketplace fee categories assessed for this seller.
                </p>
              </div>
              <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800/80">
                {metrics?.charge_type_distribution?.length || 0} Categories
              </span>
            </div>

            <div className="py-4 h-64">
              {metrics?.charge_type_distribution ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={metrics.charge_type_distribution}
                    layout="vertical"
                    margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(30, 41, 59, 0.4)" horizontal={false} />
                    <XAxis
                      type="number"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={{ stroke: "rgba(51, 65, 85, 0.5)" }}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      stroke="#94a3b8"
                      fontSize={11}
                      width={140}
                      tickLine={false}
                      axisLine={{ stroke: "rgba(51, 65, 85, 0.5)" }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(10, 15, 27, 0.95)",
                        borderColor: "rgba(51, 65, 85, 0.6)",
                        borderRadius: "12px",
                        fontSize: "12px",
                        color: "#f8fafc",
                        boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
                        backdropFilter: "blur(12px)",
                      }}
                      itemStyle={{ color: "#34d399" }}
                    />
                    <Bar
                      dataKey="count"
                      fill="#10b981"
                      radius={[0, 6, 6, 0]}
                      animationDuration={800}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex flex-col items-center justify-center space-y-3 text-slate-500 py-16">
                  <div className="w-8 h-8 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                  <span className="text-xs font-mono">Aggregating categories...</span>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-800/60 mt-2 flex items-center justify-between text-[11px] text-slate-400">
              <span>Classified via automated document parser</span>
              <span className="font-mono text-emerald-400 font-semibold">100% Channel Coverage</span>
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* 4. RECENT FINANCIAL DEDUCTIONS (HERO FORENSIC TABLE)         */}
        {/* ============================================================ */}
        <div className="command-card rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-slate-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                  Recent Financial Deductions
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Click any row to open the complete forensic investigation.
              </p>
            </div>
            <Link
              href="/charges"
              className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center space-x-1.5 transition-colors duration-200 self-start sm:self-center bg-emerald-950/40 border border-emerald-800/40 px-3 py-1.5 rounded-lg group"
            >
              <span>Explore All Charges</span>
              <ArrowUpRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800/60 text-[11px] font-mono">
                <tr>
                  <th className="py-3.5 px-5">Charge ID</th>
                  <th className="py-3.5 px-5">Unit / Shipment</th>
                  <th className="py-3.5 px-5">Deduction Reason</th>
                  <th className="py-3.5 px-5 text-right">Fee Amount</th>
                  <th className="py-3.5 px-5">Forensic Assessment</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-300">
                {loading ? (
                  <TableSkeletonRows rows={5} cols={6} />
                ) : recentCharges.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-16 text-center text-slate-500">
                      No deductions recorded for this workspace yet.
                    </td>
                  </tr>
                ) : (
                  recentCharges.map((c) => {
                    const badge = getBadgeClass(c.assessment);
                    return (
                      <tr
                        key={c.id}
                        className="table-row-hover group cursor-pointer transition-colors duration-150"
                      >
                        <td className="py-4 px-5 font-mono font-medium text-slate-200">
                          <span className="bg-slate-900 border border-slate-800 px-2 py-1 rounded-md text-[11px] text-slate-300 group-hover:border-slate-700 transition-colors">
                            {c.charge_id}
                          </span>
                        </td>
                        <td className="py-4 px-5">
                          <div className="font-mono text-emerald-400 font-semibold text-xs">
                            {c.unit_id || "N/A"}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                            {c.shipment_id || c.order_id || ""}
                          </div>
                        </td>
                        <td className="py-4 px-5 capitalize font-medium text-slate-200">
                          {c.reason.replace(/_/g, " ")}
                        </td>
                        <td className="py-4 px-5 text-right font-mono font-bold text-slate-100 tabular-nums text-xs">
                          {formatAmount(c.amount)}
                        </td>
                        <td className="py-4 px-5">
                          <span
                            className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${badge.pill}`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                            <span>{c.assessment}</span>
                          </span>
                        </td>
                        <td className="py-4 px-5 text-right">
                          <Link
                            href={`/investigations/${c.charge_id}`}
                            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold border border-slate-700/50 transition-all duration-200 group-hover:border-emerald-500/40 group-hover:text-emerald-300"
                          >
                            <span>Investigate</span>
                            <ExternalLink className="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
