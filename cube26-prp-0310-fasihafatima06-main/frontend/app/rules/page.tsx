"use client";
import React, { useEffect, useState } from "react";
import { FileCheck2, Info, CheckCircle2 } from "lucide-react";
import { fetchRules } from "@/lib/api";
import { Rule } from "@/lib/types";

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);

  useEffect(() => {
    fetchRules().then(setRules).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 max-w-[1500px] mx-auto">
      <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-[#714B67]" />
          Preparation Requirements Schema & Scope Registry
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Detailed rule specifications. Enforces strict boundary between visually verifiable rules and non-verifiable physical properties.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 bg-slate-50">
          <h3 className="text-sm font-extrabold text-slate-900">System Capability Transparency</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="p-3.5 font-bold">Rule Name & ID</th>
                <th className="p-3.5 font-bold">Product ID</th>
                <th className="p-3.5 font-bold">Category</th>
                <th className="p-3.5 font-bold">Visually Verifiable?</th>
                <th className="p-3.5 font-bold">Evaluation Method</th>
                <th className="p-3.5 font-bold">Agent Behavior if Missing / Unverifiable</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans text-xs">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3.5 font-bold text-slate-900">
                    <div>{r.name}</div>
                    <div className="font-mono text-[10px] text-slate-400 font-normal">{r.id}</div>
                  </td>
                  <td className="p-3.5 font-mono text-slate-700 font-semibold">{r.product_id}</td>
                  <td className="p-3.5 uppercase font-mono text-[10px] text-slate-500 font-bold">{r.category}</td>
                  <td className="p-3.5">
                    {r.visually_verifiable ? (
                      <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full font-bold text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        YES (Visual CV / OCR)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full font-bold text-[11px]">
                        <Info className="w-3.5 h-3.5 text-amber-600" />
                        NO (Physical Lab Test)
                      </span>
                    )}
                  </td>
                  <td className="p-3.5 font-mono text-slate-700 font-medium text-[11px]">{r.evaluation_type}</td>
                  <td className="p-3.5 text-slate-600 leading-relaxed max-w-xs text-[11px]">
                    {r.visually_verifiable
                      ? "Evaluates PASS or FAIL based on spatial geometry / OCR evidence. Returns UNCERTAIN if image is blurry, glare-covered, or missing view."
                      : "Returns UNCERTAIN / Out of Scope with requirement for physical lab measurement. Never falsely marked PASS."}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
