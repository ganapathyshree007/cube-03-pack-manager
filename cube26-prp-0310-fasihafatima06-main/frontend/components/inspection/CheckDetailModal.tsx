"use client";
import React from "react";
import { X, ShieldCheck, AlertCircle, HelpCircle, Layers } from "lucide-react";
import { CheckResult } from "@/lib/types";
import { StatusBadge } from "@/components/common/StatusBadge";

interface CheckDetailModalProps {
  check: CheckResult | null;
  onClose: () => void;
}

export const CheckDetailModal: React.FC<CheckDetailModalProps> = ({ check, onClose }) => {
  if (!check) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <Layers className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm">{check.name}</h3>
              <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">{check.category}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 text-xs">
          {/* Status & Confidence */}
          <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-200">
            <div>
              <span className="text-slate-500 block text-[11px] mb-1 font-semibold">Check Decision</span>
              <StatusBadge status={check.status} size="md" />
            </div>
            <div className="text-right">
              <span className="text-slate-500 block text-[11px] font-semibold">Model Confidence</span>
              <span className="font-mono text-slate-900 font-bold text-sm">
                {Math.round(check.confidence * 100)}%
              </span>
            </div>
          </div>

          {/* Explanation / Why */}
          <div>
            <h4 className="font-bold text-slate-800 mb-1 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-indigo-600" />
              Inspection Explanation
            </h4>
            <p className="bg-slate-50 p-3 rounded-xl text-slate-800 leading-relaxed border border-slate-200 font-medium">
              {check.reason}
            </p>
          </div>

          {/* Recommended Action */}
          {check.recommended_action && (
            <div>
              <h4 className="font-bold text-amber-700 mb-1 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                Recommended Operator Action
              </h4>
              <p className="bg-amber-50 border border-amber-200 text-amber-900 p-3 rounded-xl font-bold leading-relaxed">
                {check.recommended_action}
              </p>
            </div>
          )}

          {/* Evidence Details */}
          <div>
            <h4 className="font-bold text-slate-800 mb-1">Detected Evidence Features</h4>
            <div className="flex flex-wrap gap-1.5">
              {check.evidence?.detected_features?.map((feat, idx) => (
                <span key={idx} className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md text-[11px] border border-slate-200 font-mono font-semibold">
                  {feat}
                </span>
              )) || <span className="text-slate-400 italic">No spatial features recorded</span>}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="btn-indigo font-bold px-4 py-2 rounded-xl text-xs"
          >
            Close Detail
          </button>
        </div>
      </div>
    </div>
  );
};
