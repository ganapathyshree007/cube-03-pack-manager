"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  PlusCircle,
  ArrowRight,
  ShieldAlert,
  Play,
  Clock,
  Sparkles,
  Package
} from "lucide-react";
import { fetchInspections, fetchTestScenarios, fetchAgentStatus, createInspection } from "@/lib/api";
import { InspectionResponse, TestScenario, AgentStatus } from "@/lib/types";
import { StatusBadge } from "@/components/common/StatusBadge";

export default function DashboardPage() {
  const router = useRouter();
  const [inspections, setInspections] = useState<InspectionResponse[]>([]);
  const [scenarios, setScenarios] = useState<TestScenario[]>([]);
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);

  useEffect(() => {
    fetchInspections().then(setInspections).catch(console.error);
    fetchTestScenarios().then(setScenarios).catch(console.error);
    fetchAgentStatus().then(setStatus).catch(console.error);
  }, []);

  const handleRunScenario = async (sc: TestScenario) => {
    setLoadingScenario(sc.id);
    try {
      const formData = new FormData();
      formData.append("product_id", sc.product_id);
      formData.append("scenario_id", sc.id);
      formData.append("work_order_id", `WO-${Math.floor(10000 + Math.random() * 90000)}`);
      formData.append("operator_name", "Operator #104");

      const res = await createInspection(formData);
      router.push(`/inspection/${res.inspection_id}`);
    } catch (err) {
      console.error("Scenario run failed:", err);
      alert("Failed to run scenario test.");
    } finally {
      setLoadingScenario(null);
    }
  };

  const total = inspections.length;
  const passCount = inspections.filter((i) => i.overall_status === "PASS").length;
  const failCount = inspections.filter((i) => i.overall_status === "FAIL").length;
  const uncertainCount = inspections.filter((i) => i.overall_status === "UNCERTAIN").length;

  return (
    <div className="space-y-6 max-w-[1500px] mx-auto">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-extrabold text-slate-900">Warehouse Inbound Prep Workspace</h2>
            <span className="bg-[#F3EDF2] text-[#714B67] text-xs px-3 py-1 rounded-full font-bold border border-[#E4D6E2] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00A09D] animate-pulse"></span>
              Prep Manager Active
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1.5 max-w-2xl leading-relaxed">
            Real-time visual compliance verification for inbound items. Analyzes product photographs against multi-step prep rules using strict PASS / FAIL / UNCERTAIN decision logic.
          </p>
        </div>
        <Link
          href="/inspect"
          className="btn-odoo text-white font-bold px-5 py-2.5 rounded-xl text-xs flex items-center gap-2 shrink-0 shadow-sm"
        >
          <PlusCircle className="w-4 h-4" />
          Start New Inspection
        </Link>
      </div>

      {/* Operational Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs text-slate-500 font-bold block">Total Inspections</span>
            <span className="text-2xl font-black text-slate-900 font-mono mt-0.5 block">{total}</span>
          </div>
          <div className="p-3 bg-[#F3EDF2] rounded-xl text-[#714B67]">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs text-slate-500 font-bold block">Verified Compliant</span>
            <span className="text-2xl font-black text-[#00A09D] font-mono mt-0.5 block">{passCount}</span>
          </div>
          <div className="p-3 bg-[#E6F6F6] rounded-xl text-[#00A09D] border border-[#BCE7E6]">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs text-slate-500 font-bold block">Non-Compliant (FAIL)</span>
            <span className="text-2xl font-black text-rose-600 font-mono mt-0.5 block">{failCount}</span>
          </div>
          <div className="p-3 bg-rose-50 rounded-xl text-rose-600 border border-rose-200">
            <XCircle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs text-slate-500 font-bold block">Needs Evidence (UNCERTAIN)</span>
            <span className="text-2xl font-black text-amber-600 font-mono mt-0.5 block">{uncertainCount}</span>
          </div>
          <div className="p-3 bg-amber-50 rounded-xl text-amber-600 border border-amber-200">
            <HelpCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 1-Click Test Scenarios Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#714B67]" />
            <h3 className="text-sm font-extrabold text-slate-900">1-Click Reproducible Test Scenarios</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">Spec Scenarios 1–7</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {scenarios.map((sc) => {
            const isLoading = loadingScenario === sc.id;
            return (
              <div
                key={sc.id}
                className="bg-slate-50 border border-slate-200 hover:border-[#714B67] rounded-xl p-3.5 flex flex-col justify-between gap-3 group transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-bold text-xs text-slate-900 group-hover:text-[#714B67] transition-colors line-clamp-1">
                      {sc.name}
                    </span>
                    <StatusBadge status={sc.expected_status} size="sm" />
                  </div>
                  <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed font-normal">
                    {sc.description}
                  </p>
                </div>

                <button
                  onClick={() => handleRunScenario(sc)}
                  disabled={isLoading}
                  className="w-full bg-white hover:bg-[#714B67] hover:text-white border border-slate-200 text-slate-700 text-xs font-bold py-1.5 px-3 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 shadow-xs"
                >
                  {isLoading ? (
                    <span className="animate-spin rounded-full h-3 w-3 border-2 border-[#714B67] border-t-transparent"></span>
                  ) : (
                    <>
                      <Play className="w-3 h-3 fill-current" />
                      <span>Run Test Inspection</span>
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Inspections Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h3 className="text-sm font-extrabold text-slate-900">Recent Inbound Inspections</h3>
          <Link href="/history" className="text-xs text-[#714B67] hover:underline flex items-center gap-1 font-bold">
            <span>View Full History</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {inspections.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <ShieldAlert className="w-10 h-10 text-slate-400 mx-auto" />
            <div className="text-sm text-slate-800 font-bold">No inspections yet</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Start your first inbound product inspection or click any scenario above to execute the agent pipeline.
            </p>
            <Link
              href="/inspect"
              className="inline-flex items-center gap-2 btn-indigo text-white font-bold px-4 py-2 rounded-xl text-xs transition-colors"
            >
              Start First Inspection
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="p-3.5 font-bold">Inspection ID</th>
                  <th className="p-3.5 font-bold">Product</th>
                  <th className="p-3.5 font-bold">Work Order</th>
                  <th className="p-3.5 font-bold">Date / Time</th>
                  <th className="p-3.5 font-bold">Status</th>
                  <th className="p-3.5 font-bold">Engine Mode</th>
                  <th className="p-3.5 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {inspections.slice(0, 8).map((ins) => (
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
                        View Results →
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
