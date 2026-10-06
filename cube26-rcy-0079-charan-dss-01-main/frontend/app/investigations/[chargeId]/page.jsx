"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../../components/Navbar";
import { useWorkspace } from "../../../context/WorkspaceContext";
import { api } from "../../../lib/api";
import Link from "next/link";
import {
  ArrowLeft,
  Receipt,
  FileCheck2,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  Layers,
  Clock,
  Network,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import EvidenceTimeline from "../../../components/EvidenceTimeline";
import EvidenceGraph from "../../../components/EvidenceGraph";
import WhyNotClaimModal from "../../../components/WhyNotClaimModal";
import ClaimPackageModal from "../../../components/ClaimPackageModal";

export default function InvestigationDetailPage({ params }) {
  const { chargeId } = params;
  const { currentCompany } = useWorkspace();
  const [charge, setCharge] = useState(null);
  const [investigation, setInvestigation] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("timeline"); // "timeline" or "graph"

  // Modals
  const [whyModalOpen, setWhyModalOpen] = useState(false);
  const [claimModalOpen, setClaimModalOpen] = useState(false);
  const [activeClaim, setActiveClaim] = useState(null);
  const [generatingClaim, setGeneratingClaim] = useState(false);

  const loadInvestigation = async () => {
    try {
      setLoading(true);
      const [cData, invData, gData] = await Promise.all([
        api.getChargeDetail(chargeId, currentCompany),
        api.getInvestigation(chargeId, currentCompany),
        api.getEvidenceGraph(chargeId, currentCompany),
      ]);
      setCharge(cData);
      setInvestigation(invData);
      setGraphData(gData);

      if (cData?.status === "CLAIMED") {
        try {
          const claims = await api.getClaims(currentCompany);
          const found = claims.find((cl) => cl.charge_id === chargeId);
          if (found) setActiveClaim(found);
        } catch (e) {
          console.error("Failed to preload existing claim:", e);
        }
      }
    } catch (err) {
      console.error("Failed to load investigation:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvestigation();
  }, [chargeId, currentCompany]);

  const handleGenerateClaim = async () => {
    try {
      setGeneratingClaim(true);
      const claim = await api.createClaim(currentCompany, chargeId);
      setActiveClaim(claim);
      setClaimModalOpen(true);
      // Reload charge to reflect claimed status
      loadInvestigation();
    } catch (err) {
      alert(`Claim generation failed: ${err.message}`);
    } finally {
      setGeneratingClaim(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
          {/* Breadcrumb Skeleton */}
          <div className="flex items-center space-x-2">
            <div className="h-4 w-28 bg-slate-800/60 rounded-md" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
            <div className="h-4 w-4 bg-slate-800/60 rounded-md" />
            <div className="h-4 w-24 bg-slate-800/60 rounded-md" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
          </div>

          {/* Hero Card Skeleton */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/50 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="h-6 w-24 bg-slate-800/60 rounded-full" />
                <div className="h-4 w-32 bg-slate-800/60 rounded-md" />
              </div>
              <div className="h-8 w-64 bg-slate-800/60 rounded-md" />
              <div className="h-4 w-80 bg-slate-800/60 rounded-md" />
            </div>

            <div className="flex items-center gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
              <div className="space-y-2">
                <div className="h-3 w-28 bg-slate-800/60 rounded-md" />
                <div className="h-7 w-32 bg-slate-800/60 rounded-md" />
              </div>
              <div className="h-10 w-36 bg-slate-800/60 rounded-xl" />
            </div>
          </div>

          {/* Metadata Grid Skeleton */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/60 p-4 rounded-2xl border border-slate-800/50">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-16 bg-slate-800/60 rounded-md" />
                <div className="h-5 w-24 bg-slate-800/60 rounded-md" />
              </div>
            ))}
          </div>
        </main>
      </div>
    );
  }

  if (!charge) {
    return (
      <div className="flex-1 flex flex-col">
        <Navbar />
        <div className="p-16 text-center text-slate-500 text-xs">
          Charge {chargeId} not found in this company workspace.
        </div>
      </div>
    );
  }

  // Badging
  const assessment = investigation?.assessment || "UNINVESTIGATED";
  const getBadgeClass = (ass) => {
    if (ass === "CONTRADICTED") return "badge-contradicted";
    if (ass === "SILENT") return "badge-silent";
    if (ass === "UNCERTAIN") return "badge-uncertain";
    if (ass === "SUPPORTED") return "badge-supported";
    return "bg-slate-800 text-slate-300 border border-slate-700";
  };

  return (
    <div className="flex-1 flex flex-col">
      <Navbar onRefresh={loadInvestigation} />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
        {/* Breadcrumb & Navigation */}
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Link
            href="/charges"
            className="hover:text-slate-200 flex items-center space-x-1.5 transition-colors duration-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Charges Explorer</span>
          </Link>
          <ChevronRight className="w-3 h-3 text-slate-600" />
          <span className="text-slate-200 font-mono font-medium">{charge.charge_id}</span>
        </div>

        {/* Hero Card: Assessment, Amount & Claim Action */}
        <div className="p-6 rounded-2xl glass-surface-strong border border-slate-800/60 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${getBadgeClass(assessment)}`}>
                {assessment}
              </span>
              <span className="text-xs text-slate-400 font-mono bg-slate-900/80 px-2 py-0.5 rounded-md border border-slate-800/60">
                {charge.charge_id}
              </span>
              <span className="text-xs text-slate-500">&bull; Posted: {charge.charge_date || "N/A"}</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 capitalize">
              {charge.reason.replace(/_/g, " ")}
            </h1>
            <p className="text-xs text-slate-400">
              Evaluated against Receiving, Prep, Pack, and Returns operational records.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-slate-950/60 p-4 rounded-2xl border border-slate-800/60 shadow-inner">
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Potential Recovery</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 tabular-nums">
                ${investigation?.claim_amount?.toFixed(2) || "0.00"} {charge.currency}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                Fee Documented: ${charge.amount.toFixed(2)}
              </div>
            </div>

            {investigation?.claim_supported ? (
              <button
                onClick={handleGenerateClaim}
                disabled={generatingClaim}
                className="btn-primary whitespace-nowrap"
              >
                <FileCheck2 className="w-4 h-4" />
                <span>
                  {generatingClaim
                    ? "Assembling Dossier..."
                    : charge?.status === "CLAIMED" || activeClaim
                    ? "View Claim Dossier"
                    : "Generate Claim Package"}
                </span>
              </button>
            ) : (
              <button
                onClick={() => setWhyModalOpen(true)}
                className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 font-semibold text-xs border border-amber-500/30 transition-all duration-200"
              >
                <HelpCircle className="w-4 h-4" />
                <span>Why Not Claim?</span>
              </button>
            )}
          </div>
        </div>

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-900/60 p-4 rounded-2xl border border-slate-800/50 shadow-card">
          <div className="p-2">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">Unit ID</span>
            <div className="font-mono text-slate-200 mt-1 font-medium">{charge.unit_id || "Unspecified"}</div>
          </div>
          <div className="p-2">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">FBA Shipment</span>
            <div className="font-mono text-slate-200 mt-1 font-medium">{charge.shipment_id || "N/A"}</div>
          </div>
          <div className="p-2">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">Order ID</span>
            <div className="font-mono text-slate-200 mt-1 font-medium">{charge.order_id || "N/A"}</div>
          </div>
          <div className="p-2">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">Catalog SKU</span>
            <div className="font-mono text-slate-200 mt-1 font-medium">{charge.sku || "N/A"}</div>
          </div>
        </div>

        {/* Agent Reasoning Card */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/50 space-y-2 shadow-card">
          <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400">
            <div className="w-5 h-5 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <span>Forensic Evidence Reasoning</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed pt-1">
            {investigation?.reasoning}
          </p>
          {investigation?.unsupported_reason && (
            <div className="text-[11px] text-amber-400/90 font-mono mt-2 bg-amber-950/30 p-2.5 rounded-lg border border-amber-800/30">
              Refusal Rationale: {investigation.unsupported_reason}
            </div>
          )}
        </div>

        {/* Tab Switcher: Evidence Timeline vs Evidence Graph */}
        <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
          <div className="flex items-center p-1 bg-slate-900/80 border border-slate-800/60 rounded-xl space-x-1">
            <button
              onClick={() => setActiveTab("timeline")}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                activeTab === "timeline"
                  ? "bg-emerald-600 text-white shadow-sm shadow-emerald-950/40"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Operational Evidence Timeline</span>
            </button>
            <button
              onClick={() => setActiveTab("graph")}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                activeTab === "graph"
                  ? "bg-emerald-600 text-white shadow-sm shadow-emerald-950/40"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              <span>Interactive Evidence Graph</span>
            </button>
          </div>
        </div>

        {/* Main Tab Views */}
        {activeTab === "timeline" ? (
          <div className="space-y-6">
            <EvidenceTimeline timeline={investigation?.timeline} />

            {/* Evidence Relevance Table */}
            <div className="rounded-2xl bg-slate-900/60 border border-slate-800/50 overflow-hidden mt-6 shadow-card">
              <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-semibold text-slate-200">
                    Forensic Relevance Breakdown (What Evidence Proves vs Cannot Prove)
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">Automated relevance analysis of each physical checkpoint log.</p>
                </div>
              </div>
              <div className="divide-y divide-slate-800/40 text-xs">
                {investigation?.evidence_items?.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">No operational evidence items found.</div>
                ) : (
                  investigation?.evidence_items?.map((item, idx) => (
                    <div key={idx} className="p-4 space-y-2 table-row-hover">
                      <div className="flex justify-between items-center">
                        <div className="font-mono font-bold text-emerald-400 flex items-center space-x-2">
                          <span>{item.evidence_id}</span>
                          <span className="text-slate-600">&bull;</span>
                          <span className="uppercase text-slate-300 text-[10px] bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/60">
                            {item.source_type}
                          </span>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-semibold bg-slate-800 text-slate-200 border border-slate-700/50 font-mono">
                          Finding: {item.finding}
                        </span>
                      </div>
                      <div className="text-slate-300 text-xs">
                        <span className="font-semibold text-emerald-400">Establishes: </span>
                        {item.establishes}
                      </div>
                      <div className="text-slate-400 text-xs">
                        <span className="font-semibold text-amber-400">Does NOT Establish: </span>
                        {item.does_not_establish}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          <EvidenceGraph graphData={graphData} />
        )}

        {/* Modals */}
        <WhyNotClaimModal
          isOpen={whyModalOpen}
          onClose={() => setWhyModalOpen(false)}
          investigation={investigation}
          charge={charge}
        />

        <ClaimPackageModal
          isOpen={claimModalOpen}
          onClose={() => setClaimModalOpen(false)}
          claim={activeClaim}
        />
      </main>
    </div>
  );
}
