"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Package,
  Upload,
  CheckCircle2,
  AlertCircle,
  Play,
  FileCheck2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Plus,
  HelpCircle,
  Info
} from "lucide-react";
import { fetchProducts, createInspection, fetchTestScenarios } from "@/lib/api";
import { Product, Rule, TestScenario } from "@/lib/types";

export default function NewInspectionPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [scenarios, setScenarios] = useState<TestScenario[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [selectedViewAngle, setSelectedViewAngle] = useState<string>("front");
  const [workOrderId, setWorkOrderId] = useState<string>("WO-88902");
  const [operatorName, setOperatorName] = useState<string>("Operator #104");

  const [isInspecting, setIsInspecting] = useState<boolean>(false);
  const [inspectStage, setInspectStage] = useState<number>(0);

  useEffect(() => {
    fetchProducts().then((data) => {
      setProducts(data);
      if (data.length > 0) setSelectedProductId(data[0].id);
    });
    fetchTestScenarios().then(setScenarios);
  }, []);

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadedFiles(Array.from(e.target.files));
      setSelectedScenarioId(null);
    }
  };

  const handleSelectScenario = (sc: TestScenario) => {
    setSelectedScenarioId(sc.id);
    setSelectedProductId(sc.product_id);
    setUploadedFiles([]);
  };

  const handleStartInspection = async () => {
    if (!selectedProductId) return;

    setIsInspecting(true);
    setInspectStage(1);

    // Backend stage progression visualization
    setTimeout(() => setInspectStage(2), 250);
    setTimeout(() => setInspectStage(3), 500);
    setTimeout(() => setInspectStage(4), 750);
    setTimeout(() => setInspectStage(5), 1000);

    try {
      const formData = new FormData();
      formData.append("product_id", selectedProductId);
      formData.append("work_order_id", workOrderId);
      formData.append("operator_name", operatorName);

      if (selectedScenarioId) {
        formData.append("scenario_id", selectedScenarioId);
      } else if (uploadedFiles.length > 0) {
        uploadedFiles.forEach((file) => formData.append("files", file));
      } else {
        formData.append("scenario_id", "scenario_1");
      }

      const res = await createInspection(formData);
      setTimeout(() => {
        router.push(`/inspection/${res.inspection_id}`);
      }, 1200);
    } catch (err) {
      console.error("Inspection error:", err);
      alert("Failed to run inspection.");
      setIsInspecting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Page Title Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Package className="w-5 h-5 text-[#714B67]" />
            New Inbound Preparation Inspection
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Select an inbound product SKU, upload physical evidence photographs, and trigger the Prep Manager agent pipeline.
          </p>
        </div>

        <button
          onClick={() => router.push("/products")}
          className="btn-odoo font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-1.5 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Add Custom Product</span>
        </button>
      </div>

      {/* Explanatory Info Card on the 3 Categories */}
      <div className="bg-[#F3EDF2] border border-[#E4D6E2] rounded-2xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-[#714B67] shrink-0 mt-0.5" />
        <div className="text-xs text-slate-800 space-y-1">
          <span className="font-bold text-[#714B67] block">Why start with pre-configured product categories?</span>
          <p className="text-slate-700 leading-relaxed">
            Inbound fulfillment prep requirements vary by category: <strong>Liquids</strong> require leak-proof polybags, heat seals & suffocation warnings; <strong>Electronics</strong> require flat FNSKU placement & covered UPCs; <strong>Plush Toys</strong> require protective bagging. You can select any category below or click <strong>"+ Add Custom Product"</strong> to define custom prep rules for any SKU.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1 & 2 Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Step 1 — Product Selection */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                <span className="bg-[#714B67] text-white w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold">1</span>
                Select Inbound Product & Prep Category
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">Dynamic Rule Engine</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {products.map((prod) => {
                const isSelected = prod.id === selectedProductId;
                return (
                  <button
                    key={prod.id}
                    type="button"
                    onClick={() => {
                      setSelectedProductId(prod.id);
                      setSelectedScenarioId(null);
                    }}
                    className={`p-3.5 rounded-xl text-left border transition-all ${
                      isSelected
                        ? "bg-[#F3EDF2] border-[#714B67] text-[#714B67] shadow-xs font-semibold ring-2 ring-[#714B67]/20"
                        : "bg-slate-50 border-slate-200 hover:border-slate-300 text-slate-700"
                    }`}
                  >
                    <div className="font-bold text-xs mb-1 line-clamp-1">{prod.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">SKU: {prod.sku}</div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">ASIN: {prod.asin}</div>
                  </button>
                );
              })}

              {/* Add Custom Product Quick Card */}
              <button
                type="button"
                onClick={() => router.push("/products")}
                className="p-3.5 rounded-xl text-left border border-dashed border-[#714B67]/40 hover:border-[#714B67] bg-[#F3EDF2]/40 text-[#714B67] flex flex-col justify-center items-center gap-1 transition-all group"
              >
                <Plus className="w-5 h-5 text-[#714B67] group-hover:scale-110 transition-transform" />
                <span className="font-bold text-xs text-center">Add Custom Product</span>
                <span className="text-[9px] text-[#714B67]/80 text-center font-normal">Define rules for any SKU</span>
              </button>
            </div>

            {/* Work Order Info */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div>
                <label className="text-[11px] font-bold text-slate-700 block mb-1">Work Order ID</label>
                <input
                  type="text"
                  value={workOrderId}
                  onChange={(e) => setWorkOrderId(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-900 w-full focus:outline-none focus:border-[#714B67]"
                />
              </div>
              <div>
                <label className="text-[11px] font-bold text-slate-700 block mb-1">Operator Name</label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-900 w-full focus:outline-none focus:border-[#714B67]"
                />
              </div>
            </div>
          </div>

          {/* Step 2 — Evidence Capture / Upload */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                <span className="bg-[#714B67] text-white w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold">2</span>
                Capture Evidence Photographs
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">Front / Rear Surface</span>
            </div>

            {/* Scenario Quick Selection Tabs */}
            <div>
              <label className="text-[11px] font-bold text-slate-700 block mb-2">
                Option A: Select Pre-Built Test Scenario
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {scenarios
                  .filter((sc) => sc.product_id === selectedProductId)
                  .map((sc) => {
                    const isSelected = selectedScenarioId === sc.id;
                    return (
                      <button
                        key={sc.id}
                        type="button"
                        onClick={() => handleSelectScenario(sc)}
                        className={`p-2.5 rounded-xl text-left text-xs border transition-all ${
                          isSelected
                            ? "bg-[#F3EDF2] border-[#714B67] text-[#714B67] font-bold shadow-xs"
                            : "bg-slate-50 border-slate-200 hover:border-slate-300 text-slate-700"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="line-clamp-1">{sc.name}</span>
                          <span className="text-[10px] font-mono uppercase bg-slate-200 px-1.5 py-0.5 rounded text-slate-800 font-bold">
                            {sc.expected_status}
                          </span>
                        </div>
                      </button>
                    );
                  })}
              </div>
            </div>

            {/* Custom File Upload Dropzone */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-bold text-slate-700 block">
                  Option B: Upload Physical Photo Files
                </label>
                <div className="flex items-center gap-2 text-[11px] text-slate-600">
                  <span>Photo Angle:</span>
                  <select
                    value={selectedViewAngle}
                    onChange={(e) => setSelectedViewAngle(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded px-2 py-0.5 text-xs text-slate-900 font-mono font-semibold"
                  >
                    <option value="front">Front Surface</option>
                    <option value="back">Rear Surface</option>
                    <option value="side">Side Surface</option>
                  </select>
                </div>
              </div>

              <label className={`border-2 border-dashed rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                uploadedFiles.length > 0 ? "border-[#714B67] bg-[#F3EDF2]/50" : "border-slate-200 hover:border-slate-400 bg-slate-50"
              }`}>
                <Upload className="w-8 h-8 text-[#714B67] mb-2" />
                <span className="text-xs font-bold text-slate-900">
                  {uploadedFiles.length > 0 ? `${uploadedFiles.length} File(s) Selected` : "Drag and drop custom product photos here"}
                </span>
                <span className="text-[11px] text-slate-500 mt-1">Supports JPG, PNG, WEBP up to 10MB</span>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Right Column — Rule Checklist & Run CTA */}
        <div className="space-y-6">
          {/* Applicable Rules Checklist */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
              <FileCheck2 className="w-4 h-4 text-[#714B67]" />
              Prep Requirements ({selectedProduct?.requirements.length || 0})
            </h3>

            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {selectedProduct?.requirements.map((r) => (
                <div key={r.id} className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 flex items-start justify-between gap-2">
                  <div>
                    <div className="font-bold text-xs text-slate-900">{r.name}</div>
                    <div className="text-[10px] text-slate-500 leading-tight mt-0.5">{r.description}</div>
                  </div>
                  <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full shrink-0 font-bold ${
                    r.visually_verifiable
                      ? "bg-[#E6F6F6] text-[#00A09D] border border-[#BCE7E6]"
                      : "bg-amber-100 text-amber-800 border border-amber-300"
                  }`}>
                    {r.visually_verifiable ? "Verifiable" : "Physical Test"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Inspection Stage Progress or Run Button */}
          {isInspecting ? (
            <div className="bg-white border border-[#714B67]/30 rounded-2xl p-5 space-y-3 shadow-md">
              <div className="text-xs font-extrabold text-[#714B67] flex items-center gap-2">
                <span className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-[#714B67] border-t-transparent"></span>
                Prep Manager Inspecting...
              </div>

              <div className="space-y-2 text-xs">
                <div className={`flex items-center gap-2 ${inspectStage >= 1 ? "text-[#00A09D] font-bold" : "text-slate-400"}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Image Quality & Coverage Agent</span>
                </div>
                <div className={`flex items-center gap-2 ${inspectStage >= 2 ? "text-[#00A09D] font-bold" : "text-slate-400"}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Packaging Enclosure & Seal Agent</span>
                </div>
                <div className={`flex items-center gap-2 ${inspectStage >= 3 ? "text-[#00A09D] font-bold" : "text-slate-400"}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Barcode Geometry & UPC Agent</span>
                </div>
                <div className={`flex items-center gap-2 ${inspectStage >= 4 ? "text-[#00A09D] font-bold" : "text-slate-400"}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>OCR Suffocation Text Agent</span>
                </div>
                <div className={`flex items-center gap-2 ${inspectStage >= 5 ? "text-[#714B67] font-bold" : "text-slate-400"}`}>
                  <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                  <span>Decision Agent Synthesizing...</span>
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={handleStartInspection}
              className="w-full btn-odoo font-bold py-3.5 px-4 rounded-2xl text-sm shadow-md flex items-center justify-center gap-2 transition-all hover:scale-[1.01]"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Run Visual Prep Inspection</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
