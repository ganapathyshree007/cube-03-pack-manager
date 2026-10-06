"use client";
import React from "react";
import { AlertCircle, CheckCircle2, XCircle, ShieldAlert, X } from "lucide-react";

export default function WhyNotClaimModal({ isOpen, onClose, investigation, charge }) {
  if (!isOpen || !investigation) return null;

  const coverage = investigation.coverage_summary || {};
  const verified = coverage.verified_items || [];
  const missing = coverage.missing_items || [];
  const explanation = coverage.why_not_claim || investigation.reasoning;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="glass-surface-strong border border-slate-750 w-full max-w-lg rounded-2xl shadow-modal p-6 relative space-y-5 animate-scale-in">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800/60 pb-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Why Can't This Charge Be Claimed?</h3>
              <p className="text-xs text-slate-400">Forensic conservative reasoning disclosure</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Verdict Callout */}
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 text-xs text-amber-300">
          <div className="font-semibold text-amber-200 mb-1 flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>System Decision: <strong className="font-mono text-amber-300">{investigation.assessment}</strong> (Potential Recovery: $0.00)</span>
          </div>
          <p className="text-slate-300 leading-relaxed text-xs mt-1.5">{explanation}</p>
        </div>

        {/* Verified vs Missing Audit Checklist */}
        <div className="space-y-3.5">
          <div>
            <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <span>Verified Operational Footprint</span>
            </h4>
            <div className="space-y-1.5 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              {verified.length === 0 ? (
                <div className="text-xs text-slate-500 italic">No operational records identified</div>
              ) : (
                verified.map((v, i) => (
                  <div key={i} className="flex items-start space-x-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                    <span className="text-slate-300 leading-snug">{v}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div>
            <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <span>Missing Proof Required for Defensible Claim</span>
            </h4>
            <div className="space-y-1.5 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              {missing.length === 0 ? (
                <div className="text-xs text-slate-500 italic">No specific missing item logged</div>
              ) : (
                missing.map((m, i) => (
                  <div key={i} className="flex items-start space-x-2 text-xs text-rose-400">
                    <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span className="text-slate-300 leading-snug">{m}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Account Standing Principle */}
        <div className="text-[11px] text-slate-400 border-t border-slate-800/60 pt-3 leading-relaxed bg-slate-900/30 p-3 rounded-lg border border-slate-800/40">
          <span className="font-semibold text-slate-200">Conservative Safety Principle:</span> Marketplace
          channels penalize sellers who submit speculative disputes. Recovery Manager refuses to gamble your channel
          privileges without verifiable, tamper-resistant pre-shipment proof.
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-1">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
}
