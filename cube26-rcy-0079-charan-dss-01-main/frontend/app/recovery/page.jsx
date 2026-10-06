"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../components/Navbar";
import { useWorkspace } from "../../context/WorkspaceContext";
import { api } from "../../lib/api";
import Link from "next/link";
import {
  TrendingUp,
  FileCheck2,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import ClaimPackageModal from "../../components/ClaimPackageModal";
import { TableSkeletonRows } from "../../components/LoadingSkeleton";

export default function RecoveryOpportunitiesPage() {
  const { currentCompany } = useWorkspace();
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeClaim, setActiveClaim] = useState(null);
  const [claimModalOpen, setClaimModalOpen] = useState(false);

  const loadOpportunities = async () => {
    try {
      setLoading(true);
      const data = await api.getRecoveryOpportunities(currentCompany);
      setOpportunities(data);
    } catch (err) {
      console.error("Failed to load recovery opportunities:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [currentCompany]);

  const handleQuickClaim = async (chargeId) => {
    try {
      const claim = await api.createClaim(currentCompany, chargeId);
      setActiveClaim(claim);
      setClaimModalOpen(true);
      loadOpportunities();
    } catch (err) {
      alert(`Claim generation failed: ${err.message}`);
    }
  };

  const totalRecoverable = opportunities.reduce((acc, curr) => acc + (curr.amount || 0), 0);

  return (
    <div className="flex-1 flex flex-col">
      <Navbar onRefresh={loadOpportunities} />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/15 to-emerald-600/5 border border-emerald-500/20 text-emerald-400 shadow-glow">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100">
                Recovery Opportunities
              </h1>
            </div>
            <p className="text-sm text-slate-500 mt-1.5">
              Charges contradicted by upstream prep & receiving logs ready for defensible filing.
            </p>
          </div>

          <div className="bg-emerald-950/15 border border-emerald-800/25 p-4 rounded-2xl flex items-center space-x-4 shadow-card">
            <div>
              <div className="text-[10px] uppercase font-bold text-emerald-400/80 tracking-wider">Total Recoverable Pipeline</div>
              <div className="text-2xl font-bold font-mono text-emerald-300 tabular-nums">
                {loading ? (
                  <div className="h-8 w-28 bg-emerald-950/40 rounded-md my-0.5" style={{ background: 'linear-gradient(90deg, rgba(6,78,59,0.4) 25%, rgba(16,185,129,0.1) 50%, rgba(6,78,59,0.4) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
                ) : (
                  `$${totalRecoverable.toFixed(2)} USD`
                )}
              </div>
            </div>
            <div className="h-8 w-px bg-emerald-800/30" />
            <div className="text-xs text-slate-400">
              {loading ? (
                <div className="h-4 w-28 bg-slate-800/60 rounded-md" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
              ) : (
                <>
                  <span className="font-bold text-emerald-400">{opportunities.length}</span> substantiated claims
                </>
              )}
            </div>
          </div>
        </div>

        {/* Opportunities List */}
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/50 overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/40 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-800/50">
                <tr>
                  <th className="py-3 px-4">Charge ID</th>
                  <th className="py-3 px-4">Unit / Shipment</th>
                  <th className="py-3 px-4">Deduction Reason</th>
                  <th className="py-3 px-4 text-right">Claim Amount</th>
                  <th className="py-3 px-4">Proof Records</th>
                  <th className="py-3 px-4">Defense Rationale</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-300">
                {loading ? (
                  <TableSkeletonRows rows={6} cols={7} />
                ) : opportunities.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center text-slate-500">
                      No recoverable opportunities identified for this company workspace yet.
                    </td>
                  </tr>
                ) : (
                  opportunities.map((opp) => (
                    <tr key={opp.charge_id} className="table-row-hover">
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-100">
                        {opp.charge_id}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-mono text-emerald-400">{opp.unit_id || "N/A"}</div>
                        <div className="text-[10px] text-slate-500">{opp.shipment_id || ""}</div>
                      </td>
                      <td className="py-3.5 px-4 capitalize font-medium text-slate-200">
                        {opp.reason.replace(/_/g, " ")}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-emerald-400 tabular-nums">
                        ${opp.amount.toFixed(2)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-800/50 text-slate-300 font-mono text-[11px] border border-slate-700/40">
                          <span>{opp.evidence_count} attached</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 max-w-xs truncate text-slate-400 text-[11px]">
                        {opp.reasoning}
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        <Link
                          href={`/investigations/${opp.charge_id}`}
                          className="btn-ghost"
                        >
                          <span>Review</span>
                          <ExternalLink className="w-3 h-3 text-slate-400" />
                        </Link>
                        <button
                          onClick={() => handleQuickClaim(opp.charge_id)}
                          className="btn-primary"
                        >
                          <FileCheck2 className="w-3 h-3" />
                          <span>Generate Claim</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <ClaimPackageModal
          isOpen={claimModalOpen}
          onClose={() => setClaimModalOpen(false)}
          claim={activeClaim}
        />
      </main>
    </div>
  );
}
