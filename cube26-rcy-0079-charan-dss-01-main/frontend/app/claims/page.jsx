"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../components/Navbar";
import { useWorkspace } from "../../context/WorkspaceContext";
import { api } from "../../lib/api";
import { FileCheck2, Download, Copy, Check, ExternalLink } from "lucide-react";
import ClaimPackageModal from "../../components/ClaimPackageModal";
import { TableSkeletonRows } from "../../components/LoadingSkeleton";

export default function ClaimsPage() {
  const { currentCompany } = useWorkspace();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [claimModalOpen, setClaimModalOpen] = useState(false);

  const loadClaims = async () => {
    try {
      setLoading(true);
      const data = await api.getClaims(currentCompany);
      setClaims(data);
    } catch (err) {
      console.error("Failed to load claims:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClaims();
  }, [currentCompany]);

  const handleOpenClaim = (c) => {
    setSelectedClaim(c);
    setClaimModalOpen(true);
  };

  const handleStatusChange = async (claimId, newStatus) => {
    try {
      await api.updateClaimStatus(claimId, newStatus, currentCompany);
      loadClaims();
    } catch (err) {
      alert(`Failed to update claim status: ${err.message}`);
    }
  };

  const totalClaimAmount = claims.reduce((acc, curr) => acc + (curr.amount || 0), 0);

  const getStatusBadge = (claim) => {
    const s = claim.status?.toUpperCase() || "DRAFT";
    let colorClass = "bg-amber-500/15 text-amber-400 border-amber-500/30";
    if (s === "SUBMITTED") colorClass = "bg-sky-500/15 text-sky-400 border-sky-500/30";
    if (s === "PAID" || s === "RECOVERED") colorClass = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    if (s === "REJECTED") colorClass = "bg-rose-500/15 text-rose-400 border-rose-500/30";

    return (
      <select
        value={s}
        onChange={(e) => handleStatusChange(claim.claim_id, e.target.value)}
        className={`px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase border cursor-pointer focus:outline-none transition-all duration-200 ${colorClass} bg-slate-900/80`}
      >
        <option value="DRAFT" className="bg-slate-900 text-amber-400">DRAFT (Unfiled)</option>
        <option value="SUBMITTED" className="bg-slate-900 text-sky-400">SUBMITTED (In Review)</option>
        <option value="PAID" className="bg-slate-900 text-emerald-400">PAID / RECOVERED</option>
        <option value="REJECTED" className="bg-slate-900 text-rose-400">REJECTED</option>
      </select>
    );
  };

  return (
    <div className="flex-1 flex flex-col">
      <Navbar onRefresh={loadClaims} />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">Claims & Audit Dossiers</h1>
            <p className="text-sm text-slate-500 mt-1.5">
              Frozen claim packages with immutable physical proof citations. Change status to track recovery progress.
            </p>
          </div>

          <div className="glass-surface-strong p-4 rounded-2xl flex items-center space-x-4 shadow-card">
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Total Pipeline Value</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 tabular-nums">
                {loading ? (
                  <div className="h-8 w-28 bg-slate-800/60 rounded-md my-0.5" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
                ) : (
                  `$${totalClaimAmount.toFixed(2)} USD`
                )}
              </div>
            </div>
            <div className="h-8 w-px bg-slate-800/60" />
            <div className="text-xs text-slate-400">
              {loading ? (
                <div className="h-4 w-24 bg-slate-800/60 rounded-md" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
              ) : (
                <>
                  <span className="font-bold text-slate-100">{claims.length}</span> claim packages
                </>
              )}
            </div>
          </div>
        </div>

        {/* Claims Table */}
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/50 overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/40 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-800/50">
                <tr>
                  <th className="py-3 px-4">Claim ID</th>
                  <th className="py-3 px-4">Deduction Charge</th>
                  <th className="py-3 px-4 text-right">Recovery Amount</th>
                  <th className="py-3 px-4">Filing Status</th>
                  <th className="py-3 px-4">Created Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-300">
                {loading ? (
                  <TableSkeletonRows rows={5} cols={6} />
                ) : claims.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-16 text-center text-slate-500">
                      No claims generated for this company workspace yet. Visit Recovery Opportunities to generate claims.
                    </td>
                  </tr>
                ) : (
                  claims.map((c) => (
                    <tr key={c.id} className="table-row-hover">
                      <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                        {c.claim_id}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-200">
                        {c.charge_id}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-slate-100 tabular-nums">
                        ${c.amount.toFixed(2)} {c.currency}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(c)}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {c.created_at ? new Date(c.created_at).toLocaleDateString() : "Today"}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleOpenClaim(c)}
                          className="btn-secondary"
                        >
                          <FileCheck2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>View Dossier</span>
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
          claim={selectedClaim}
          onStatusChange={loadClaims}
        />
      </main>
    </div>
  );
}
