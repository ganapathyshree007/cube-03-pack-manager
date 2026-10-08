import React, { useState, useRef, useEffect } from "react";
import { createRoot } from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  PackageCheck,
  ScanLine,
  ClipboardList,
  Boxes,
  History,
  ArrowUpRight,
  Plus,
  Upload,
  ShieldCheck,
  AlertTriangle,
  CircleHelp,
  ChevronRight,
  Download,
  RefreshCw,
  X,
  LayoutDashboard,
  Check,
} from "lucide-react";
import { z } from "zod";
import { api, authorizedFetch, type RecordRow } from "./api";
import "@fontsource-variable/inter";
import "./styles.css";
import { AuthGate } from "./auth";
import { Landing } from "./landing";
import { CameraCapture } from "./camera";

const client = new QueryClient({ defaultOptions: { queries: { retry: 1 } } });
const labels: Record<string, string> = {
  seal: "Seal approved",
  stop_and_fix: "Stop & fix",
  uncertain: "Uncertain",
  pending: "Pending review",
  draft: "Awaiting capture",
  queued: "Queued",
  running: "Inspecting",
};
const formatDate = (value: string) =>
  new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

function Badge({ value }: { value: string }) {
  const Icon =
    value === "seal"
      ? ShieldCheck
      : value === "stop_and_fix"
        ? AlertTriangle
        : CircleHelp;
  return (
    <span className={`badge ${value}`}>
      <Icon size={14} />
      {labels[value] || value}
    </span>
  );
}

function App() {
  const cache = useQueryClient();
  const [page, setPage] = useState("Overview");
  const [active, setActive] = useState<string | null>(
    localStorage.getItem("pack-attempt"),
  );
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<"order" | "product" | null>(null);
  const [editing, setEditing] = useState<RecordRow | null>(null);
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    setOffset(0);
    setSearch("");
  }, [page]);
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => api("/me"),
  });
  const { data: summary = { total: 0, approved: 0, exceptions: 0 } } = useQuery(
    {
      queryKey: ["summary"],
      queryFn: () => api("/summary"),
      refetchInterval: 5000,
    },
  );
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: () => api("/config"),
  });
  const { data: orders = [], error: orderError } = useQuery({
    queryKey: [
      "orders",
      page === "Orders" ? offset : 0,
      page === "Orders" || page === "Inspection" ? search : "",
    ],
    queryFn: () =>
      api<RecordRow[]>(
        `/orders?offset=${page === "Orders" ? offset : 0}&q=${encodeURIComponent(page === "Orders" || page === "Inspection" ? search : "")}`,
      ),
  });
  const { data: products = [] } = useQuery({
    queryKey: ["catalogue"],
    queryFn: () => api<RecordRow[]>("/catalogue"),
  });
  const { data: inspections = [] } = useQuery({
    queryKey: ["inspections", page, offset, search],
    queryFn: () =>
      api<RecordRow[]>(
        `/inspections?offset=${["History", "Exceptions"].includes(page) ? offset : 0}&q=${encodeURIComponent(["History", "Exceptions"].includes(page) ? search : "")}&exceptions=${page === "Exceptions"}`,
      ),
    refetchInterval: 5000,
  });
  const { data: attempt } = useQuery({
    queryKey: ["attempt", active],
    queryFn: () => api<RecordRow>(`/inspections/${active}`),
    enabled: !!active,
    refetchInterval: 2000,
  });
  const [selectedOrder, setSelectedOrder] = useState("");
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [zoom, setZoom] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewCheck, setReviewCheck] = useState<string | null>(null);
  const current = attempt?.data;
  const reviewedVerdicts = Object.fromEntries(
    (current?.result?.checks || []).map((c: any) => [
      c.check_key,
      c.verdict.toLowerCase(),
    ]),
  );
  for (const entry of current?.check_overrides || [])
    reviewedVerdicts[entry.check_key] = entry.to_verdict;
  const reviewedDecision = current?.check_overrides?.length
    ? Object.values(reviewedVerdicts).includes("fail")
      ? "stop_and_fix"
      : Object.values(reviewedVerdicts).includes("uncertain")
        ? "uncertain"
        : "seal"
    : current?.result?.decision;
  const exceptions = inspections.filter(
    (r) =>
      r.data.status === "pending" ||
      ["uncertain", "stop_and_fix"].includes(
        r.data.review_decision || r.data.result?.decision,
      ),
  );
  const refresh = () => cache.invalidateQueries();
  const actionInFlight = useRef(false);
  function submissionKey(attemptId: string) {
    const storageKey = `pack-submission-${attemptId}`;
    const existing = localStorage.getItem(storageKey);
    if (existing) return existing;
    const key = crypto.randomUUID();
    localStorage.setItem(storageKey, key);
    return key;
  }
  async function action(fn: () => Promise<void>) {
    // State updates alone do not synchronously guard rapid duplicate clicks.
    if (actionInFlight.current) return;
    actionInFlight.current = true;
    setBusy(true);
    setMessage("");
    try {
      await fn();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      await refresh();
      actionInFlight.current = false;
      setBusy(false);
    }
  }
  function openAttempt(id: string) {
    setActive(id);
    localStorage.setItem("pack-attempt", id);
    setPage("Inspection");
    setPhoto(null);
    setPreview("");
  }
  async function inspect() {
    await action(async () => {
      if (!photo || !selectedOrder)
        throw new Error("Choose an order and a photograph first.");
      const payload: any = { order_id: selectedOrder };
      if (selectedProductIds.length > 0) {
        payload.selected_product_ids = selectedProductIds;
      }
      const row = await api<RecordRow>("/inspections", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      openAttempt(row.id);
      const fd = new FormData();
      fd.append("file", photo);
      const image = await api("/images", { method: "POST", body: fd });
      await api(`/inspections/${row.id}/submit`, {
        method: "POST",
        headers: { "Idempotency-Key": submissionKey(row.id) },
        body: JSON.stringify({ image_id: image.id }),
      });
    });
  }
  async function retake() {
    await action(async () => {
      const row = await api<RecordRow>("/inspections", {
        method: "POST",
        body: JSON.stringify({
          order_id: current.order_id,
          previous_attempt_id: active,
        }),
      });
      openAttempt(row.id);
      setSelectedOrder(current.order_id);
    });
  }
  async function submitRetake() {
    await action(async () => {
      if (!photo) throw new Error("Upload a new photograph.");
      const fd = new FormData();
      fd.append("file", photo);
      const image = await api("/images", { method: "POST", body: fd });
      await api(`/inspections/${active}/submit`, {
        method: "POST",
        headers: { "Idempotency-Key": submissionKey(active!) },
        body: JSON.stringify({ image_id: image.id }),
      });
      setPhoto(null);
      setPreview("");
    });
  }
  function choosePhoto(file?: File) {
    if (!file) return;
    if (preview) URL.revokeObjectURL(preview);
    setPhoto(file);
    setPreview(URL.createObjectURL(file));
  }
  const nav = [
    { name: "Overview", icon: LayoutDashboard },
    { name: "Inspection", icon: ScanLine },
    { name: "Orders", icon: ClipboardList },
    { name: "Catalogue", icon: Boxes },
    { name: "History", icon: History },
    { name: "Exceptions", icon: AlertTriangle },
  ];
  const { data: savedImage = "" } = useQuery({
    queryKey: ["image", current?.image_id],
    enabled: !!current?.image_id,
    queryFn: async () => {
      const r = await authorizedFetch(`/api/v1/images/${current.image_id}`);
      if (!r.ok) throw new Error("Evidence unavailable");
      return URL.createObjectURL(await r.blob());
    },
    staleTime: Infinity,
  });
  const imageUrl = preview || savedImage;
  const expected =
    current?.order_snapshot || orders.find((o) => o.id === selectedOrder)?.data;
  return (
    <div className="shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setPage("Overview");
          }}
        >
          <span className="brand-mark">
            <PackageCheck size={25} />
          </span>
          <span>
            Pack<span className="brand-light">Manager</span>
            <small>THE PACKING WORKSPACE</small>
          </span>
        </a>
        <div className="workspace-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {nav.map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={page === name ? "nav active" : "nav"}
              onClick={() => {
                setPage(name);
                setSearch("");
              }}
            >
              <Icon size={18} />
              <span>{name}</span>
              {name === "Exceptions" && exceptions.length > 0 && (
                <span className="nav-count">{exceptions.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="mono">CUBE / PCK</div>
          <p>
            One box.
            <br />A clear record.
          </p>
          <span className="environment">
            {config?.auth_mode === "local"
              ? "Local development"
              : "Authenticated workspace"}
          </span>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            Operations <ChevronRight size={13} /> {page}
          </span>
          <span className="connection">
            <span className={orderError ? "dot warning" : "dot"} />
            {orderError ? "Database disconnected" : "Pack station"}
            {me?.role === "demo" && (
              <button
                className="text-button"
                onClick={async () => {
                  await api("/demo-session", { method: "DELETE" });
                  localStorage.removeItem("pack-attempt");
                  location.reload();
                }}
              >
                End demo
              </button>
            )}
            <span className="avatar">PM</span>
          </span>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">ORDER VERIFICATION BEFORE SEALING</div>
              <h1>
                {page === "Overview"
                  ? "Every order, accounted for."
                  : page === "Inspection"
                    ? "Inspect the open box."
                    : page}
              </h1>
              <p>
                {page === "Overview"
                  ? "A clear view of what is ready, what needs attention, and why."
                  : page === "Inspection"
                    ? "Expose every item and its identifying label. Keep the entire box in view."
                    : page === "Catalogue"
                      ? "Define the products and variants your station can verify."
                      : page === "Orders"
                        ? "The expected contents. Saved before the inspection begins."
                        : "A traceable record of each attempt and decision."}
              </p>
            </div>
            {page !== "Inspection" && (
              <button
                className="primary"
                onClick={() => {
                  setActive(null);
                  localStorage.removeItem("pack-attempt");
                  setPage("Inspection");
                }}
              >
                <ScanLine size={17} /> New inspection
              </button>
            )}
          </div>
          {message && (
            <div role="alert" className="notice error">
              {message}
              <button aria-label="Dismiss error" onClick={() => setMessage("")}>
                <X size={17} />
              </button>
            </div>
          )}
          {orderError && (
            <div role="alert" className="notice error">
              Database unavailable. Start PostgreSQL and run the migration to
              save orders and inspections.
              <button onClick={() => refresh()}>
                <RefreshCw size={16} /> Retry
              </button>
            </div>
          )}
          {!config?.model_configured && (
            <div className="notice model">
              <CircleHelp size={18} />
              <div>
                <strong>Model not configured</strong>
                <span>
                  {" "}
                  You can prepare orders and save evidence. Live inspections
                  stay pending until Azure is connected.
                </span>
              </div>
            </div>
          )}
          {page === "Overview" && (
            <>
              <section className="setup-guide" aria-label="Workspace setup">
                <h2>Build your first real inspection</h2>
                <p>
                  Use your own products and photographs. Records labelled DEMO
                  ONLY are fictional examples, not inspection evidence.
                </p>
                <div className="setup-steps">
                  <button onClick={() => setPage("Catalogue")}>
                    <strong>01 · Prepare the catalogue</strong>
                    <span>
                      {products.length} active products. Add real SKUs and
                      reference photographs.
                    </span>
                  </button>
                  <button onClick={() => setPage("Orders")}>
                    <strong>02 · Define the order</strong>
                    <span>
                      Save expected quantities and a unique physical unit ID.
                    </span>
                  </button>
                  <button
                    onClick={() => {
                      setActive(null);
                      localStorage.removeItem("pack-attempt");
                      setPage("Inspection");
                    }}
                  >
                    <strong>03 · Capture and inspect</strong>
                    <span>
                      {config?.model_configured
                        ? "Capture all items and labels in one clear view."
                        : "Capture evidence for review. Model connection is still required for AI inspection."}
                    </span>
                  </button>
                </div>
              </section>
              <section className="metrics" aria-label="Inspection totals">
                <Metric
                  label="Recorded inspections"
                  value={summary.total}
                  note="Saved attempts"
                />
                <Metric
                  label="Seal approved"
                  value={summary.approved}
                  note="Original AI decisions"
                />
                <Metric
                  label="Needs attention"
                  value={summary.exceptions}
                  note="Pending and exception cases"
                />
              </section>
              <section className="panel">
                <div className="panel-title">
                  <div>
                    <h2>Recent inspections</h2>
                    <p>Evidence stays with every decision.</p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setPage("History")}
                  >
                    View history <ArrowUpRight size={16} />
                  </button>
                </div>
                <InspectionTable
                  rows={inspections.slice(0, 5)}
                  open={openAttempt}
                />
              </section>
              <div className="bottom-grid">
                <section className="capture-guide">
                  <div className="eyebrow">
                    A GOOD CAPTURE IS THE FIRST CHECK
                  </div>
                  <h2>Make the contents visible.</h2>
                  <p>
                    Lay items in one layer. Separate repeated units. Turn size
                    and variant labels toward the camera.
                  </p>
                  <div className="guide-step">
                    <span>01</span> Open box, clear light
                  </div>
                  <div className="guide-step">
                    <span>02</span> Every unit visible
                  </div>
                  <div className="guide-step">
                    <span>03</span> Labels facing up
                  </div>
                </section>
                <section className="panel evaluation">
                  <div className="outline-icon">
                    <ShieldCheck />
                  </div>
                  <h2>Measured, not assumed.</h2>
                  <p>
                    No evaluation run yet. Accuracy will be reported after
                    independent human labeling and a held-out evaluation.
                  </p>
                  <span className="small-tag">EVALUATION PENDING</span>
                </section>
              </div>
            </>
          )}
          {page === "Inspection" && (
            <div className="inspection-grid">
              <section className="panel photo-panel">
                <div className="panel-title">
                  <h2>Box evidence</h2>
                  <span className="small-tag">PRIMARY COUNTING VIEW</span>
                </div>
                {imageUrl ? (
                  <div style={{ position: "relative", width: "100%" }}>
                    <button
                      className="photo-button"
                      onClick={() => setZoom(true)}
                      aria-label="Enlarge box photograph"
                    >
                      <img
                        src={imageUrl}
                        alt="Open box evidence for this inspection"
                      />
                      <span>Click to enlarge</span>
                    </button>
                    {current?.result?.observation?.instances?.map((inst: any) => {
                      if (!inst.bounding_box || inst.bounding_box.length !== 4) return null;
                      const [ymin, xmin, ymax, xmax] = inst.bounding_box;
                      return (
                        <div
                          key={inst.instance_id}
                          style={{
                            position: "absolute",
                            top: `${ymin * 100}%`,
                            left: `${xmin * 100}%`,
                            width: `${(xmax - xmin) * 100}%`,
                            height: `${(ymax - ymin) * 100}%`,
                            border: "2px solid #3b82f6",
                            boxShadow: "0 0 8px rgba(59, 130, 246, 0.5)",
                            backgroundColor: "rgba(59, 130, 246, 0.12)",
                            pointerEvents: "none",
                            borderRadius: "4px",
                            zIndex: 10,
                          }}
                        >
                          <span
                            style={{
                              position: "absolute",
                              top: "2px",
                              left: "2px",
                              fontSize: "11px",
                              fontWeight: 600,
                              background: "#1e40af",
                              color: "#ffffff",
                              padding: "2px 6px",
                              borderRadius: "3px",
                              fontFamily: "monospace",
                            }}
                          >
                            {inst.instance_id}: {inst.candidates?.join("/") || "unmatched"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <label
                    className="dropzone"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      choosePhoto(e.dataTransfer.files[0]);
                    }}
                  >
                    <div className="capture-corners">
                      <ScanLine size={54} strokeWidth={1} />
                    </div>
                    <h2>A clear photo. A defensible decision.</h2>
                    <p>
                      Drop an open-box photograph here,
                      <br />
                      or choose a photo from your device.
                    </p>
                    <span className="secondary">
                      <Upload size={16} /> Choose photograph
                    </span>
                    <input
                      aria-label="Box photograph"
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={(e) => choosePhoto(e.target.files?.[0])}
                    />
                    <small>JPG, PNG or WebP · up to 10 MB</small>
                  </label>
                )}
                {(!current || current.status === "draft") && (
                  <CameraCapture onCapture={choosePhoto} />
                )}
                {imageUrl && (!current || current.status === "draft") && (
                  <label className="replace-photo">
                    Replace photograph
                    <input
                      aria-label="Replace photograph"
                      type="file"
                      accept="image/*"
                      onChange={(e) => choosePhoto(e.target.files?.[0])}
                    />
                  </label>
                )}
                <div className="photo-footer">
                  <ShieldCheck size={16} /> Original evidence is saved. No
                  invented boxes or confidence scores.
                </div>
              </section>
              <div className="inspection-side">
                <section className="panel order-panel">
                  <div className="panel-title">
                    <h2>Expected order</h2>
                    <ClipboardList size={18} />
                  </div>
                  {!current ? (
                    <label>
                      Choose order
                      <input
                        aria-label="Find order for inspection"
                        placeholder="Search order or unit…"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                      <select
                        value={selectedOrder}
                        onChange={(e) => setSelectedOrder(e.target.value)}
                      >
                        <option value="">Select an order</option>
                        {orders.map((o) => (
                          <option key={o.id} value={o.id}>
                            {o.data.reference}
                          </option>
                        ))}
                      </select>
                    </label>
                  ) : (
                    <div className="order-ref mono">{expected?.reference}</div>
                  )}
                  {expected ? (
                    <>
                      <div className="unit-id mono">{expected.unit_id}</div>
                      <table>
                        <thead>
                          <tr>
                            <th>SKU / variant</th>
                            <th className="number">Qty</th>
                          </tr>
                        </thead>
                        <tbody>
                          {expected.lines.map((l: any) => (
                            <tr key={l.sku}>
                              <td className="mono">{l.sku}</td>
                              <td className="number mono">{l.quantity}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  ) : (
                    <p className="muted">
                      No order selected. Create an order to define the expected
                      items.
                    </p>
                  )}
                  {!current && products.length > 0 && (
                    <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border)" }}>
                      <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--muted-foreground)", marginBottom: "0.4rem", textTransform: "uppercase" }}>
                        Selected Product Identities (Max 4)
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                        {products.map((p) => {
                          const selected = selectedProductIds.includes(p.id);
                          return (
                            <button
                              key={p.id}
                              type="button"
                              style={{
                                cursor: "pointer",
                                background: selected ? "#2563eb" : "var(--muted, #f1f5f9)",
                                color: selected ? "#ffffff" : "var(--foreground, #0f172a)",
                                border: "1px solid " + (selected ? "#2563eb" : "var(--border, #cbd5e1)"),
                                padding: "2px 8px",
                                borderRadius: "4px",
                                fontSize: "12px",
                              }}
                              onClick={() => {
                                if (selected) {
                                  setSelectedProductIds(selectedProductIds.filter((id) => id !== p.id));
                                } else if (selectedProductIds.length < 4) {
                                  setSelectedProductIds([...selectedProductIds, p.id]);
                                }
                              }}
                            >
                              {p.data.sku}
                            </button>
                          );
                        })}
                      </div>
                      <small className="muted" style={{ display: "block", marginTop: "0.4rem", fontSize: "11px" }}>
                        {selectedProductIds.length === 0
                          ? "Default: Snapshots active catalogue products"
                          : `${selectedProductIds.length}/4 selected for this attempt`}
                      </small>
                    </div>
                  )}
                  <button
                    className="text-button"
                    onClick={() => setForm("order")}
                  >
                    <Plus size={15} /> Create order
                  </button>
                </section>

                <section className="panel readiness-panel">
                  <div className="panel-title">
                    <h2>Readiness Prerequisites</h2>
                    <ShieldCheck size={18} />
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Order validity:</span>
                      <strong style={{ color: selectedOrder || current?.order_id ? "#16a34a" : "#dc2626" }}>
                        {selectedOrder || current?.order_id ? "PASS" : "FAIL (Select order)"}
                      </strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Photograph evidence:</span>
                      <strong style={{ color: photo || current?.image_id ? "#16a34a" : "#dc2626" }}>
                        {photo || current?.image_id ? "PASS" : "FAIL (Upload photo)"}
                      </strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Catalogue selection (≤4):</span>
                      <strong style={{ color: selectedProductIds.length <= 4 ? "#16a34a" : "#dc2626" }}>
                        {selectedProductIds.length <= 4 ? `PASS (${selectedProductIds.length || (current?.catalogue_snapshot?.length ?? products.length)} SKUs)` : "FAIL (>4 selected)"}
                      </strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Vision provider:</span>
                      <strong style={{ color: config?.model_configured ? "#16a34a" : "#ca8a04" }}>
                        {config?.model_configured ? "PASS (Configured)" : "UNCONFIGURED"}
                      </strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Model call budget:</span>
                      <strong style={{ color: "#16a34a" }}>
                        PASS (1 per attempt)
                      </strong>
                    </div>
                  </div>
                </section>

                <section className="panel decision-panel" aria-live="polite">
                  <div className="eyebrow">INSPECTION DECISION</div>
                  {current ? (
                    <>
                      <Badge value={reviewedDecision || current.status} />
                      <p>
                        {current.reason ||
                          (reviewedDecision === "seal"
                            ? "All required checks pass under the capture protocol. Approval does not physically seal the box."
                            : reviewedDecision === "stop_and_fix"
                              ? "A supported discrepancy needs correction. Keep unresolved checks in view."
                              : reviewedDecision === "uncertain"
                                ? "Evidence is insufficient. Expose the unclear item or ask a supervisor."
                                : "Evidence and processing status are saved with this attempt.")}
                      </p>
                      {current.superseded_by && (
                        <div className="notice">
                          Superseded by a new capture. This result is
                          historical.
                        </div>
                      )}
                      {current.overrides?.length > 0 && (
                        <div className="human-outcome">
                          <strong>
                            Human decision:{" "}
                            {labels[current.overrides.at(-1).new_outcome]}
                          </strong>
                          <p>{current.overrides.at(-1).reason}</p>
                          <small>By {current.overrides.at(-1).actor}</small>
                        </div>
                      )}
                      {current.status === "draft" ? (
                        <button
                          className="primary full"
                          disabled={busy || !photo}
                          onClick={submitRetake}
                        >
                          <Upload size={16} /> Save new capture
                        </button>
                      ) : (
                        <>
                          <button
                            className="secondary full"
                            disabled={busy || !!current.superseded_by}
                            onClick={retake}
                          >
                            <RefreshCw size={16} /> New capture / attempt
                          </button>
                          <button
                            className="text-button"
                            disabled={
                              me?.role !== "supervisor" ||
                              ["running", "queued"].includes(current.status) ||
                              !!current.superseded_by ||
                              !!current.check_overrides?.length
                            }
                            onClick={() => {
                              setReviewCheck(null);
                              setReviewOpen(true);
                            }}
                          >
                            Supervisor review <ArrowUpRight size={16} />
                          </button>
                        </>
                      )}
                      <button
                        className="text-button"
                        onClick={() =>
                          action(async () => {
                            const result = await api(
                              `/inspections/${active}/export`,
                            );
                            const url = URL.createObjectURL(
                              new Blob([JSON.stringify(result, null, 2)], {
                                type: "application/json",
                              }),
                            );
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `pack-${active}.json`;
                            a.click();
                            URL.revokeObjectURL(url);
                          })
                        }
                      >
                        <Download size={16} /> Export workspace JSON (legacy)
                      </button>
                      <button
                        className="text-button"
                        disabled={
                          !current.image_id ||
                          current.status === "draft" ||
                          !!current.overrides?.length
                        }
                        onClick={() =>
                          action(async () => {
                            const result = await api(
                              `/inspections/${active}/contract`,
                            );
                            const url = URL.createObjectURL(
                              new Blob([JSON.stringify(result, null, 2)], {
                                type: "application/json",
                              }),
                            );
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `pack-v1.1-${active}.json`;
                            a.click();
                            URL.revokeObjectURL(url);
                          })
                        }
                      >
                        <Download size={16} /> Export contract 1.1 JSON
                      </button>
                      <p className="micro">
                        Contract export needs a saved capture. Legacy
                        outcome-only reviews cannot be converted into per-check
                        evidence.
                      </p>
                      {me?.role === "demo" && (
                        <p className="micro">
                          Demo session: supervisor review is unavailable.
                        </p>
                      )}
                      {!current.superseded_by &&
                        me?.role !== "demo" &&
                        (current.overrides?.at(-1)?.new_outcome ||
                          reviewedDecision) === "seal" && (
                          <button
                            className="secondary full"
                            disabled={busy || !!current.packed_acknowledgement}
                            onClick={() =>
                              action(async () => {
                                await api(`/inspections/${active}/packed`, {
                                  method: "POST",
                                  body: JSON.stringify({
                                    expected_version: attempt?.version,
                                  }),
                                });
                              })
                            }
                          >
                            {current.packed_acknowledgement
                              ? "Operator acknowledged packed"
                              : "Acknowledge packed"}
                          </button>
                        )}
                      <p className="micro">
                        One inference call per unit. Further captures preserve
                        evidence for human review; they do not reset the model
                        budget.
                      </p>
                    </>
                  ) : (
                    <>
                      <h2>Ready when you are.</h2>
                      <p>
                        We compare supported observations against this order.
                        Unclear evidence stays uncertain.
                      </p>
                      <button
                        className="primary full"
                        disabled={busy || !photo || !selectedOrder}
                        onClick={inspect}
                      >
                        {busy
                          ? "Saving evidence…"
                          : config?.model_configured
                            ? "Start inspection"
                            : "Save for review"}
                        <ChevronRight size={17} />
                      </button>
                    </>
                  )}
                </section>
              </div>
              {current?.result && (
                <section className="panel full-span">
                  <div className="panel-title">
                    <h2>Checks & evidence</h2>
                    <span className="small-tag">ORIGINAL AUTOMATED RESULT</span>
                  </div>
                  <div className="checks">
                    {current.result.checks.map((c: any) => (
                      <div className="check-row" key={c.check_key}>
                        <span className={`verdict ${c.verdict}`}>
                          {c.verdict === "PASS" ? (
                            <Check size={18} />
                          ) : (
                            <CircleHelp size={18} />
                          )}
                        </span>
                        <div>
                          <strong>{c.check_key.replaceAll("_", " ")}</strong>
                          <p>{c.detail}</p>
                        </div>
                        <span className="mono">{c.verdict}</span>
                        <button
                          className="text-button"
                          disabled={
                            me?.role !== "supervisor" ||
                            !!current.superseded_by ||
                            !!current.overrides?.length ||
                            !!current.packed_acknowledgement
                          }
                          onClick={() => {
                            setReviewCheck(c.check_key);
                            setReviewOpen(true);
                          }}
                        >
                          Review {c.check_key.replaceAll("_", " ")}
                        </button>
                      </div>
                    ))}
                  </div>
                  {!!current.check_overrides?.length && (
                    <div className="notice">
                      <strong>Human check reviews</strong>
                      {current.check_overrides.map((entry: any, i: number) => (
                        <p key={i}>
                          {entry.check_key.replaceAll("_", " ")}:{" "}
                          {entry.from_verdict} → {entry.to_verdict}.{" "}
                          {entry.reason} — {entry.by}
                        </p>
                      ))}
                    </div>
                  )}
                  <table>
                    <thead>
                      <tr>
                        <th>SKU</th>
                        <th>Expected</th>
                        <th>Model-reported visible quantity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {current.result.observed.map((o: any) => (
                        <tr key={o.sku}>
                          <td>{o.sku}</td>
                          <td>{o.expected}</td>
                          <td>
                            {o.exact_count_known
                              ? o.visible_lower_bound
                              : `At least ${o.visible_lower_bound}; exact count unknown`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {current.result.observation && (
                    <div className="notice">
                      <h3>What the model reported</h3>
                      <p>
                        These are model claims about the primary photograph.
                        Catalogue references are never package contents. Human
                        reviews are recorded separately.
                      </p>
                      {["ollama", "gemini"].includes(current.result.provenance?.provider) && (
                        <p>
                          <strong>
                            Experimental model: identification and counting are
                            not validated. Check every claim against the
                            photograph.
                          </strong>
                        </p>
                      )}
                      <ul>
                        {current.result.observation.instances.map(
                          (item: any) => (
                            <li key={item.instance_id}>
                              <strong>
                                {item.candidates.length
                                  ? item.candidates.join(" / ")
                                  : "Unknown product"}
                              </strong>
                              {item.identity_verified
                                ? " — model claims identity"
                                : " — identity unresolved"}
                              . {item.evidence}
                              {item.occlusion && (
                                <span> Obstruction: {item.occlusion}.</span>
                              )}
                            </li>
                          ),
                        )}
                      </ul>
                      {!!current.result.observation.unresolved.length && (
                        <p>
                          <strong>Needs review:</strong>{" "}
                          {current.result.observation.unresolved.join("; ")}
                        </p>
                      )}
                    </div>
                  )}
                  <details>
                    <summary>Observation and model provenance</summary>
                    <pre>
                      {JSON.stringify(
                        {
                          observation: current.result.observation,
                          provenance: current.result.provenance,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                </section>
              )}
              {active && <Timeline id={active} />}
            </div>
          )}
          {(page === "Orders" || page === "Catalogue") && (
            <section className="panel">
              <div className="panel-title">
                <h2>
                  {page === "Orders" ? "Order book" : "Product catalogue"}
                </h2>
                <button
                  className="secondary"
                  onClick={() => {
                    setEditing(null);
                    setForm(page === "Orders" ? "order" : "product");
                  }}
                >
                  <Plus size={16} />{" "}
                  {page === "Orders" ? "Create order" : "Add product"}
                </button>
              </div>
              <div className="search-row">
                {page === "Orders" && (
                  <label className="import-label">
                    Import order CSV
                    <input
                      type="file"
                      accept=".csv,text/csv"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file)
                          action(async () => {
                            const f = new FormData();
                            f.append("file", file);
                            await api("/orders/import", {
                              method: "POST",
                              body: f,
                            });
                            setMessage("Orders imported successfully.");
                          });
                      }}
                    />
                  </label>
                )}
                <input
                  aria-label={`Search ${page.toLowerCase()}`}
                  placeholder={`Search ${page.toLowerCase()}…`}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              {page === "Orders" ? (
                <table>
                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Unit</th>
                      <th>Contents</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {orders
                      .filter((r) =>
                        JSON.stringify(r.data)
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                      )
                      .map((o) => (
                        <tr key={o.id}>
                          <td>
                            <strong>{o.data.reference}</strong>
                          </td>
                          <td className="mono">{o.data.unit_id}</td>
                          <td>
                            {o.data.lines
                              .map((l: any) => `${l.sku} × ${l.quantity}`)
                              .join(", ")}
                          </td>
                          <td>
                            <button
                              className="text-button"
                              onClick={() => {
                                setSelectedOrder(o.id);
                                setActive(null);
                                setPage("Inspection");
                              }}
                            >
                              Inspect <ChevronRight size={15} />
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>SKU</th>
                      <th>Variant / identity evidence</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {products
                      .filter((r) =>
                        JSON.stringify(r.data)
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                      )
                      .map((p) => (
                        <tr key={p.id}>
                          <td>
                            <strong>{p.data.name}</strong>
                          </td>
                          <td className="mono">{p.data.sku}</td>
                          <td>
                            {p.data.variant}
                            <small className="table-note">
                              {p.data.visual_description}
                            </small>
                          </td>
                          <td>
                            <button
                              className="text-button"
                              onClick={() => {
                                setEditing(p);
                                setForm("product");
                              }}
                            >
                              Edit
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
              {(page === "Orders" ? orders : products).length === 0 && (
                <Empty
                  title={
                    page === "Orders"
                      ? "Your order book starts here."
                      : "Give every variant an identity."
                  }
                  detail={
                    page === "Orders"
                      ? "Add catalogue products, then create the first order."
                      : "Add real product descriptions and distinguishing attributes. No merchandise is preloaded."
                  }
                />
              )}
            </section>
          )}
          {(page === "History" || page === "Exceptions") && (
            <section className="panel">
              <div className="search-row">
                <input
                  aria-label="Search inspection history"
                  placeholder="Search orders, units or outcomes…"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setOffset(0);
                  }}
                />
              </div>
              <div className="panel-title">
                <h2>
                  {page === "History"
                    ? "Saved inspection records"
                    : "Review queue"}
                </h2>
                <span className="small-tag">
                  {page === "History" ? inspections.length : exceptions.length}{" "}
                  RECORDS
                </span>
              </div>
              <InspectionTable
                rows={page === "History" ? inspections : exceptions}
                open={openAttempt}
              />
            </section>
          )}
          {["Orders", "History", "Exceptions"].includes(page) && (
            <div className="pagination">
              <button
                className="secondary"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - 50))}
              >
                Previous
              </button>
              <span>Page {Math.floor(offset / 50) + 1}</span>
              <button
                className="secondary"
                disabled={
                  (page === "Orders" ? orders : inspections).length < 50
                }
                onClick={() => setOffset(offset + 50)}
              >
                Next
              </button>
            </div>
          )}
          <footer>
            Pack Manager{" "}
            <span>
              Constrained AI inspection · Evidence contract provisional · No
              measured accuracy yet
            </span>
          </footer>
        </div>
      </main>
      {form && (
        <Modal
          close={() => {
            setForm(null);
            setEditing(null);
          }}
          label={form === "product" ? "Product details" : "Create order"}
        >
          <FormModal
            key={editing?.id || form}
            type={form}
            products={products}
            editing={editing}
            close={() => {
              setForm(null);
              setEditing(null);
            }}
            save={async (data: any) => {
              await api(
                form === "product"
                  ? `/catalogue${editing ? `/${editing.id}` : ""}`
                  : "/orders",
                {
                  method: editing ? "PUT" : "POST",
                  body: JSON.stringify(data),
                },
              );
              setForm(null);
              setEditing(null);
              await refresh();
            }}
          />
          {editing && me?.role === "supervisor" && (
            <button
              className="text-button"
              onClick={() => {
                if (
                  window.confirm(
                    "Archive this product? Saved inspection snapshots remain available.",
                  )
                )
                  action(async () => {
                    await api(`/catalogue/${editing.id}`, { method: "DELETE" });
                    setForm(null);
                    setEditing(null);
                  });
              }}
            >
              Archive product
            </button>
          )}
        </Modal>
      )}
      {reviewOpen && attempt && (
        <Modal close={() => setReviewOpen(false)} label="Supervisor review">
          <ReviewModal
            checkKey={reviewCheck}
            close={() => setReviewOpen(false)}
            save={async (decision, reason) => {
              await api(
                reviewCheck
                  ? `/inspections/${active}/checks/${reviewCheck}/review`
                  : `/inspections/${active}/review`,
                {
                  method: "POST",
                  body: JSON.stringify({
                    expected_version: attempt.version,
                    ...(reviewCheck ? { verdict: decision } : { decision }),
                    reason,
                  }),
                },
              );
              setReviewOpen(false);
              await refresh();
            }}
          />
        </Modal>
      )}
      {zoom && (
        <Modal
          close={() => setZoom(false)}
          label="Enlarged evidence"
          className="zoom"
        >
          <button
            className="close"
            aria-label="Close enlarged image"
            onClick={() => setZoom(false)}
          >
            <X />
          </button>
          <img src={imageUrl} alt="Enlarged original box evidence" />
        </Modal>
      )}
    </div>
  );
}
function Modal({
  children,
  close,
  label,
  className = "",
}: {
  children: React.ReactNode;
  close: () => void;
  label: string;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
    return () => ref.current?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      aria-label={label}
      className={className}
      onKeyDown={(e) => {
        if (e.key !== "Tab") return;
        const nodes = Array.from(
          ref.current?.querySelectorAll<HTMLElement>(
            "button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]",
          ) || [],
        );
        const first = nodes[0],
          last = nodes.at(-1);
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
    >
      {children}
    </dialog>
  );
}
function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: number;
  note: string;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className="mono">{value.toString().padStart(2, "0")}</strong>
      <small>{note}</small>
    </div>
  );
}
function Empty({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty">
      <div className="outline-icon">
        <PackageCheck size={26} />
      </div>
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}
function InspectionTable({
  rows,
  open,
}: {
  rows: RecordRow[];
  open: (id: string) => void;
}) {
  return rows.length ? (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Order / unit</th>
            <th>Captured</th>
            <th>Decision</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>
                <strong>{r.data.order_snapshot.reference}</strong>
                <small className="table-note mono">
                  {r.data.order_snapshot.unit_id}
                </small>
              </td>
              <td>{formatDate(r.created_at)}</td>
              <td>
                <Badge
                  value={
                    r.data.review_decision ||
                    r.data.result?.decision ||
                    r.data.status
                  }
                />
              </td>
              <td>
                <button
                  aria-label={`Open ${r.data.order_snapshot.reference}`}
                  className="icon-button"
                  onClick={() => open(r.id)}
                >
                  <ArrowUpRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <Empty
      title="No inspections yet."
      detail="Create an order and capture an open box. Your saved records will appear here."
    />
  );
}
function Timeline({ id }: { id: string }) {
  const { data = [] } = useQuery({
    queryKey: ["events", id],
    queryFn: () => api<any[]>(`/inspections/${id}/events`),
    refetchInterval: 3000,
  });
  return (
    <section className="panel full-span">
      <div className="panel-title">
        <h2>Attempt timeline</h2>
      </div>
      <div className="timeline">
        {data.map((e) => (
          <div key={e.id}>
            <span className="dot" />
            <strong>{e.data.name.replaceAll("_", " ")}</strong>
            <time>{formatDate(e.created_at)}</time>
            <p>
              {typeof e.data.detail === "string"
                ? e.data.detail
                : JSON.stringify(e.data.detail)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
function FormModal({
  type,
  products,
  editing,
  close,
  save,
}: {
  type: string;
  products: RecordRow[];
  editing: RecordRow | null;
  close: () => void;
  save: (data: any) => Promise<void>;
}) {
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        const f = new FormData(e.currentTarget);
        try {
          let data;
          if (type === "product") {
            data = {
              sku: f.get("sku"),
              name: f.get("name"),
              variant: f.get("variant"),
              visual_description: f.get("description"),
              barcodes: String(f.get("barcodes") || "")
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
              reference_image_ids: editing?.data.reference_image_ids || [],
            };
            const refs = f
              .getAll("reference_photos")
              .filter((x): x is File => x instanceof File && x.size > 0);
            if (refs.length + data.reference_image_ids.length > 4)
              throw new Error("Maximum four reference photos per SKU.");
            for (const photo of refs) {
              const upload = new FormData();
              upload.append("file", photo);
              const image = await api("/images", {
                method: "POST",
                body: upload,
              });
              data.reference_image_ids.push(image.id);
            }
            z.object({
              sku: z.string().min(1),
              name: z.string().min(1),
              visual_description: z.string().min(5),
            }).parse(data);
          } else {
            data = {
              reference: f.get("reference"),
              unit_id: f.get("unit"),
              channel: "3pl_client",
              lines: String(f.get("lines"))
                .split("\n")
                .filter(Boolean)
                .map((s) => {
                  const [sku, quantity] = s.trim().split(/[,\s]+/);
                  return { sku, quantity: Number(quantity) };
                }),
            };
            z.object({
              reference: z.string().min(1),
              unit_id: z.string().min(1),
              lines: z
                .array(
                  z.object({
                    sku: z.string().min(1),
                    quantity: z.number().int().positive(),
                  }),
                )
                .min(1),
            }).parse(data);
          }
          await save(data);
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setSaving(false);
        }
      }}
    >
      <div className="modal-header">
        <h2>
          {type === "product"
            ? editing
              ? "Edit product"
              : "Add product"
            : "Create order"}
        </h2>
        <button type="button" aria-label="Close form" onClick={close}>
          <X size={20} />
        </button>
      </div>
      {type === "product" ? (
        <>
          <label>
            SKU
            <input
              name="sku"
              required
              defaultValue={editing?.data.sku}
              placeholder="BOTTLE-750-BLUE"
            />
          </label>
          <label>
            Product name
            <input name="name" required defaultValue={editing?.data.name} />
          </label>
          <label>
            Variant
            <input
              name="variant"
              defaultValue={editing?.data.variant}
              placeholder="Blue / 750 ml"
            />
          </label>
          <label>
            Distinguishing visual attributes
            <textarea
              name="description"
              required
              minLength={5}
              defaultValue={editing?.data.visual_description}
            />
          </label>
          <label>
            Barcodes (comma separated)
            <input
              name="barcodes"
              defaultValue={editing?.data.barcodes.join(", ")}
            />
          </label>
          <label>
            Reference photos (up to four)
            <input
              type="file"
              name="reference_photos"
              accept="image/jpeg,image/png,image/webp"
              multiple
            />
          </label>
          <p className="micro">
            Descriptions provide candidates, not proof. Visually
            indistinguishable variants require a readable label or human review.
          </p>
        </>
      ) : (
        <>
          <label>
            Order reference
            <input name="reference" required placeholder="ORD-1042" />
          </label>
          <label>
            Physical unit ID
            <input name="unit" required placeholder="UNIT-1042" />
          </label>
          <p className="micro">
            Use the same ID across attempts for the same physical unit. One
            model-call budget is shared across those attempts.
          </p>
          <label>
            Order lines — one SKU and quantity per line
            <textarea
              name="lines"
              required
              placeholder={
                products.length
                  ? `${products[0].data.sku}, 1`
                  : "Add catalogue products first"
              }
            />
          </label>
          <p className="micro">
            Duplicate SKU lines are combined. Only positive whole quantities are
            accepted.
          </p>
        </>
      )}
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <button className="primary full" disabled={saving}>
        {saving
          ? "Saving…"
          : "Save " + (type === "product" ? "product" : "order")}
      </button>
    </form>
  );
}
function ReviewModal({
  close,
  save,
  checkKey,
}: {
  close: () => void;
  save: (decision: string, reason: string) => Promise<void>;
  checkKey?: string | null;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        setBusy(true);
        try {
          await save(String(f.get("decision")), String(f.get("reason")));
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <div className="modal-header">
        <h2>Supervisor review</h2>
        <button type="button" aria-label="Close review" onClick={close}>
          <X size={20} />
        </button>
      </div>
      <p>
        The original automated result remains unchanged. Your identity and
        reason are saved separately.
      </p>
      <label>
        {checkKey
          ? `Review: ${checkKey.replaceAll("_", " ")}`
          : "Human decision"}
        <select name="decision">
          <option value="uncertain">Uncertain</option>
          <option value={checkKey ? "fail" : "stop_and_fix"}>
            {checkKey ? "Fail" : "Stop & fix"}
          </option>
          <option value={checkKey ? "pass" : "seal"}>
            {checkKey ? "Pass confirmed by human" : "Seal approved by human"}
          </option>
        </select>
      </label>
      <label>
        Reason
        <textarea name="reason" required minLength={10} />
      </label>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <button className="primary full" disabled={busy}>
        Save attributed review
      </button>
    </form>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      {location.pathname === "/workspace" ||
      location.pathname.startsWith("/workspace/") ? (
        <AuthGate>
          <App />
        </AuthGate>
      ) : (
        <Landing />
      )}
    </QueryClientProvider>
  </React.StrictMode>,
);
