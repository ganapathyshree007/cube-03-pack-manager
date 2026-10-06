"use client";
import React, { useState } from "react";
import {
  Receipt,
  Truck,
  ShoppingCart,
  Box,
  CheckCircle,
  PackageCheck,
  RotateCcw,
  Layers,
  Info,
  X,
  ExternalLink,
} from "lucide-react";

export default function EvidenceGraph({ graphData }) {
  const [activeNode, setActiveNode] = useState(null);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="p-12 text-center bg-slate-900/30 rounded-2xl border border-slate-800/50 text-slate-500 text-xs">
        No graph relationships mapped for this charge.
      </div>
    );
  }

  const { nodes, edges } = graphData;

  // Separate nodes by hierarchy
  const chargeNode = nodes.find((n) => n.type === "charge");
  const unitNode = nodes.find((n) => n.type === "unit");
  const shipmentNode = nodes.find((n) => n.type === "shipment");
  const orderNode = nodes.find((n) => n.type === "order");
  const skuNode = nodes.find((n) => n.type === "sku");
  const evidenceNodes = nodes.filter((n) => n.type === "evidence");

  const getNodeIcon = (type, category) => {
    if (type === "charge") return <Receipt className="w-4 h-4 text-rose-400" />;
    if (type === "unit") return <Box className="w-4 h-4 text-amber-400" />;
    if (type === "shipment") return <Truck className="w-4 h-4 text-sky-400" />;
    if (type === "order") return <ShoppingCart className="w-4 h-4 text-indigo-400" />;
    if (type === "sku") return <Box className="w-4 h-4 text-emerald-400" />;
    if (category?.includes("PREP")) return <CheckCircle className="w-4 h-4 text-emerald-400" />;
    if (category?.includes("RECEIV")) return <PackageCheck className="w-4 h-4 text-sky-400" />;
    if (category?.includes("PACK")) return <Layers className="w-4 h-4 text-indigo-400" />;
    if (category?.includes("RETURN")) return <RotateCcw className="w-4 h-4 text-purple-400" />;
    return <Info className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="space-y-4">
      <div className="p-6 rounded-2xl glass-surface-strong border border-slate-800/60 shadow-card">
        <div className="text-xs font-semibold text-slate-200 mb-4 flex items-center justify-between border-b border-slate-800/60 pb-3">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Multi-Hop Traversal Graph</span>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-950/60 px-2.5 py-1 rounded-lg border border-slate-800/60">
            {nodes.length} Nodes &bull; {edges.length} Relational Edges
          </span>
        </div>

        {/* Visual Graph Hierarchy */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 py-4 px-2">
          {/* Column 1: Financial Charge */}
          {chargeNode && (
            <div className="flex flex-col items-center">
              <div
                onClick={() => setActiveNode(chargeNode)}
                className={`w-48 p-3.5 rounded-2xl border cursor-pointer transition-all duration-200 text-center shadow-card ${
                  activeNode?.id === chargeNode.id
                    ? "bg-rose-950/40 border-rose-500 ring-2 ring-rose-500/20 shadow-glow"
                    : "bg-slate-900/80 border-rose-500/30 hover:border-rose-400/60"
                }`}
              >
                <div className="flex items-center justify-center space-x-2 mb-1.5">
                  <div className="p-1 rounded-lg bg-rose-500/10">{getNodeIcon("charge")}</div>
                  <span className="font-bold text-xs text-rose-300 font-mono">{chargeNode.label}</span>
                </div>
                <div className="text-[11px] text-slate-200 font-semibold">{chargeNode.details}</div>
                <div className="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-wider">Origin Deduction</div>
              </div>
            </div>
          )}

          {/* Directed Connector Arrow */}
          <div className="hidden md:flex flex-col items-center text-slate-500">
            <span className="text-[10px] font-mono mb-1 text-slate-400">hops to</span>
            <div className="w-14 h-0.5 bg-slate-700/80 relative">
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-y-4 border-y-transparent border-l-4 border-l-slate-400" />
            </div>
          </div>

          {/* Column 2: Physical Unit / Shipment Master Nodes */}
          <div className="flex flex-col space-y-3">
            {unitNode && (
              <div
                onClick={() => setActiveNode(unitNode)}
                className={`w-48 p-3 rounded-xl border cursor-pointer transition-all duration-200 text-center shadow-card ${
                  activeNode?.id === unitNode.id
                    ? "bg-amber-950/40 border-amber-500 ring-2 ring-amber-500/20 shadow-glow"
                    : "bg-slate-900/80 border-amber-500/30 hover:border-amber-400/60"
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <div className="p-1 rounded-lg bg-amber-500/10">{getNodeIcon("unit")}</div>
                  <span className="font-semibold text-xs text-amber-300 font-mono">{unitNode.label}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 font-mono">{unitNode.details}</div>
              </div>
            )}

            {shipmentNode && (
              <div
                onClick={() => setActiveNode(shipmentNode)}
                className={`w-48 p-3 rounded-xl border cursor-pointer transition-all duration-200 text-center shadow-card ${
                  activeNode?.id === shipmentNode.id
                    ? "bg-sky-950/40 border-sky-500 ring-2 ring-sky-500/20 shadow-glow"
                    : "bg-slate-900/80 border-sky-500/30 hover:border-sky-400/60"
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <div className="p-1 rounded-lg bg-sky-500/10">{getNodeIcon("shipment")}</div>
                  <span className="font-semibold text-xs text-sky-300 font-mono">{shipmentNode.label}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 font-mono">{shipmentNode.details}</div>
              </div>
            )}

            {orderNode && (
              <div
                onClick={() => setActiveNode(orderNode)}
                className={`w-48 p-3 rounded-xl border cursor-pointer transition-all duration-200 text-center shadow-card ${
                  activeNode?.id === orderNode.id
                    ? "bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500/20 shadow-glow"
                    : "bg-slate-900/80 border-indigo-500/30 hover:border-indigo-400/60"
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <div className="p-1 rounded-lg bg-indigo-500/10">{getNodeIcon("order")}</div>
                  <span className="font-semibold text-xs text-indigo-300 font-mono">{orderNode.label}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 font-mono">{orderNode.details}</div>
              </div>
            )}
          </div>

          {/* Directed Connector Arrow */}
          <div className="hidden md:flex flex-col items-center text-slate-500">
            <span className="text-[10px] font-mono mb-1 text-slate-400">proves via</span>
            <div className="w-14 h-0.5 bg-slate-700/80 relative">
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-y-4 border-y-transparent border-l-4 border-l-slate-400" />
            </div>
          </div>

          {/* Column 3: Operational Evidence Leaves */}
          <div className="flex flex-col space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {evidenceNodes.length === 0 ? (
              <div className="text-[11px] text-slate-500 italic p-4 border border-slate-800 rounded-xl bg-slate-900/40 text-center w-60">
                No upstream records
              </div>
            ) : (
              evidenceNodes.map((ev) => (
                <div
                  key={ev.id}
                  onClick={() => setActiveNode(ev)}
                  className={`w-60 p-3 rounded-xl border cursor-pointer transition-all duration-200 text-left shadow-card ${
                    activeNode?.id === ev.id
                      ? "bg-emerald-950/40 border-emerald-400 ring-2 ring-emerald-500/20 shadow-glow"
                      : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="p-1 rounded-md bg-slate-800">{getNodeIcon("evidence", ev.category)}</div>
                      <span className="font-bold text-[11px] text-slate-200 truncate font-mono">{ev.label}</span>
                    </div>
                    <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/40">
                      {ev.finding}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-1 mt-1.5">{ev.details}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Selected Node Inspector Drawer */}
      {activeNode && (
        <div className="p-5 rounded-2xl glass-surface-strong border border-slate-750 shadow-card animate-scale-in">
          <div className="flex justify-between items-start mb-3 border-b border-slate-800/60 pb-3">
            <div>
              <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider font-semibold bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                {activeNode.category || activeNode.type}
              </span>
              <h4 className="text-sm font-bold text-slate-100 font-mono mt-1.5">{activeNode.label}</h4>
            </div>
            <button
              onClick={() => setActiveNode(null)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{activeNode.details}</p>
          {activeNode.timestamp && (
            <div className="text-[11px] font-mono text-slate-400 mt-2.5 flex items-center space-x-1.5">
              <span className="text-slate-500">Captured:</span>
              <span className="text-slate-300">{activeNode.timestamp}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
