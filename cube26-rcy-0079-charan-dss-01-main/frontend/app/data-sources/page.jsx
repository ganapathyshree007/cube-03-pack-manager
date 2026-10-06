"use client";
import React, { useState, useEffect } from "react";
import Navbar from "../../components/Navbar";
import { useWorkspace } from "../../context/WorkspaceContext";
import { api } from "../../lib/api";
import {
  UploadCloud,
  FileSpreadsheet,
  PlusCircle,
  CheckCircle2,
  AlertCircle,
  FileText,
  FileCheck,
  FolderOpen,
  ArrowRight,
  ShieldAlert,
  Database,
  Layers,
  Sparkles,
} from "lucide-react";

export default function DataSourcesPage() {
  const { currentCompany } = useWorkspace();
  const [activeTab, setActiveTab] = useState("upload"); // "upload", "charge_manual", "evidence_manual"
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(true);

  // File upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importSuccess, setImportSuccess] = useState(null);

  // Manual Charge form state
  const [chargeForm, setChargeForm] = useState({
    charge_id: "",
    unit_id: "",
    shipment_id: "",
    order_id: "",
    sku: "",
    reason: "inbound_defect_fee",
    amount: "",
    charge_date: new Date().toISOString().split("T")[0],
  });

  // Manual Evidence form state
  const [evidenceForm, setEvidenceForm] = useState({
    evidence_id: "",
    source_type: "prep",
    unit_id: "",
    shipment_id: "",
    order_id: "",
    sku: "",
    event_type: "fba_prep_compliance",
    finding: "PASS",
    description: "",
    timestamp: new Date().toISOString(),
  });

  const loadFiles = async () => {
    try {
      setLoadingFiles(true);
      const data = await api.getUploadedFiles(currentCompany);
      setUploadedFiles(data || []);
    } catch (err) {
      console.error("Failed to load uploaded files:", err);
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [currentCompany]);

  // File select & preview
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    setImportSuccess(null);
    setPreviewData(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("company_id", currentCompany);

    try {
      setUploading(true);
      const preview = await api.previewUpload(formData);
      setPreviewData(preview);
    } catch (err) {
      alert(`Preview failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  // Confirm Import
  const handleConfirmImport = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("company_id", currentCompany);

    try {
      setImporting(true);
      const res = await api.importFile(formData);
      setImportSuccess(res);
      setPreviewData(null);
      setSelectedFile(null);
      loadFiles();
    } catch (err) {
      alert(`Import failed: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  // Submit manual charge
  const handleSubmitCharge = async (e) => {
    e.preventDefault();
    try {
      await api.createManualCharge({
        ...chargeForm,
        amount: parseFloat(chargeForm.amount) || 0.0,
        company_id: currentCompany,
      });
      alert(`Charge ${chargeForm.charge_id} created successfully!`);
      setChargeForm({
        charge_id: "",
        unit_id: "",
        shipment_id: "",
        order_id: "",
        sku: "",
        reason: "inbound_defect_fee",
        amount: "",
        charge_date: new Date().toISOString().split("T")[0],
      });
    } catch (err) {
      alert(`Failed to create charge: ${err.message}`);
    }
  };

  // Submit manual evidence
  const handleSubmitEvidence = async (e) => {
    e.preventDefault();
    try {
      await api.createManualEvidence({
        ...evidenceForm,
        company_id: currentCompany,
      });
      alert(`Evidence ${evidenceForm.evidence_id} created successfully!`);
      setEvidenceForm({
        evidence_id: "",
        source_type: "prep",
        unit_id: "",
        shipment_id: "",
        order_id: "",
        sku: "",
        event_type: "fba_prep_compliance",
        finding: "PASS",
        description: "",
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      alert(`Failed to create evidence: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <Navbar onRefresh={loadFiles} />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full page-enter">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/15 to-emerald-600/5 border border-emerald-500/20 text-emerald-400 shadow-glow">
                <Database className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100">
                Data Ingestion & Source Control
              </h1>
            </div>
            <p className="text-sm text-slate-500 mt-1.5">
              Ingest fee reports, receiving records, prep inspection logs, or record single transactions with strict tenant isolation.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono bg-slate-900/60 border border-slate-800/60 px-3.5 py-1.5 rounded-xl">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Tenant: {currentCompany}</span>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center p-1 bg-slate-900/80 border border-slate-800/60 rounded-xl max-w-fit space-x-1">
          <button
            onClick={() => setActiveTab("upload")}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
              activeTab === "upload"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-950/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Document (CSV, XLSX, PDF, JSON)</span>
          </button>
          <button
            onClick={() => setActiveTab("charge_manual")}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
              activeTab === "charge_manual"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-950/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Manual Charge</span>
          </button>
          <button
            onClick={() => setActiveTab("evidence_manual")}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
              activeTab === "evidence_manual"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-950/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Manual Evidence</span>
          </button>
        </div>

        {/* Tab 1: File Ingestion Pipeline */}
        {activeTab === "upload" && (
          <div className="space-y-6">
            {/* Drag & Drop Upload Zone */}
            <div className="border-2 border-dashed border-slate-800/80 hover:border-emerald-500/50 rounded-2xl p-10 text-center glass-surface transition-all duration-300 group hover:shadow-glow">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4 group-hover:scale-105 transition-transform duration-200">
                <UploadCloud className="w-7 h-7" />
              </div>
              <h3 className="text-base font-semibold text-slate-100">Upload Channel or Operational Report</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-lg mx-auto leading-relaxed">
                Universal parser automatically classifies fee reports, receiving custody logs, prep inspection reports, pack sheets, and customer returns (.csv, .xlsx, .pdf, .json).
              </p>

              <div className="flex items-center justify-center gap-2 mt-4 text-[11px] font-mono text-slate-400">
                <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">CSV</span>
                <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">XLSX</span>
                <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">PDF</span>
                <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">JSON</span>
              </div>

              <div className="mt-6">
                <label className="btn-primary cursor-pointer">
                  <span>Browse File</span>
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls,.json,.pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </div>

              {uploading && (
                <div className="inline-flex items-center space-x-2 text-xs text-emerald-400 mt-4 bg-emerald-950/40 border border-emerald-800/40 px-3 py-1.5 rounded-full animate-fade-in">
                  <div className="w-3.5 h-3.5 border-2 border-emerald-400/20 border-t-emerald-400 rounded-full animate-spin" />
                  <span>Parsing schemas & pre-validating headers...</span>
                </div>
              )}
            </div>

            {/* Import Result Banner */}
            {importSuccess && (
              <div
                className={`p-4 rounded-2xl text-xs border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-card animate-fade-in ${
                  importSuccess.charges_imported === 0 && importSuccess.evidence_records_imported === 0
                    ? "bg-amber-950/25 border-amber-800/40 text-amber-200"
                    : "bg-emerald-950/20 border-emerald-800/40 text-emerald-300"
                }`}
              >
                <div className="flex items-start sm:items-center space-x-3">
                  {importSuccess.charges_imported === 0 && importSuccess.evidence_records_imported === 0 ? (
                    <div className="w-8 h-8 rounded-xl bg-amber-500/15 flex items-center justify-center shrink-0">
                      <AlertCircle className="w-4 h-4 text-amber-400" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-xl bg-emerald-500/15 flex items-center justify-center shrink-0">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    </div>
                  )}
                  <div>
                    {importSuccess.message ? (
                      <div className="font-semibold text-slate-100">{importSuccess.message}</div>
                    ) : (
                      <div className="font-medium text-slate-200">
                        Processed <code className="font-mono text-emerald-400 bg-slate-900/80 px-1.5 py-0.5 rounded">{importSuccess.filename}</code>:{" "}
                        <strong className="text-emerald-400">{importSuccess.charges_imported || 0}</strong> new charges,{" "}
                        <strong className="text-emerald-400">{importSuccess.evidence_records_imported || 0}</strong> new evidence records.
                      </div>
                    )}
                    {importSuccess.duplicate_charges_skipped > 0 && (
                      <div className="text-[11px] text-amber-300/90 mt-1 flex items-center space-x-1.5">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span><strong>Ledger Deduplication:</strong> {importSuccess.duplicate_charges_skipped} rows matched existing Charge IDs and were skipped to protect against double-charging claims.</span>
                      </div>
                    )}
                  </div>
                </div>
                <span className="font-mono text-[10px] text-slate-400 whitespace-nowrap self-start sm:self-center bg-slate-900/60 px-2.5 py-1 rounded-lg border border-slate-800/60">
                  Tenant: {currentCompany}
                </span>
              </div>
            )}

            {/* Ingestion Preview & Column Validation */}
            {previewData && (
              <div className="rounded-2xl glass-surface-strong border border-slate-800/70 p-6 space-y-4 shadow-card animate-scale-in">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-4">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
                      Detected Type: {previewData.file_type?.toUpperCase()}
                    </span>
                    <h3 className="text-sm font-bold text-slate-100 mt-2">Ingestion Pre-Validation Preview</h3>
                    <p className="text-xs text-slate-400">Review mapped headers and record samples before committing to the immutable ledger.</p>
                  </div>
                  <div className="text-right text-xs">
                    <span className="text-emerald-400 font-bold font-mono text-sm">{previewData.valid_rows}</span>{" "}
                    <span className="text-slate-400">valid rows</span> &bull;{" "}
                    <span className="text-slate-300 font-mono">{previewData.columns_detected?.length} columns</span>
                  </div>
                </div>

                {/* Column tags */}
                <div>
                  <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-2">Detected Column Schema:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {previewData.columns_detected?.map((col, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-md text-[10px] font-mono bg-slate-950/80 border border-slate-800 text-slate-300"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Sample Preview Table */}
                <div className="overflow-x-auto border border-slate-800/80 rounded-xl shadow-inner">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-slate-950 text-slate-400 uppercase font-mono">
                      <tr>
                        {previewData.columns_detected?.slice(0, 6).map((col, idx) => (
                          <th key={idx} className="p-3 border-b border-slate-800 font-semibold">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 bg-slate-900/40">
                      {previewData.sample_preview?.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-800/30 transition">
                          {previewData.columns_detected?.slice(0, 6).map((col, cIdx) => (
                            <td key={cIdx} className="p-3 truncate max-w-xs font-mono text-slate-300">
                              {String(row[col] ?? "")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Confirm Import Button */}
                <div className="flex justify-end space-x-3 pt-2">
                  <button
                    onClick={() => setPreviewData(null)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmImport}
                    disabled={importing}
                    className="btn-primary"
                  >
                    <FileCheck className="w-4 h-4" />
                    <span>{importing ? "Importing to Ledger..." : "Confirm & Ingest Data"}</span>
                  </button>
                </div>
              </div>
            )}

            {/* List of previously uploaded files */}
            <div className="rounded-2xl bg-slate-900/60 border border-slate-800/50 overflow-hidden shadow-card">
              <div className="p-5 border-b border-slate-800/50 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    Tenant Source Documents (Cloudinary & Local Storage)
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">Audit log of all uploaded files associated with this workspace.</p>
                </div>
                <span className="text-xs text-slate-400 font-mono bg-slate-950/60 px-2.5 py-1 rounded-lg border border-slate-800/60">
                  {uploadedFiles.length} files tracked
                </span>
              </div>
              <div className="divide-y divide-slate-800/40 text-xs">
                {uploadedFiles.length === 0 ? (
                  <div className="p-12 text-center text-slate-500">No source files logged for this tenant workspace yet.</div>
                ) : (
                  uploadedFiles.map((f) => (
                    <div key={f.id} className="p-4 flex justify-between items-center table-row-hover">
                      <div className="flex items-center space-x-3.5">
                        <div className="w-9 h-9 rounded-xl bg-slate-800/70 border border-slate-700/60 flex items-center justify-center text-emerald-400">
                          <FileSpreadsheet className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-200">{f.filename}</div>
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                            Type: <span className="text-slate-400 uppercase">{f.file_type}</span> &bull; <span className="text-slate-400">{f.row_count} rows</span>
                          </div>
                        </div>
                      </div>
                      <span className="font-mono text-[10px] px-2.5 py-1 rounded-md bg-emerald-950/40 border border-emerald-800/40 text-emerald-400 font-semibold">
                        {f.upload_status || "PROCESSED"}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Manual Charge Creation */}
        {activeTab === "charge_manual" && (
          <form onSubmit={handleSubmitCharge} className="glass-surface-strong rounded-2xl p-7 space-y-5 max-w-2xl shadow-card">
            <div className="border-b border-slate-800/60 pb-3">
              <h3 className="text-base font-bold text-slate-100">Add Manual Charge Record</h3>
              <p className="text-xs text-slate-400 mt-0.5">Create a single fee line item to match against operational evidence.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Charge ID <span className="text-rose-400">*</span></label>
                <input
                  required
                  type="text"
                  placeholder="e.g. CH-20491"
                  value={chargeForm.charge_id}
                  onChange={(e) => setChargeForm({ ...chargeForm, charge_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Unit ID</label>
                <input
                  type="text"
                  placeholder="e.g. UNIT-0014"
                  value={chargeForm.unit_id}
                  onChange={(e) => setChargeForm({ ...chargeForm, unit_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Shipment ID</label>
                <input
                  type="text"
                  placeholder="e.g. FBA-DUMMY-101"
                  value={chargeForm.shipment_id}
                  onChange={(e) => setChargeForm({ ...chargeForm, shipment_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Order ID</label>
                <input
                  type="text"
                  placeholder="e.g. ORD-DUMMY-50014"
                  value={chargeForm.order_id}
                  onChange={(e) => setChargeForm({ ...chargeForm, order_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">SKU</label>
                <input
                  type="text"
                  placeholder="e.g. SKU-LAMP-LED"
                  value={chargeForm.sku}
                  onChange={(e) => setChargeForm({ ...chargeForm, sku: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Amount ($ USD) <span className="text-rose-400">*</span></label>
                <input
                  required
                  type="number"
                  step="0.01"
                  placeholder="38.00"
                  value={chargeForm.amount}
                  onChange={(e) => setChargeForm({ ...chargeForm, amount: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-slate-400 font-medium block mb-1.5">Deduction Reason <span className="text-rose-400">*</span></label>
                <select
                  value={chargeForm.reason}
                  onChange={(e) => setChargeForm({ ...chargeForm, reason: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 input-focus"
                >
                  <option value="inbound_defect_fee">Inbound Defect Fee</option>
                  <option value="lost_inbound">Lost Inbound Inventory</option>
                  <option value="refund_issued_item_not_returned">Refund Issued Item Not Returned</option>
                  <option value="damaged_in_warehouse">Damaged In Warehouse</option>
                  <option value="fulfilment_fee_weight_tier">Fulfilment Fee Weight Tier</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800/60">
              <button
                type="submit"
                className="btn-primary"
              >
                Save Charge
              </button>
            </div>
          </form>
        )}

        {/* Tab 3: Manual Evidence Creation */}
        {activeTab === "evidence_manual" && (
          <form onSubmit={handleSubmitEvidence} className="glass-surface-strong rounded-2xl p-7 space-y-5 max-w-2xl shadow-card">
            <div className="border-b border-slate-800/60 pb-3">
              <h3 className="text-base font-bold text-slate-100">Add Manual Evidence Record</h3>
              <p className="text-xs text-slate-400 mt-0.5">Record warehouse floor verification proof to refute channel fee claims.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Evidence ID <span className="text-rose-400">*</span></label>
                <input
                  required
                  type="text"
                  placeholder="e.g. PRP-9912"
                  value={evidenceForm.evidence_id}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, evidence_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Source Stage <span className="text-rose-400">*</span></label>
                <select
                  value={evidenceForm.source_type}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, source_type: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 input-focus"
                >
                  <option value="receiving">Receiving Line</option>
                  <option value="prep">Prep Station</option>
                  <option value="pack">Pack Bench</option>
                  <option value="returns">Returns Processing</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Unit ID</label>
                <input
                  type="text"
                  placeholder="e.g. UNIT-0014"
                  value={evidenceForm.unit_id}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, unit_id: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 font-mono input-focus"
                />
              </div>
              <div>
                <label className="text-slate-400 font-medium block mb-1.5">Finding Verdict <span className="text-rose-400">*</span></label>
                <select
                  value={evidenceForm.finding}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, finding: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 input-focus"
                >
                  <option value="PASS">PASS (Compliant)</option>
                  <option value="FAIL">FAIL (Defect Confirmed)</option>
                  <option value="UNCERTAIN">UNCERTAIN (Ambiguous)</option>
                  <option value="RESTOCKED">RESTOCKED</option>
                  <option value="DISPOSED">DISPOSED</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="text-slate-400 font-medium block mb-1.5">Description / Operational Findings <span className="text-rose-400">*</span></label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Polybag present & sealed: yes. Barcode covered: yes. Item measured at 1.2 lbs."
                  value={evidenceForm.description}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, description: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 placeholder-slate-600 input-focus leading-relaxed"
                />
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800/60">
              <button
                type="submit"
                className="btn-primary"
              >
                Save Evidence Record
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}
