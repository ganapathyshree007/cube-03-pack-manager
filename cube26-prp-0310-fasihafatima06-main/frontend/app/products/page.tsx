"use client";
import React, { useEffect, useState } from "react";
import { Package, Plus, Trash2, CheckCircle2, ShieldCheck, Layers, FileCheck2, X, Sparkles } from "lucide-react";
import { fetchProducts, createProduct, deleteProduct } from "@/lib/api";
import { Product } from "@/lib/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // New Product Form State
  const [newProductId, setNewProductId] = useState<string>("");
  const [newProductName, setNewProductName] = useState<string>("");
  const [newAsin, setNewAsin] = useState<string>("");
  const [newSku, setNewSku] = useState<string>("");
  const [newCategory, setNewCategory] = useState<string>("Boxed Electronics");
  const [newDescription, setNewDescription] = useState<string>("");
  
  // Custom Rules State
  const [customRules, setCustomRules] = useState<any[]>([
    { name: "FNSKU Placement", category: "label", visually_verifiable: true, evaluation_type: "barcode_geometry", required_views: "front", description: "FNSKU label placed flat on outer package." },
    { name: "Original Barcode Covered", category: "barcode", visually_verifiable: true, evaluation_type: "barcode_visibility", required_views: "back", description: "Original UPC/EAN barcode fully covered." }
  ]);

  const loadProducts = () => {
    fetchProducts().then(setProducts).catch(console.error);
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleAddRuleRow = () => {
    setCustomRules([
      ...customRules,
      { name: "New Prep Check", category: "packaging", visually_verifiable: true, evaluation_type: "detect_polybag", required_views: "front", description: "Inspection requirement." }
    ]);
  };

  const handleRemoveRuleRow = (index: number) => {
    setCustomRules(customRules.filter((_, idx) => idx !== index));
  };

  const handleUpdateRuleRow = (index: number, field: string, value: any) => {
    const updated = [...customRules];
    updated[index][field] = value;
    setCustomRules(updated);
  };

  const handleCreateProductSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProductId || !newProductName) {
      alert("Please provide Product ID and Product Name.");
      return;
    }

    setIsSubmitting(true);
    try {
      await createProduct({
        id: newProductId.toUpperCase().trim(),
        name: newProductName.trim(),
        asin: newAsin.toUpperCase().trim() || "B00CUSTOM1",
        sku: newSku.toUpperCase().trim() || "SKU-CUSTOM1",
        category: newCategory,
        description: newDescription || "Custom inbound product item.",
        rules: customRules
      });
      setShowCreateModal(false);
      // Reset form
      setNewProductId("");
      setNewProductName("");
      setNewAsin("");
      setNewSku("");
      loadProducts();
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to create product.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteProduct = async (id: string) => {
    if (confirm(`Are you sure you want to delete product '${id}'?`)) {
      try {
        await deleteProduct(id);
        loadProducts();
      } catch (err) {
        console.error(err);
        alert("Failed to delete product.");
      }
    }
  };

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
              <Package className="w-5 h-5 text-[#714B67]" />
              Inbound Product Catalog & Rules Engine
            </h2>
            <span className="bg-[#F3EDF2] text-[#714B67] text-xs px-2.5 py-0.5 rounded-full font-bold border border-[#E4D6E2]">
              {products.length} Products Configured
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-xl">
            Add custom products, SKUs, ASINs, and define product-specific preparation rules dynamically.
          </p>
        </div>

        <button
          onClick={() => {
            setNewProductId(`PROD-${Math.floor(100 + Math.random() * 900)}`);
            setShowCreateModal(true);
          }}
          className="btn-odoo text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 shrink-0 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Add Custom Product & Rules</span>
        </button>
      </div>

      {/* Product Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((prod) => (
          <div
            key={prod.id}
            className="bg-white border border-slate-200 hover:border-[#714B67] rounded-2xl p-5 space-y-4 shadow-sm flex flex-col justify-between transition-all group"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs font-mono font-bold bg-[#F3EDF2] text-[#714B67] px-2.5 py-1 rounded-lg border border-[#E4D6E2]">
                  {prod.id}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-500 font-semibold">{prod.category}</span>
                  {!["DEMO-BOTTLE-001", "DEMO-ELEC-002", "DEMO-TOY-003"].includes(prod.id) && (
                    <button
                      onClick={() => handleDeleteProduct(prod.id)}
                      className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                      title="Delete Product"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              <div>
                <h3 className="font-bold text-slate-900 text-sm group-hover:text-[#714B67] transition-colors">
                  {prod.name}
                </h3>
                <div className="text-xs font-mono text-slate-500 mt-1 space-x-3">
                  <span>SKU: {prod.sku}</span>
                  <span>ASIN: {prod.asin}</span>
                </div>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">{prod.description}</p>
              </div>

              {/* Requirements List */}
              <div className="pt-2 space-y-2">
                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                  Prep Requirements ({prod.requirements.length})
                </span>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {prod.requirements.map((r) => (
                    <div key={r.id} className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-xs flex items-center justify-between">
                      <span className="text-slate-800 font-medium">{r.name}</span>
                      <span className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        r.visually_verifiable
                          ? "bg-[#E6F6F6] text-[#00A09D] border border-[#BCE7E6]"
                          : "bg-amber-50 text-amber-800 border border-amber-200"
                      }`}>
                        {r.visually_verifiable ? "Visually Verifiable" : "Physical Test"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* CREATE NEW PRODUCT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#714B67]" />
                <h3 className="font-extrabold text-slate-900 text-base">Create Custom Product & Preparation Rules</h3>
              </div>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600 p-1 text-lg font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateProductSubmit} className="space-y-4 text-xs">
              {/* Product Identifiers */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">Product ID (Unique)</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. DEMO-BOX-004"
                    value={newProductId}
                    onChange={(e) => setNewProductId(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono w-full focus:outline-none focus:border-[#714B67]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">Category</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Cardboard Packaging / Apparel"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 w-full focus:outline-none focus:border-[#714B67]"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-700 block mb-1">Product Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Custom Printed Shipping Box"
                  value={newProductName}
                  onChange={(e) => setNewProductName(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 w-full focus:outline-none focus:border-[#714B67]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">SKU</label>
                  <input
                    type="text"
                    placeholder="e.g. BOX-PRINT-01"
                    value={newSku}
                    onChange={(e) => setNewSku(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono w-full focus:outline-none focus:border-[#714B67]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">ASIN</label>
                  <input
                    type="text"
                    placeholder="e.g. B09CUSTOMBOX"
                    value={newAsin}
                    onChange={(e) => setNewAsin(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 font-mono w-full focus:outline-none focus:border-[#714B67]"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-700 block mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Details regarding item packaging and inbound fulfillment requirements..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 w-full focus:outline-none focus:border-[#714B67]"
                />
              </div>

              {/* Dynamic Rules Editor */}
              <div className="pt-2 space-y-2 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#714B67] uppercase tracking-wider">
                    Preparation Rules Schema ({customRules.length})
                  </label>
                  <button
                    type="button"
                    onClick={handleAddRuleRow}
                    className="text-xs text-[#714B67] hover:text-[#5B3B53] font-bold flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Rule</span>
                  </button>
                </div>

                <div className="space-y-2">
                  {customRules.map((rule, idx) => (
                    <div key={idx} className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <input
                          type="text"
                          value={rule.name}
                          placeholder="Rule Name (e.g. Polybag Presence)"
                          onChange={(e) => handleUpdateRuleRow(idx, "name", e.target.value)}
                          className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-900 font-semibold flex-1 focus:outline-none focus:border-[#714B67]"
                        />
                        <select
                          value={rule.category}
                          onChange={(e) => handleUpdateRuleRow(idx, "category", e.target.value)}
                          className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-[11px] text-slate-700 focus:outline-none"
                        >
                          <option value="packaging">Packaging</option>
                          <option value="label">Label</option>
                          <option value="barcode">Barcode</option>
                          <option value="warning">Warning</option>
                        </select>
                        <select
                          value={rule.evaluation_type}
                          onChange={(e) => handleUpdateRuleRow(idx, "evaluation_type", e.target.value)}
                          className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-[11px] text-slate-700 focus:outline-none"
                        >
                          <option value="barcode_geometry">Barcode Geometry</option>
                          <option value="barcode_visibility">Barcode Visibility</option>
                          <option value="detect_polybag">Polybag Presence</option>
                          <option value="detect_seal">Polybag Sealing</option>
                          <option value="ocr_warning">Suffocation Warning OCR</option>
                          <option value="physical_property">Physical Property (Lab)</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => handleRemoveRuleRow(idx)}
                          className="text-slate-400 hover:text-rose-600 p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-500 gap-4">
                        <label className="flex items-center gap-1.5 cursor-pointer font-medium">
                          <input
                            type="checkbox"
                            checked={rule.visually_verifiable}
                            onChange={(e) => handleUpdateRuleRow(idx, "visually_verifiable", e.target.checked)}
                            className="accent-[#714B67] rounded"
                          />
                          <span>Visually Verifiable</span>
                        </label>
                        <div className="flex items-center gap-2">
                          <span>Required Surface:</span>
                          <select
                            value={rule.required_views}
                            onChange={(e) => handleUpdateRuleRow(idx, "required_views", e.target.value)}
                            className="bg-white border border-slate-200 rounded px-1.5 py-0.5 text-[10px] text-slate-700 font-mono"
                          >
                            <option value="front">front</option>
                            <option value="back">back</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-xl font-bold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-odoo font-bold px-5 py-2 rounded-xl text-xs disabled:opacity-50 shadow-sm"
                >
                  {isSubmitting ? "Creating Product..." : "Save Product & Rules"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
