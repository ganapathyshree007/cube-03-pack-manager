"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Scale,
  ShieldCheck,
  TrendingUp,
  FileCheck2,
  Receipt,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Activity,
  Layers,
  Database,
  Search,
  Sparkles,
  ChevronRight,
  ExternalLink,
  Shield,
  Clock,
  PackageCheck,
  RotateCcw,
  Check,
  FileText,
  AlertTriangle,
  Lock,
  Boxes,
} from "lucide-react";

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [activeVerdict, setActiveVerdict] = useState("CONTRADICTED");
  const [activeStep, setActiveStep] = useState(1);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 40) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="relative min-h-screen bg-[#080c15] text-slate-100 selection:bg-emerald-500/20 selection:text-emerald-300">
      {/* ============================================================ */}
      {/* 1. TOP STICKY LANDING NAVBAR                                 */}
      {/* ============================================================ */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 select-none ${
          scrolled
            ? "h-16 bg-[#080c15]/90 backdrop-blur-2xl border-b border-slate-800/80 shadow-2xl shadow-black/50"
            : "h-20 bg-transparent border-b border-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto h-full px-6 lg:px-8 flex items-center justify-between">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/25 via-emerald-600/10 to-transparent border border-emerald-500/35 flex items-center justify-center text-emerald-400 shadow-glow shrink-0 group-hover:scale-105 transition-transform duration-200">
              <Scale className="w-4 h-4 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-slate-100 tracking-tight text-sm font-sans">
                  RCY RECOVERY
                </span>
                <span className="text-[10px] bg-emerald-500/15 text-emerald-300 font-mono px-1.5 py-0.5 rounded-md font-semibold border border-emerald-500/25">
                  v1.0
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-medium">Evidence Operations Center</p>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2 text-xs font-medium text-slate-300">
            <a
              href="#problem"
              className="px-3 py-1.5 rounded-lg hover:text-slate-100 hover:bg-slate-800/50 transition-colors"
            >
              The Problem
            </a>
            <a
              href="#solution"
              className="px-3 py-1.5 rounded-lg hover:text-slate-100 hover:bg-slate-800/50 transition-colors"
            >
              Solution
            </a>
            <a
              href="#verdicts"
              className="px-3 py-1.5 rounded-lg hover:text-slate-100 hover:bg-slate-800/50 transition-colors"
            >
              Verdict Engine
            </a>
            <a
              href="#workflow"
              className="px-3 py-1.5 rounded-lg hover:text-slate-100 hover:bg-slate-800/50 transition-colors"
            >
              How It Works
            </a>
            <a
              href="#showcase"
              className="px-3 py-1.5 rounded-lg hover:text-slate-100 hover:bg-slate-800/50 transition-colors"
            >
              Product
            </a>
            <a
              href="#principles"
              className="px-3 py-1.5 rounded-lg hover:text-slate-100 hover:bg-slate-800/50 transition-colors"
            >
              Safety Principles
            </a>
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-3">
            <Link
              href="/charges"
              className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-slate-300 hover:text-slate-100 transition-colors"
            >
              <span>Explore Data</span>
            </Link>
            <Link
              href="/dashboard"
              className="btn-primary group"
            >
              <span>Open Recovery Center</span>
              <ArrowRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ============================================================ */}
      {/* 2. HERO SECTION                                              */}
      {/* ============================================================ */}
      <section className="relative pt-32 pb-24 md:pt-40 md:pb-32 overflow-hidden">
        {/* Ambient atmospheric lighting */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-gradient-to-tr from-emerald-500/10 via-teal-500/5 to-transparent rounded-full blur-3xl pointer-events-none -z-10" />
        <div className="absolute top-1/3 left-1/3 w-[400px] h-[300px] bg-indigo-500/5 rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            {/* Live Eyebrow Badge */}
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-xs font-mono text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="tracking-wide uppercase font-semibold text-[11px]">
                AI-POWERED EVIDENCE &rarr; RECOVERY ENGINE
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-100 font-sans leading-[1.12]">
              Turn financial deductions into{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200">
                defensible recovery.
              </span>
            </h1>

            {/* Supporting Copy */}
            <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
              RCY Recovery analyzes marketplace deduction fees, connects them with physical checkpoint
              records across receiving, prep, pack, and returns lines, and evaluates whether charges are
              supported, contradicted, or silent.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
              <Link
                href="/dashboard"
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-xl shadow-emerald-950/50 flex items-center justify-center space-x-2 transition-all duration-200 group"
              >
                <span>Open Recovery Center</span>
                <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
              <a
                href="#workflow"
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 font-medium text-sm border border-slate-750 flex items-center justify-center space-x-2 transition-all duration-200"
              >
                <span>See How It Works</span>
              </a>
            </div>
          </div>

          {/* ============================================================ */}
          {/* HERO VISUALIZATION: FLOATING FORENSIC SYSTEM MATCH           */}
          {/* ============================================================ */}
          <div className="mt-16 md:mt-20 max-w-4xl mx-auto">
            <div className="p-3 sm:p-4 rounded-3xl bg-slate-950/60 border border-slate-800/80 shadow-2xl backdrop-blur-xl relative">
              {/* Outer decorative glow */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-emerald-500/10 to-transparent pointer-events-none -z-10" />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* 1. FINANCIAL DEDUCTION CARD */}
                <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800/80 flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pb-2 border-b border-slate-800/60">
                      <span className="uppercase text-rose-400 font-semibold flex items-center space-x-1">
                        <Receipt className="w-3.5 h-3.5" />
                        <span>Channel Deduction</span>
                      </span>
                      <span>Amazon FBA</span>
                    </div>
                    <div className="mt-3">
                      <div className="text-2xl font-bold font-mono text-slate-100">$38.00</div>
                      <div className="text-xs font-semibold text-slate-200 mt-1">Inbound Defect Fee</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">Alleged packaging non-compliance</div>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/60 font-mono text-[11px] space-y-1">
                    <div className="text-slate-400">Charge: <span className="text-slate-200 font-bold">CH-TC07-DUPLICATE</span></div>
                    <div className="text-slate-400">Unit ID: <span className="text-emerald-400">UNIT-TC07</span></div>
                  </div>
                </div>

                {/* 2. MATCHED PHYSICAL EVIDENCE CARD */}
                <div className="p-5 rounded-2xl bg-slate-900/90 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.08)] flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pb-2 border-b border-slate-800/60">
                      <span className="uppercase text-emerald-400 font-semibold flex items-center space-x-1">
                        <PackageCheck className="w-3.5 h-3.5" />
                        <span>Operational Evidence</span>
                      </span>
                      <span>Prep Line</span>
                    </div>
                    <div className="mt-3">
                      <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-emerald-950/80 border border-emerald-800/60 text-emerald-400 font-bold font-mono text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>FINDING: PASS (Compliant)</span>
                      </div>
                      <div className="text-xs font-medium text-slate-300 mt-2.5 leading-relaxed">
                        Polybag present & sealed with suffocation warning. FNSKU label verified scannable.
                      </div>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/60 font-mono text-[11px] space-y-1">
                    <div className="text-slate-400">Evidence ID: <span className="text-slate-200 font-bold">PRP-TC07</span></div>
                    <div className="text-slate-400">Timestamp: <span className="text-slate-300">Pre-shipment custody</span></div>
                  </div>
                </div>

                {/* 3. FORENSIC ASSESSMENT CARD */}
                <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/40 shadow-glow flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pb-2 border-b border-emerald-800/40">
                      <span className="uppercase text-emerald-300 font-semibold flex items-center space-x-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Forensic Assessment</span>
                      </span>
                      <span className="text-emerald-400 font-bold">DEFENSIBLE</span>
                    </div>
                    <div className="mt-3">
                      <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span>CONTRADICTED</span>
                      </span>
                      <div className="mt-3">
                        <div className="text-[10px] uppercase font-bold text-slate-400">Potential Recovery</div>
                        <div className="text-2xl font-bold font-mono text-emerald-300">$38.00 USD</div>
                      </div>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950/80 border border-emerald-800/40 font-mono text-[11px] text-emerald-300">
                    &bull; Dispute Package Assembled (Dossier Ready)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 3. CORE OPERATIONAL PRINCIPLES STRIP                         */}
      {/* ============================================================ */}
      <section className="py-10 border-y border-slate-800/60 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center lg:text-left">
            <div className="space-y-1">
              <div className="flex items-center justify-center lg:justify-start space-x-2 text-xs font-bold uppercase tracking-wider text-slate-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Evidence-First</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Every recovery claim strictly cites physical warehouse floor logs.
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-center lg:justify-start space-x-2 text-xs font-bold uppercase tracking-wider text-slate-200">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Conservative Decisions</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Missing operational proof strictly yields SILENT ($0.00 recovery).
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-center lg:justify-start space-x-2 text-xs font-bold uppercase tracking-wider text-slate-200">
                <FileCheck2 className="w-4 h-4 text-emerald-400" />
                <span>Deterministic Traceability</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Frozen audit dossiers with formal dispute narrative & JSON packets.
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-center lg:justify-start space-x-2 text-xs font-bold uppercase tracking-wider text-slate-200">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span>Multi-Tenant RLS</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Row-level database security ensuring strict merchant isolation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 4. THE PROBLEM: FRAGMENTED OPERATIONAL EVIDENCE              */}
      {/* ============================================================ */}
      <section id="problem" className="py-24 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="max-w-3xl mb-12">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
            The Fundamental Challenge
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight mt-2 font-sans">
            Financial deductions rarely tell the whole story.
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Marketplace penalty deductions (inbound defect fees, weight tier adjustments, lost inventory, returns)
            are assessed weeks after dispatch. The proof required to dispute them lives in disconnected operational silos.
          </p>
        </div>

        {/* Visual Fragmented Evidence Diagram */}
        <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800/80 shadow-card">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
            {/* Silo 1 */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
                <PackageCheck className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-200 text-sm">Receiving Dock</h3>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Inbound carton scans, gross pallet weights, and carrier custody transfer timestamps.
              </p>
              <div className="pt-2 font-mono text-[10px] text-sky-400">Weights &bull; Box Counts</div>
            </div>

            {/* Silo 2 */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-200 text-sm">Prep Station</h3>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Polybagging records, bubble wrap verification, barcode cover label inspections.
              </p>
              <div className="pt-2 font-mono text-[10px] text-emerald-400">Packaging Compliance</div>
            </div>

            {/* Silo 3 */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-200 text-sm">Pack Bench</h3>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Shipment carton packing verification, item dimensions, and pre-courier sealing.
              </p>
              <div className="pt-2 font-mono text-[10px] text-indigo-400">Volumetric Tiers</div>
            </div>

            {/* Silo 4 */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <RotateCcw className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-200 text-sm">Returns Line</h3>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                LPN reverse logistics inspections, customer return verification, and restock logs.
              </p>
              <div className="pt-2 font-mono text-[10px] text-purple-400">Item Restock & Proof</div>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                Without automated multi-hop evidence retrieval, merchants forfeit <strong>15%–30% of margin</strong> to uncontested channel deductions.
              </span>
            </div>
            <Link
              href="/dashboard"
              className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center space-x-1 shrink-0"
            >
              <span>See How Recovery Solves This</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 5. THE SOLUTION: MEET RECOVERY MANAGER                       */}
      {/* ============================================================ */}
      <section id="solution" className="py-24 border-t border-slate-800/60 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="max-w-3xl mb-16">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
              Autonomous Financial Defense
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight mt-2 font-sans">
              Meet Recovery Manager.
            </h2>
            <p className="text-sm text-slate-400 mt-3 leading-relaxed">
              Recovery Manager connects individual fee line items against operational evidence generated across
              your warehouse pipeline. It resolves tracking, evaluates defensibility, and generates audit packages.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="command-card p-6 rounded-2xl space-y-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-100">Universal Report Ingestion</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ingest channel deduction statements and physical floor logs across CSV, XLSX, PDF, and JSON formats.
                Ledger deduplication prevents double-claiming.
              </p>
              <div className="pt-2 text-[11px] font-mono text-emerald-400 font-semibold">
                &bull; Automatic Schema Pre-Validation
              </div>
            </div>

            <div className="command-card p-6 rounded-2xl space-y-4">
              <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-100">Multi-Hop Evidence Graph</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Traverses relational hops from Charge ID &rarr; Physical Unit &rarr; Shipment &rarr; Order &rarr; Operational Logs
                to uncover connected proof even when channel identifiers vary.
              </p>
              <div className="pt-2 text-[11px] font-mono text-teal-400 font-semibold">
                &bull; 3-Tier Multi-Hop Graph Traversal
              </div>
            </div>

            <div className="command-card p-6 rounded-2xl space-y-4">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-100">Frozen Dispute Dossiers</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Assembles audit-grade commercial packages with formal dispute narratives, fact comparison tables,
                and immutable physical proof citations ready for Seller Central or 3PL submission.
              </p>
              <div className="pt-2 text-[11px] font-mono text-indigo-400 font-semibold">
                &bull; One-Click HTML Dossier & JSON Export
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 6. THREE-STATE VERDICT ENGINE                                */}
      {/* ============================================================ */}
      <section id="verdicts" className="py-24 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="max-w-3xl mb-14">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
            Forensic Decision Matrix
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight mt-2 font-sans">
            The Three-State Verdict Engine
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Marketplaces penalize aggressive, ungrounded disputes. Recovery Manager uses a deterministic three-verdict
            matrix that only generates claims when evidence definitively contradicts the charge.
          </p>
        </div>

        {/* Verdict Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* VERDICT 1: CONTRADICTED */}
          <div
            onClick={() => setActiveVerdict("CONTRADICTED")}
            className={`command-card p-6 rounded-2xl cursor-pointer transition-all duration-300 relative ${
              activeVerdict === "CONTRADICTED"
                ? "border-emerald-500/60 ring-2 ring-emerald-500/20 shadow-glow"
                : "hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>CONTRADICTED</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">100% RECOVERABLE</span>
            </div>

            <h3 className="text-base font-bold text-slate-100">Physical Evidence Refutes Fee</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Upstream scanner and inspection logs definitively prove compliance prior to custody transfer.
              A complete dispute claim package is assembled with attached citations.
            </p>

            <div className="mt-5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono space-y-1">
              <div className="text-slate-400">Action: <span className="text-emerald-400 font-bold">Generate Claim Dossier</span></div>
              <div className="text-slate-400">Potential: <span className="text-slate-200">100% Reimbursement Request</span></div>
            </div>
          </div>

          {/* VERDICT 2: SUPPORTED */}
          <div
            onClick={() => setActiveVerdict("SUPPORTED")}
            className={`command-card p-6 rounded-2xl cursor-pointer transition-all duration-300 relative ${
              activeVerdict === "SUPPORTED"
                ? "border-rose-500/60 ring-2 ring-rose-500/20 shadow-[0_0_20px_rgba(244,63,94,0.15)]"
                : "hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                <span>SUPPORTED</span>
              </span>
              <span className="text-[10px] font-mono text-rose-400 font-bold uppercase">VALID FEE</span>
            </div>

            <h3 className="text-base font-bold text-slate-100">Warehouse Logs Confirm Deviation</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Inspection records confirm that the defect occurred on the merchant's floor (e.g., missing polybag label).
              Recovery Manager prevents filing to protect account health.
            </p>

            <div className="mt-5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono space-y-1">
              <div className="text-slate-400">Action: <span className="text-rose-400 font-bold">Do Not Dispute</span></div>
              <div className="text-slate-400">Safety: <span className="text-slate-200">Protects Account Health</span></div>
            </div>
          </div>

          {/* VERDICT 3: SILENT (SPECIAL DIFFERENTIATOR) */}
          <div
            onClick={() => setActiveVerdict("SILENT")}
            className={`command-card p-6 rounded-2xl cursor-pointer transition-all duration-300 relative ${
              activeVerdict === "SILENT"
                ? "border-amber-500/60 ring-2 ring-amber-500/20 shadow-[0_0_20px_rgba(245,158,11,0.15)]"
                : "hover:border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                <span>SILENT</span>
              </span>
              <span className="text-[10px] font-mono text-amber-400 font-bold uppercase">ZERO SPECULATION</span>
            </div>

            <h3 className="text-base font-bold text-slate-100">Insufficient Physical Proof</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              No conclusive pre-shipment record exists. Rather than hallucinate or submit a speculative dispute,
              Recovery Manager logs SILENT with $0.00 recovery.
            </p>

            <div className="mt-5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono space-y-1">
              <div className="text-slate-400">Action: <span className="text-amber-400 font-bold">Conservative Skip</span></div>
              <div className="text-slate-400">Disclosure: <span className="text-slate-200">Full "Why Not Claim" Audit</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 7. HOW IT WORKS: 5-STEP FORENSIC PIPELINE                    */}
      {/* ============================================================ */}
      <section id="workflow" className="py-24 border-t border-slate-800/60 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="max-w-3xl mb-16">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
              End-to-End Workflow
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight mt-2 font-sans">
              From Raw Deduction to Audit-Ready Dossier
            </h2>
            <p className="text-sm text-slate-400 mt-3 leading-relaxed">
              Five autonomous operational phases turn fragmented data into defensible capital recovery.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Step 1 */}
            <div className="command-card p-5 rounded-2xl space-y-3">
              <div className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded w-fit border border-emerald-800/50">
                PHASE 01
              </div>
              <h3 className="text-sm font-bold text-slate-100">Ingest</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Upload marketplace fee reports, 3PL invoices, and floor custody logs across CSV, XLSX, PDF, or JSON.
              </p>
            </div>

            {/* Step 2 */}
            <div className="command-card p-5 rounded-2xl space-y-3">
              <div className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded w-fit border border-emerald-800/50">
                PHASE 02
              </div>
              <h3 className="text-sm font-bold text-slate-100">Identify</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Deterministic entity resolution extracts unit IDs, shipment IDs, FNSKUs, and order identifiers.
              </p>
            </div>

            {/* Step 3 */}
            <div className="command-card p-5 rounded-2xl space-y-3">
              <div className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded w-fit border border-emerald-800/50">
                PHASE 03
              </div>
              <h3 className="text-sm font-bold text-slate-100">Retrieve</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Multi-hop query locates corresponding receiving custody, prep compliance, pack bench, and return records.
              </p>
            </div>

            {/* Step 4 */}
            <div className="command-card p-5 rounded-2xl space-y-3">
              <div className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded w-fit border border-emerald-800/50">
                PHASE 04
              </div>
              <h3 className="text-sm font-bold text-slate-100">Assess</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Deterministic compliance rules + conservative evaluation synthesize evidence into an immutable verdict.
              </p>
            </div>

            {/* Step 5 */}
            <div className="command-card p-5 rounded-2xl space-y-3">
              <div className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded w-fit border border-emerald-800/50">
                PHASE 05
              </div>
              <h3 className="text-sm font-bold text-slate-100">Recover</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Frozen claim dossier generated with formal narrative letter, fact comparison table, and JSON metadata.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 8. PRODUCT SHOWCASE: RECOVERY OPERATIONS CENTER PREVIEW      */}
      {/* ============================================================ */}
      <section id="showcase" className="py-24 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="max-w-3xl mb-14">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
            Real-Time Operations Command
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight mt-2 font-sans">
            Built for High-Velocity Evidence Operations
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            The actual Recovery Operations Center dashboard in action — financial KPIs, evidence verdict distribution,
            category analytics, and row-level investigation explorer.
          </p>
        </div>

        {/* Browser Mockup Window */}
        <div className="rounded-3xl border border-slate-800/90 bg-slate-950/80 shadow-2xl overflow-hidden backdrop-blur-2xl">
          {/* Browser Chrome Bar */}
          <div className="h-11 px-4 bg-slate-900/90 border-b border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/60" />
              <span className="w-3 h-3 rounded-full bg-amber-500/60" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/60" />
            </div>
            <div className="px-6 py-1 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-400 flex items-center space-x-2">
              <Lock className="w-3 h-3 text-emerald-400" />
              <span>rcy://operations-center/dashboard?tenant=org_demo_alpha</span>
            </div>
            <div className="text-[10px] font-mono text-emerald-400 font-semibold hidden sm:block">
              RLS ACTIVE
            </div>
          </div>

          {/* Embedded Dashboard Preview Cards */}
          <div className="p-6 lg:p-8 space-y-6">
            {/* KPI Row Preview */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="command-card p-4 rounded-xl">
                <span className="text-[10px] font-medium text-slate-400 uppercase">Total Deductions</span>
                <div className="text-xl font-bold font-mono text-slate-100 mt-1">$1,768.50</div>
                <div className="text-[10px] text-slate-500 mt-1">116 financial items</div>
              </div>
              <div className="command-card-hero p-4 rounded-xl">
                <span className="text-[10px] font-semibold text-emerald-400 uppercase">Recovery Pipeline</span>
                <div className="text-xl font-bold font-mono text-emerald-300 mt-1">$928.50</div>
                <div className="text-[10px] text-emerald-400/80 mt-1">39 contradicted charges</div>
              </div>
              <div className="command-card p-4 rounded-xl">
                <span className="text-[10px] font-medium text-slate-400 uppercase">Claim Precision</span>
                <div className="text-xl font-bold font-mono text-slate-100 mt-1">100%</div>
                <div className="text-[10px] text-slate-500 mt-1">0 ungrounded claims</div>
              </div>
              <div className="command-card p-4 rounded-xl">
                <span className="text-[10px] font-medium text-slate-400 uppercase">Conservative Skips</span>
                <div className="text-xl font-bold font-mono text-amber-300 mt-1">43</div>
                <div className="text-[10px] text-slate-500 mt-1">33 Silent &bull; 10 Uncertain</div>
              </div>
            </div>

            {/* Table Mockup Preview */}
            <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 overflow-hidden text-xs">
              <div className="p-3 border-b border-slate-800 flex justify-between items-center bg-slate-950/40">
                <span className="font-semibold text-slate-200">Recent Deduction Line Items</span>
                <Link href="/dashboard" className="text-emerald-400 hover:text-emerald-300 font-medium text-[11px] flex items-center space-x-1">
                  <span>Open Full Dashboard</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              <div className="divide-y divide-slate-800/60 font-mono text-[11px]">
                <div className="p-3 flex items-center justify-between hover:bg-slate-800/30">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-200">CH-TC07-DUPLICATE</span>
                    <span className="text-emerald-400">UNIT-TC07</span>
                    <span className="text-slate-300 font-sans">Inbound Defect Fee</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="font-bold text-slate-100">$15.00</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold">
                      CONTRADICTED
                    </span>
                  </div>
                </div>

                <div className="p-3 flex items-center justify-between hover:bg-slate-800/30">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-200">CH-TC10-UNMODELED</span>
                    <span className="text-emerald-400">UNIT-TC10</span>
                    <span className="text-slate-300 font-sans">Unauthorized Prep Relabel</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="font-bold text-slate-100">$55.00</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold">
                      UNCERTAIN
                    </span>
                  </div>
                </div>

                <div className="p-3 flex items-center justify-between hover:bg-slate-800/30">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-200">CH-TC06-RETURNED</span>
                    <span className="text-emerald-400">UNIT-TC06</span>
                    <span className="text-slate-300 font-sans">Refund Issued Item Not Returned</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="font-bold text-slate-100">$60.00</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold">
                      CONTRADICTED
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 9. NOT A VISION AGENT — OPERATIONAL DATA CLARIFICATION        */}
      {/* ============================================================ */}
      <section className="py-20 border-t border-slate-800/60 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="command-card p-8 rounded-3xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
                Architecture Clarification
              </span>
              <h3 className="text-2xl font-bold text-slate-100 font-sans">
                Built for operational records, not camera workflows.
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Recovery Manager is an evidence correlation and recovery agent, not a computer vision model.
                It ingests and audits structured scanner records, scale weights, barcode logs, and reimbursement reports —
                requiring zero cameras, image labeling, or video surveillance hardware.
              </p>
            </div>
            <div className="flex items-center space-x-2 font-mono text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-4 py-2.5 rounded-xl shrink-0">
              <CheckCircle2 className="w-4 h-4" />
              <span>Record-First Architecture</span>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 10. WHY CONSERVATIVE MATTERS (ACCOUNT SAFETY PRINCIPLE)       */}
      {/* ============================================================ */}
      <section id="principles" className="py-24 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-4">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
              Account Safety & Defensibility
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight font-sans">
              More claims isn't the goal. Defensible claims are.
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Dispute scraping tools submit hundreds of speculative claims, resulting in high rejection rates
              and seller account warnings. Recovery Manager takes the opposite stance:
            </p>
            <div className="space-y-3 pt-2">
              <div className="flex items-start space-x-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Zero hallucinated evidence. Missing proof results strictly in SILENT ($0.00 recovery).</span>
              </div>
              <div className="flex items-start space-x-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Every submitted claim includes immutable pre-shipment operator scan records.</span>
              </div>
              <div className="flex items-start space-x-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Protects long-term marketplace standing by preventing ungrounded dispute filings.</span>
              </div>
            </div>
          </div>

          {/* Equation comparison box */}
          <div className="space-y-4">
            <div className="p-6 rounded-2xl bg-rose-950/15 border border-rose-800/30 space-y-2">
              <div className="text-xs font-bold text-rose-300 uppercase tracking-wider">
                The Aggressive Scraping Approach (Risky)
              </div>
              <p className="text-xs font-mono text-slate-300">
                Automated Dispute Spam &rarr; 60% Rejection &rarr; Account Suspension Risk
              </p>
            </div>

            <div className="p-6 rounded-2xl command-card-hero space-y-2">
              <div className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                RCY Recovery Conservative Standard
              </div>
              <p className="text-xs font-mono text-emerald-200">
                Operational Proof + Conservative Verdicts &rarr; 100% Defensible Reimbursements
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 11. FINAL HIGH-IMPACT CTA                                    */}
      {/* ============================================================ */}
      <section className="py-24 border-t border-slate-800/60 bg-gradient-to-b from-slate-950 to-[#080c15] relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-100 tracking-tight font-sans">
            Turn deductions into evidence-backed decisions.
          </h2>
          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Launch the Recovery Operations Center to inspect deductions, trace multi-hop evidence graphs,
            and generate frozen dispute dossiers.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-2xl shadow-emerald-950/60 flex items-center justify-center space-x-2 transition-all duration-200 group"
            >
              <span>Launch Recovery Center</span>
              <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Link>
            <Link
              href="/charges"
              className="w-full sm:w-auto px-6 py-4 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-300 font-semibold text-sm border border-slate-750 flex items-center justify-center transition-all duration-200"
            >
              <span>Explore Live Charges</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 12. FOOTER                                                   */}
      {/* ============================================================ */}
      <footer className="py-12 border-t border-slate-800/80 bg-[#060910] text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Scale className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="font-bold text-slate-300">RCY RECOVERY</span>
              <span className="text-[10px] text-slate-500 ml-2 font-mono">Evidence Operations Center</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6 text-[11px] text-slate-400 font-medium">
            <Link href="/dashboard" className="hover:text-slate-200 transition-colors">Operations Center</Link>
            <Link href="/charges" className="hover:text-slate-200 transition-colors">Charges Explorer</Link>
            <Link href="/recovery" className="hover:text-slate-200 transition-colors">Recovery Pipeline</Link>
            <Link href="/evidence" className="hover:text-slate-200 transition-colors">Evidence Records</Link>
            <Link href="/claims" className="hover:text-slate-200 transition-colors">Claims & Audit</Link>
            <Link href="/data-sources" className="hover:text-slate-200 transition-colors">Data Ingestion</Link>
          </div>

          <div className="text-[11px] font-mono text-slate-500">
            Tenant Isolated &bull; v1.0 Production
          </div>
        </div>
      </footer>
    </div>
  );
}
