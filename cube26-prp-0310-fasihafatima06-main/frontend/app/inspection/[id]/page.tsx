"use client";
import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ShieldAlert,
  Sliders,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Camera,
  RotateCcw,
  UserCheck,
  FileCode,
  ArrowLeft,
  MessageSquarePlus,
  AlertTriangle,
  Sparkles,
  Send
} from "lucide-react";
import { fetchInspection, submitAdditionalEvidence, submitInspectionFeedback } from "@/lib/api";
import { InspectionResponse, CheckResult, BoundingBox } from "@/lib/types";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EvidenceOverlayCanvas } from "@/components/inspection/EvidenceOverlayCanvas";
import { CheckDetailModal } from "@/components/inspection/CheckDetailModal";

export default function InspectionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [inspection, setInspection] = useState<InspectionResponse | null>(null);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  const [selectedCheck, setSelectedCheck] = useState<CheckResult | null>(null);
  const [showAdditionalModal, setShowAdditionalModal] = useState<boolean>(false);
  const [additionalFile, setAdditionalFile] = useState<File | null>(null);
  const [isSubmittingEvidence, setIsSubmittingEvidence] = useState<boolean>(false);

  // Agent Feedback & Continuous Learning Modal States
  const [showFeedbackModal, setShowFeedbackModal] = useState<boolean>(false);
  const [feedbackCheckId, setFeedbackCheckId] = useState<string>("");
  const [feedbackCheckName, setFeedbackCheckName] = useState<string>("");
  const [correctedStatus, setCorrectedStatus] = useState<string>("FAIL");
  const [feedbackCategory, setFeedbackCategory] = useState<string>("MISIDENTIFIED_FEATURE");
  const [feedbackNotes, setFeedbackNotes] = useState<string>("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState<boolean>(false);

  // Overlay toggle states
  const [toggles, setToggles] = useState({
    labels: true,
    barcodes: true,
    edges: true,
    text: true,
    packaging: true,
  });

  const loadData = () => {
    fetchInspection(id)
      .then(setInspection)
      .catch((err) => console.error("Error loading inspection:", err));
  };

  useEffect(() => {
    if (id) loadData();
  }, [id]);

  if (!inspection) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono text-xs flex flex-col items-center justify-center gap-3">
        <span className="animate-spin rounded-full h-6 w-6 border-2 border-[#714B67] border-t-transparent"></span>
        <span>Loading Inspection Workspace #{id}...</span>
      </div>
    );
  }

  const selectedImage = inspection.images[selectedImageIndex] || inspection.images[0];

  // Aggregate bounding boxes across all checks for the selected image
  const allBoundingBoxes: BoundingBox[] = [];
  inspection.checks.forEach((c) => {
    if (c.evidence?.bounding_boxes) {
      allBoundingBoxes.push(...c.evidence.bounding_boxes);
    }
  });

  const passedCount = inspection.checks.filter((c) => c.status === "PASS").length;
  const failedCount = inspection.checks.filter((c) => c.status === "FAIL").length;
  const uncertainCount = inspection.checks.filter((c) => c.status === "UNCERTAIN").length;

  const handleUploadAdditional = async () => {
    setIsSubmittingEvidence(true);
    try {
      const formData = new FormData();
      formData.append("view_angle", "back");
      if (additionalFile) {
        formData.append("files", additionalFile);
      }
      const updated = await submitAdditionalEvidence(id, formData);
      setInspection(updated);
      setShowAdditionalModal(false);
    } catch (err) {
      console.error(err);
      alert("Failed to submit additional evidence.");
    } finally {
      setIsSubmittingEvidence(false);
    }
  };

  const handleOpenFeedback = (check?: CheckResult) => {
    if (check) {
      setFeedbackCheckId(check.id);
      setFeedbackCheckName(check.name);
      setFeedbackNotes(`Agent misidentified '${check.name}'. Corrected to non-compliant because feature is incorrect.`);
    } else {
      setFeedbackCheckId("");
      setFeedbackCheckName("Overall Inspection Verdict");
      setFeedbackNotes("Agent verdict misidentified features. No FNSKU barcode sticker present on package surface.");
    }
    setCorrectedStatus("FAIL");
    setShowFeedbackModal(true);
  };

  const handleSendFeedback = async () => {
    if (!feedbackNotes.trim()) {
      alert("Please type a quick feedback message for the agent.");
      return;
    }

    setIsSubmittingFeedback(true);
    try {
      const updated = await submitInspectionFeedback(id, {
        check_id: feedbackCheckId || undefined,
        check_name: feedbackCheckName || undefined,
        corrected_status: correctedStatus,
        feedback_category: feedbackCategory,
        operator_notes: feedbackNotes,
        operator_name: "Operator #104"
      });
      setInspection(updated);
      setShowFeedbackModal(false);
    } catch (err) {
      console.error(err);
      alert("Failed to submit feedback.");
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  return (
    <div className="space-y-4 max-w-[1600px] mx-auto pb-12">
      {/* Top Header Navigation */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/history")}
            className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="font-extrabold text-slate-900 text-lg font-mono">{inspection.inspection_id}</h2>
              <StatusBadge status={inspection.overall_status} size="lg" />
              {inspection.is_overridden && (
                <span className="bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 font-sans">
                  <Sparkles className="w-3 h-3 text-amber-600" />
                  Agent Decision Corrected by Operator
                </span>
              )}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              Product: <span className="text-slate-900 font-bold">{inspection.product_name || inspection.product_id}</span> • Work Order: <span className="font-mono">{inspection.work_order_id || "WO-88902"}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleOpenFeedback()}
            className="bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-xs px-3.5 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all shadow-xs"
            title="Mark decision as wrong and send feedback to improve the agent"
          >
            <MessageSquarePlus className="w-3.5 h-3.5 text-amber-700" />
            <span>Mark Agent Error / Give Feedback</span>
          </button>
          <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200 font-mono font-medium">
            {inspection.mode}
          </span>
          <a
            href={`/api/inspections/${inspection.inspection_id}/evidence`}
            target="_blank"
            rel="noreferrer"
            className="bg-[#F3EDF2] hover:bg-[#E4D6E2] text-[#714B67] text-xs px-3.5 py-1.5 rounded-xl border border-[#E4D6E2] font-bold flex items-center gap-1.5 transition-colors"
          >
            <FileCode className="w-3.5 h-3.5 text-[#714B67]" />
            <span>Agent JSON API</span>
          </a>
        </div>
      </div>

      {/* Operator Feedback Override Notification Banner */}
      {inspection.is_overridden && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 flex items-start gap-3 shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-950 space-y-1">
            <span className="font-extrabold text-amber-900 block">Operator Feedback Recorded & Decision Overridden</span>
            <p className="text-amber-900/90 leading-relaxed font-medium">
              "{inspection.operator_feedback_notes}"
            </p>
            <span className="text-[10px] text-amber-700 font-mono block pt-0.5">
              ✓ Logged to agent continuous learning memory & audit trail.
            </span>
          </div>
        </div>
      )}

      {/* 3-COLUMN ENTERPRISE WORKSPACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* LEFT COLUMN — Photo Thumbnails (2 cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="bg-white border border-slate-200 rounded-2xl p-3 space-y-3 shadow-sm">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block px-1">
              Evidence Photos ({inspection.images.length})
            </span>
            <div className="space-y-2">
              {inspection.images.map((img, idx) => {
                const isSelected = idx === selectedImageIndex;
                const imgUrl = img.file_path.startsWith("http")
                  ? img.file_path
                  : `/${img.file_path.replace(/\\/g, "/")}`;

                return (
                  <button
                    key={img.id || idx}
                    onClick={() => setSelectedImageIndex(idx)}
                    className={`w-full rounded-xl overflow-hidden border text-left transition-all ${
                      isSelected
                        ? "border-[#714B67] ring-2 ring-[#714B67]/20 shadow-xs"
                        : "border-slate-200 hover:border-slate-300 opacity-80 hover:opacity-100"
                    }`}
                  >
                    <div className="relative aspect-video bg-slate-100">
                      <img src={imgUrl} alt="Thumbnail" className="w-full h-full object-cover" />
                      <span className="absolute bottom-1 right-1 bg-slate-900/80 text-white text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-bold">
                        {img.view_angle}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* CENTER COLUMN — Large Image & Overlay Canvas (6 cols) */}
        <div className="lg:col-span-6 space-y-3">
          <div className="bg-white border border-slate-200 rounded-2xl p-3 space-y-3 shadow-sm">
            {/* Overlay Toggle Controls Bar */}
            <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-xs">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-[#714B67]" />
                Evidence Overlays:
              </span>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 cursor-pointer text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={toggles.labels}
                    onChange={(e) => setToggles({ ...toggles, labels: e.target.checked })}
                    className="accent-[#714B67] rounded"
                  />
                  <span>Labels</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={toggles.barcodes}
                    onChange={(e) => setToggles({ ...toggles, barcodes: e.target.checked })}
                    className="accent-[#714B67] rounded"
                  />
                  <span>Barcodes</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={toggles.edges}
                    onChange={(e) => setToggles({ ...toggles, edges: e.target.checked })}
                    className="accent-[#714B67] rounded"
                  />
                  <span>Package Edges</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={toggles.text}
                    onChange={(e) => setToggles({ ...toggles, text: e.target.checked })}
                    className="accent-[#714B67] rounded"
                  />
                  <span>Text</span>
                </label>
              </div>
            </div>

            {/* Evidence Overlay Canvas Component */}
            {selectedImage && (
              <EvidenceOverlayCanvas
                imageUrl={
                  selectedImage.file_path.startsWith("http")
                    ? selectedImage.file_path
                    : `/${selectedImage.file_path.replace(/\\/g, "/")}`
                }
                width={selectedImage.width || 800}
                height={selectedImage.height || 600}
                boundingBoxes={allBoundingBoxes}
                activeToggles={toggles}
              />
            )}
          </div>
        </div>

        {/* RIGHT COLUMN — Compliance Checklist & Action Panels (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Prep Status Summary Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-bold block">Overall Prep Status</span>
                <div className="mt-1 flex items-center gap-2">
                  <StatusBadge status={inspection.overall_status} size="lg" />
                </div>
              </div>
              <div className="text-right text-xs text-slate-500 font-mono">
                <div>{inspection.checks.length} Checks Total</div>
                <div className="text-[#00A09D] font-bold">{passedCount} PASS</div>
                <div className="text-rose-600 font-bold">{failedCount} FAIL</div>
                <div className="text-amber-600 font-bold">{uncertainCount} UNCERTAIN</div>
              </div>
            </div>

            {/* ACTIONABLE WORKFLOW PANELS */}

            {/* 1. FAIL UX PANEL */}
            {inspection.overall_status === "FAIL" && (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-rose-700 font-extrabold text-xs">
                  <XCircle className="w-4 h-4 shrink-0" />
                  <span>PREP STATUS: NON-COMPLIANT (FAIL)</span>
                </div>
                <p className="text-xs text-rose-900 leading-relaxed font-medium">
                  {inspection.agent_action.message}
                </p>
                <div className="pt-2">
                  <button
                    onClick={() => router.push("/inspect")}
                    className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-2 rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reposition Label & Rescan</span>
                  </button>
                </div>
              </div>
            )}

            {/* 2. UNCERTAIN UX PANEL */}
            {inspection.overall_status === "UNCERTAIN" && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-amber-800 font-extrabold text-xs">
                  <HelpCircle className="w-4 h-4 shrink-0" />
                  <span>NEEDS MORE EVIDENCE</span>
                </div>
                <p className="text-xs text-amber-900 leading-relaxed font-medium">
                  {inspection.agent_action.message}
                </p>
                <div className="pt-2 flex items-center gap-2">
                  <button
                    onClick={() => setShowAdditionalModal(true)}
                    className="flex-1 bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>Capture / Upload Rear Photo</span>
                  </button>
                  <button
                    onClick={() => alert("Inspection escalated to Warehouse Supervisor for manual audit.")}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold py-2 px-3 rounded-xl text-xs border border-slate-300 flex items-center gap-1"
                  >
                    <UserCheck className="w-3.5 h-3.5 text-slate-600" />
                    <span>Manual Review</span>
                  </button>
                </div>
              </div>
            )}

            {/* 3. PASS UX PANEL */}
            {inspection.overall_status === "PASS" && (
              <div className="bg-[#E6F6F6] border border-[#BCE7E6] rounded-xl p-4 space-y-1">
                <div className="flex items-center gap-2 text-[#00A09D] font-extrabold text-xs">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>PREP STATUS: VERIFIED COMPLIANT</span>
                </div>
                <p className="text-xs text-slate-800 leading-relaxed font-medium">
                  {inspection.agent_action.message}
                </p>
              </div>
            )}
          </div>

          {/* Compliance Checks List with Feedback Triggers */}
          <div className="bg-white border border-slate-200 rounded-2xl p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Individual Compliance Checks ({inspection.checks.length})
              </h3>
              <span className="text-[10px] text-slate-500 font-medium">Click check to correct</span>
            </div>

            <div className="space-y-2">
              {inspection.checks.map((chk) => (
                <div
                  key={chk.id}
                  className="bg-slate-50 border border-slate-200 hover:border-[#714B67] rounded-xl p-3 transition-all space-y-2 group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1 flex-1 cursor-pointer" onClick={() => setSelectedCheck(chk)}>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-900 group-hover:text-[#714B67] transition-colors">
                          {chk.name}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 line-clamp-2 leading-snug font-normal">
                        {chk.reason}
                      </p>
                    </div>
                    <div className="shrink-0 flex flex-col items-end gap-1.5">
                      <StatusBadge status={chk.status} size="sm" />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenFeedback(chk);
                        }}
                        className="text-[10px] text-amber-700 hover:text-amber-900 hover:underline font-bold flex items-center gap-1 pt-1"
                        title="Correct this specific rule decision"
                      >
                        <MessageSquarePlus className="w-3 h-3 text-amber-600" />
                        <span>Correct</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Check Detail Modal */}
      <CheckDetailModal check={selectedCheck} onClose={() => setSelectedCheck(null)} />

      {/* Additional Evidence Upload Modal (Actionable UNCERTAIN Workflow) */}
      {showAdditionalModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
                <Camera className="w-4 h-4 text-[#714B67]" />
                Upload Additional Surface Photograph
              </h3>
              <button onClick={() => setShowAdditionalModal(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              The rear surface photograph is missing. Capture or upload a rear-facing photo of the product container to verify the original manufacturer barcode requirement.
            </p>

            <label className="border-2 border-dashed border-slate-200 hover:border-[#714B67] bg-slate-50 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors">
              <Camera className="w-6 h-6 text-[#714B67] mb-2" />
              <span className="text-xs text-slate-800 font-bold">
                {additionalFile ? additionalFile.name : "Select Rear Surface Photograph"}
              </span>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => e.target.files && setAdditionalFile(e.target.files[0])}
                className="hidden"
              />
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowAdditionalModal(false)}
                className="bg-slate-100 text-slate-700 px-4 py-2 rounded-xl text-xs hover:bg-slate-200 font-bold"
              >
                Cancel
              </button>
              <button
                onClick={handleUploadAdditional}
                disabled={isSubmittingEvidence}
                className="btn-odoo font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 disabled:opacity-50"
              >
                {isSubmittingEvidence ? "Processing Evidence..." : "Submit & Re-inspect"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OPERATOR AGENT FEEDBACK & CONTINUOUS LEARNING MODAL */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-amber-100 text-amber-800 rounded-xl">
                  <MessageSquarePlus className="w-5 h-5 text-amber-700" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-sm">Correct Agent & Provide Feedback</h3>
                  <p className="text-[11px] text-slate-500 font-medium">Continuous Learning & Override Loop</p>
                </div>
              </div>
              <button onClick={() => setShowFeedbackModal(false)} className="text-slate-400 hover:text-slate-600 text-lg font-bold">
                ✕
              </button>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl text-xs space-y-1">
              <span className="font-bold text-slate-700 block">Target Rule / Inspection:</span>
              <span className="text-[#714B67] font-bold text-xs">{feedbackCheckName || "Overall Inspection Decision"}</span>
            </div>

            {/* 1. Corrected Status Selection */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-800 block">1. Select Corrected Status:</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setCorrectedStatus("FAIL")}
                  className={`py-2 px-3 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    correctedStatus === "FAIL"
                      ? "bg-rose-100 text-rose-800 border-rose-300 shadow-xs ring-2 ring-rose-500/20"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  <XCircle className="w-3.5 h-3.5 text-rose-600" />
                  <span>FAIL (Non-compliant)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setCorrectedStatus("UNCERTAIN")}
                  className={`py-2 px-3 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    correctedStatus === "UNCERTAIN"
                      ? "bg-amber-100 text-amber-800 border-amber-300 shadow-xs ring-2 ring-amber-500/20"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                  <span>UNCERTAIN</span>
                </button>

                <button
                  type="button"
                  onClick={() => setCorrectedStatus("PASS")}
                  className={`py-2 px-3 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    correctedStatus === "PASS"
                      ? "bg-[#E6F6F6] text-[#00A09D] border-[#BCE7E6] shadow-xs ring-2 ring-[#00A09D]/20"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#00A09D]" />
                  <span>PASS (Compliant)</span>
                </button>
              </div>
            </div>

            {/* 2. Error Category */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-800 block">2. Reason Category:</label>
              <select
                value={feedbackCategory}
                onChange={(e) => setFeedbackCategory(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 font-medium focus:outline-none focus:border-[#714B67]"
              >
                <option value="MISIDENTIFIED_FEATURE">Misidentified Feature (e.g. warning text mistaken for FNSKU label)</option>
                <option value="MISSING_BARCODE">Missing Barcode Sticker (polybag has text but no barcode sticker)</option>
                <option value="WRONG_BOUNDING_BOX">Incorrect Bounding Box Overlay</option>
                <option value="GLARE_BLUR">Glare or Blur Misinterpretation</option>
                <option value="OTHER">Other Operator Override</option>
              </select>
            </div>

            {/* 3. Detailed Feedback Notes */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-800 block">
                3. Feedback Message for Agent Training:
              </label>
              <textarea
                rows={3}
                value={feedbackNotes}
                onChange={(e) => setFeedbackNotes(e.target.value)}
                placeholder="Explain what the agent got wrong (e.g., 'There is no FNSKU barcode sticker present on this polybag; suffocation warning text was misidentified as FNSKU label')."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-900 focus:outline-none focus:border-[#714B67] leading-relaxed"
              />
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-[10px] text-slate-500 font-mono">
                Log entry saved to SQLite audit history.
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowFeedbackModal(false)}
                  className="bg-slate-100 text-slate-700 font-bold px-4 py-2 rounded-xl text-xs hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSendFeedback}
                  disabled={isSubmittingFeedback}
                  className="btn-odoo font-bold px-5 py-2 rounded-xl text-xs flex items-center gap-2 disabled:opacity-50 shadow-sm"
                >
                  {isSubmittingFeedback ? (
                    <span className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></span>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Submit Correction & Train Agent</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
