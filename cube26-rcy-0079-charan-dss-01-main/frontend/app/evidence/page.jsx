"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../components/Navbar";
import { useWorkspace } from "../../context/WorkspaceContext";
import { api } from "../../lib/api";
import {
  FolderSync,
  PackageCheck,
  CheckCircle,
  Layers,
  RotateCcw,
  Clock,
  Camera,
  Search,
  X,
} from "lucide-react";
import { EvidenceCardSkeleton } from "../../components/LoadingSkeleton";

export default function EvidencePage() {
  const { currentCompany } = useWorkspace();
  const [evidenceList, setEvidenceList] = useState([]);
  const [sourceFilter, setSourceFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);

  const loadEvidence = async () => {
    try {
      setLoading(true);
      const data = await api.getEvidenceList(currentCompany, {
        source_type: sourceFilter !== "ALL" ? sourceFilter.toLowerCase() : undefined,
      });
      setEvidenceList(data);
    } catch (err) {
      console.error("Failed to load evidence:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvidence();
  }, [currentCompany, sourceFilter]);

  const filteredEvidence = evidenceList.filter((e) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      e.evidence_id?.toLowerCase().includes(s) ||
      e.unit_id?.toLowerCase().includes(s) ||
      e.sku?.toLowerCase().includes(s) ||
      e.description?.toLowerCase().includes(s)
    );
  });

  const getSourceBadge = (source) => {
    const styles = {
      receiving: "bg-sky-500/10 text-sky-400 border-sky-500/25",
      prep: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
      pack: "bg-indigo-500/10 text-indigo-400 border-indigo-500/25",
      returns: "bg-purple-500/10 text-purple-400 border-purple-500/25",
    };
    const style = styles[source] || "bg-slate-800/60 text-slate-300 border-slate-700";
    return (
      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${style}`}>
        {source?.toUpperCase() || "OP"}
      </span>
    );
  };

  return (
    <div className="flex-1 flex flex-col">
      <Navbar onRefresh={loadEvidence} />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Operational Evidence Logs
            </h1>
            <p className="text-sm text-slate-500 mt-1.5">
              Immutable physical logs recorded across Receiving, Prep, Pack, and Returns lines.
            </p>
          </div>
          <div className="text-xs text-slate-500">
            {loading ? (
              <div className="h-4 w-28 bg-slate-800/60 rounded-md" style={{ background: 'linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(51,65,85,0.3) 50%, rgba(30,41,59,0.5) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
            ) : (
              <>Total records: <span className="font-semibold text-slate-200">{filteredEvidence.length}</span></>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 glass-surface-strong p-3 rounded-2xl">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by Evidence ID, Unit ID, SKU, or Description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950/50 border border-slate-800/50 rounded-xl text-xs text-slate-200 placeholder-slate-600 input-focus"
            />
          </div>

          <div className="flex items-center space-x-1">
            {["ALL", "RECEIVING", "PREP", "PACK", "RETURNS"].map((f) => (
              <button
                key={f}
                onClick={() => setSourceFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap ${
                  sourceFilter === f
                    ? "bg-emerald-600 text-white font-semibold shadow-sm shadow-emerald-950/30"
                    : "text-slate-500 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Evidence Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <EvidenceCardSkeleton key={i} />
            ))}
          </div>
        ) : filteredEvidence.length === 0 ? (
          <div className="py-20 text-center text-xs text-slate-500 border border-slate-800/50 rounded-2xl bg-slate-900/30">
            No operational evidence logs match the current filters.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEvidence.map((ev) => (
              <div
                key={ev.id}
                onClick={() => setSelectedRecord(ev)}
                className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/50 hover:border-slate-700/60 cursor-pointer transition-all duration-200 shadow-card card-hover space-y-3"
              >
                <div className="flex justify-between items-start">
                  <div>
                    {getSourceBadge(ev.source_type)}
                    <h4 className="font-mono font-bold text-xs text-slate-200 mt-2">{ev.evidence_id}</h4>
                  </div>
                  <span className="font-mono font-bold text-[11px] px-2 py-0.5 rounded-md bg-slate-800/60 text-emerald-400 border border-slate-700/50">
                    {ev.finding}
                  </span>
                </div>

                <div className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {ev.description}
                </div>

                <div className="pt-2 border-t border-slate-800/40 flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span className="text-slate-400">Unit: {ev.unit_id || "N/A"}</span>
                  <span>{ev.timestamp || "Pre-shipment"}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Detail Modal */}
        {selectedRecord && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
            <div className="glass-surface-strong w-full max-w-lg rounded-2xl shadow-modal p-6 relative space-y-4 animate-scale-in">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] uppercase font-bold text-emerald-400 font-mono">
                    {selectedRecord.source_type} EVIDENCE
                  </span>
                  <h3 className="text-base font-bold text-slate-100 font-mono mt-0.5">
                    {selectedRecord.evidence_id}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800/60 transition-all duration-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800/50 text-xs text-slate-300 space-y-1">
                <div className="font-semibold text-slate-200">Operational Log Description:</div>
                <p className="leading-relaxed">{selectedRecord.description}</p>
              </div>

              {/* Raw JSON Payload */}
              <div>
                <span className="text-[10px] font-semibold uppercase text-slate-500">Raw Stored Metadata</span>
                <pre className="p-3 rounded-xl bg-slate-950/60 text-[10px] font-mono text-slate-300 max-h-48 overflow-y-auto mt-1 border border-slate-800/50">
                  {JSON.stringify(selectedRecord.raw_payload || {}, null, 2)}
                </pre>
              </div>

              {selectedRecord.photo_refs && (
                <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
                  <Camera className="w-3.5 h-3.5 text-slate-500" />
                  <span>Photo attachments: {selectedRecord.photo_refs}</span>
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="btn-secondary"
                >
                  <span>Close</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
