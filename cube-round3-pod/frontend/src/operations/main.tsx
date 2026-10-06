import React, { useEffect, useMemo, useRef, useState } from "react";
import { VisionEvidence } from "./vision";
import { createRoot } from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  Box,
  ArrowLeft,
  ArrowUpRight,
  LayoutGrid,
  ListChecks,
  Plus,
  RefreshCw,
  LogOut,
  Camera,
  Upload,
  X,
  Check,
  CircleHelp,
  Pause,
  ShieldCheck,
} from "lucide-react";
import "@fontsource-variable/inter";
import {
  OperationsApi,
  ApiError,
  explain,
  type Session,
  type Workflow,
  type Unit,
  type Run,
  type Context,
  type Manager,
  type Finding,
  type Verdict,
  type Product,
  type Permission,
} from "./api";
import "./operations.css";
import { CustomerPortal, CommerceAdmin, AnalyticsPanel } from "./commerce";
import { HostedLogin, hostedSignOut, useRuntime } from "./hosted";

const managers: Manager[] = [
  "receiving",
  "prep",
  "pack",
  "returns",
  "recovery",
];
const names: Record<string, string> = {
  receiving: "Receiving",
  prep: "Prep",
  pack: "Pack",
  returns: "Returns",
  recovery: "Recovery",
  fba: "FBA",
  merchant: "Merchant",
  "3pl": "3PL",
  unknown: "Route unknown",
  review_needed: "Needs review",
  blocked: "Blocked",
  completed: "Completed",
  queued: "Queued",
  running: "Processing",
  retryable: "Retry eligible",
  failed: "Failed",
  active: "Active",
  held: "On hold",
  cancelled: "Cancelled",
  pass: "Pass",
  fail: "Fail",
  uncertain: "Uncertain",
  pending_review: "Pending review",
  restock: "Restock",
  refurbish: "Refurbish",
  liquidate: "Liquidate",
  dispose: "Dispose",
};
const label = (s: string) => names[s.toLowerCase()] || s.replaceAll("_", " ");
const date = (s: string) =>
  new Date(s).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
const basis = (s: string) =>
  s === "fixture_human"
    ? "Synthetic · manual fixture"
    : s === "human"
      ? "Human inspection"
      : s === "deterministic_evidence_review"
        ? "Evidence review · no claim"
        : "No findings recorded";
function Badge({ value }: { value: string }) {
  return (
    <span className={"badge " + value.toLowerCase()}>
      <span aria-hidden="true" className="status-dot" />
      {label(value)}
    </span>
  );
}
function ErrorNotice({ error }: { error: unknown }) {
  const e = error instanceof ApiError ? error : new ApiError("NETWORK_ERROR");
  return (
    <div className="notice error" role="alert">
      <strong>{e.message}</strong>
      <small>Error code: {e.code}</small>
    </div>
  );
}
function Empty({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="empty">
      <Box size={26} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

function Login({
  onConnect,
}: {
  onConnect: (api: OperationsApi, session: Session) => void;
}) {
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [remember, setRemember] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const lock = useRef(false);
  async function connect(value: string, keep = remember) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(undefined);
    try {
      const api = new OperationsApi(value.trim());
      const session = await api.get<Session>(
        location.pathname === "/shop.html"
          ? "/v1/commerce/session"
          : "/v1/session",
      );
      if (!session.operator || !session.checks)
        throw new ApiError("INVALID_RESPONSE");
      if (keep) sessionStorage.setItem("cube-local-token", value.trim());
      else sessionStorage.removeItem("cube-local-token");
      setToken("");
      onConnect(api, session);
    } catch (e) {
      setError(e);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  useEffect(() => {
    const saved = sessionStorage.getItem("cube-local-token");
    if (saved) void connect(saved, true);
  }, []);
  return (
    <main className="login-shell">
      <header className="login-brand">
        <div className="wordmark">
          <Box /> CUBE <span>OPERATIONS</span>
        </div>
        <small>Private local workspace</small>
      </header>
      <section className="login-card">
        <p className="eyebrow">LOCAL DEVELOPMENT ACCESS</p>
        <h1>
          {location.pathname === "/shop.html"
            ? "Sign in to your customer account"
            : "Sign in to CUBE Operations"}
        </h1>
        <p>
          Use your private local account file or development token. Your account
          determines your organization and permissions.
        </p>
        {!!error && <ErrorNotice error={error} />}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void connect(token);
          }}
        >
          <label>
            Development token
            <input
              type={showToken ? "text" : "password"}
              autoComplete="off"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
          </label>
          <button
            type="button"
            aria-pressed={showToken}
            onClick={() => setShowToken(!showToken)}
          >
            {showToken ? "Hide token" : "Show token"}
          </button>
          <label className="check-line">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
            />
            Keep this session in this browser tab
          </label>
          <p className="hint">
            Optional. Uses tab session storage; signing out removes it.
            Otherwise your token stays in memory only.
          </p>
          <button className="primary" disabled={busy}>
            {busy ? "Connecting…" : "Connect locally"}
            <ArrowUpRight size={16} />
          </button>
        </form>
        <div className="divider">or use your private account file</div>
        <label className="file-button">
          Choose local account JSON
          <input
            aria-label="Local account file"
            type="file"
            accept=".json,application/json"
            disabled={busy}
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              try {
                if (file.size > 10000) throw new Error();
                const value = JSON.parse(await file.text());
                if (typeof value.token !== "string") throw new Error();
                void connect(value.token);
              } catch {
                setError(new ApiError("INVALID_INPUT"));
              }
              e.target.value = "";
            }}
          />
        </label>
        <p className="hint">
          Created by the local backend setup. The file is read in your browser;
          only the bearer token is sent to the local API. Never paste it into
          chat.
        </p>
      </section>
    </main>
  );
}

function AuthImage({ api, id }: { api: OperationsApi; id: string }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    let active = true;
    let object = "";
    setUrl("");
    setError(undefined);
    api
      .image(id)
      .then((blob) => {
        object = URL.createObjectURL(blob);
        if (active) setUrl(object);
        else URL.revokeObjectURL(object);
      })
      .catch((e) => {
        if (active) setError(e);
      });
    return () => {
      active = false;
      if (object) URL.revokeObjectURL(object);
    };
  }, [api, id]);
  return (
    <div className="evidence-photo">
      {error ? (
        <ErrorNotice error={error} />
      ) : url ? (
        <img src={url} alt={"Saved evidence " + id} />
      ) : (
        <span role="status">Loading authorized image…</span>
      )}
    </div>
  );
}

function Dialog({
  title,
  children,
  onClose,
  dirty = false,
  locked = false,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  dirty?: boolean;
  locked?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = React.useId();
  useEffect(() => {
    ref.current?.showModal();
    const unload = (event: BeforeUnloadEvent) => {
      if (dirty) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", unload);
    return () => window.removeEventListener("beforeunload", unload);
  }, [dirty]);
  const close = () => {
    if (locked) return;
    if (!dirty || window.confirm("Discard your unsaved input?")) onClose();
  };
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
    >
      <header className="dialog-header">
        <h2 id={titleId}>{title}</h2>
        <button
          className="icon-button"
          type="button"
          aria-label="Close dialog"
          disabled={locked}
          onClick={close}
        >
          <X size={20} />
        </button>
      </header>
      {children}
    </dialog>
  );
}

type Action =
  | { kind: "review"; run: Run }
  | {
      kind: "hold" | "cancel" | "resume" | "route" | "event" | "retry";
      run?: Run;
    };
function ReviewDialog({
  api,
  context,
  session,
  action,
  onClose,
  onSaved,
  onRefresh,
}: {
  api: OperationsApi;
  context: Context;
  session: Session;
  action: Action;
  onClose: () => void;
  onSaved: () => void;
  onRefresh: () => void;
}) {
  const [reason, setReason] = useState("");
  const [confirmation, setConfirmation] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const guard = useRef(false);
  const run = action.run;
  const [version, setVersion] = useState(
    run?.version || context.workflow.version,
  );
  const [findings, setFindings] = useState<Finding[]>(
    Array.from(
      new Set([
        ...(session.checks[run?.manager || "receiving"] || []),
        ...(context.workflow.data.policy?.stages.find(
          (s) => s.stage === run?.manager,
        )?.required_checks || []),
      ]),
    ).map((key) => ({
      check_key: key,
      verdict: "uncertain",
      detail: "",
    })),
  );
  const [images, setImages] = useState<string[]>([]);
  const [captured, setCaptured] = useState("");
  const [disposition, setDisposition] = useState("pending_review");
  const [route, setRoute] = useState("fba");
  const [source, setSource] = useState("");
  const [eventId, setEventId] = useState("");
  const [eventKind, setEventKind] = useState("return_received");
  const dirty =
    reason.length > 0 ||
    images.length > 0 ||
    findings.some((f) => !!f.detail) ||
    !!source ||
    !!eventId;
  const title =
    action.kind === "review"
      ? `Review ${label(run!.manager)}`
      : action.kind === "event"
        ? "Record an operational event"
        : action.kind === "route"
          ? "Resolve the route"
          : `${label(action.kind)} ${action.kind === "retry" ? "run" : "workflow"}`;
  async function save() {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setError(undefined);
    try {
      let path = "/v1/workflows/" + encodeURIComponent(context.workflow.id);
      let body: unknown;
      if (action.kind === "review") {
        path = "/v1/runs/" + encodeURIComponent(run!.id) + "/review";
        body = {
          expected_version: version,
          reason,
          findings,
          image_ids: images,
          captured_at: new Date(captured).toISOString(),
          source_payload: {},
          returns_disposition: run!.manager === "returns" ? disposition : null,
        };
      } else if (action.kind === "retry") {
        path = "/v1/runs/" + encodeURIComponent(run!.id) + "/retry";
        body = {};
      } else if (action.kind === "event") {
        path += "/events";
        body = {
          event_id: eventId,
          kind: eventKind,
          unit_id: context.unit.id,
          order_id: context.unit.data.order_id,
          source: { reference: source, note: reason },
        };
      } else if (action.kind === "route") {
        path += "/route";
        body = {
          expected_version: version,
          route,
          reason,
          source_reference: source,
        };
      } else {
        path += "/control";
        body = { expected_version: version, action: action.kind, reason };
      }
      await api.post(path, body);
      onSaved();
      onClose();
    } catch (e) {
      setError(e);
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  return (
    <Dialog title={title} onClose={onClose} dirty={dirty || busy} locked={busy}>
      <p className="hint">
        Signed in as <strong>{session.operator}</strong> · {session.role}.
        Identity is attached by the backend.
      </p>
      {!!error && <ErrorNotice error={error} />}
      {error instanceof ApiError &&
        ["STALE_REVIEW", "STALE_WORKFLOW"].includes(error.code) && (
          <button
            type="button"
            onClick={async () => {
              try {
                const fresh = await api.get<Context>(
                  "/v1/workflows/" + context.workflow.id + "/context",
                );
                setVersion(
                  action.kind === "review"
                    ? fresh.workflow.runs.find((r) => r.id === run!.id)!.version
                    : fresh.workflow.version,
                );
                onRefresh();
                setConfirmation(false);
                setError(undefined);
              } catch (e) {
                setError(e);
              }
            }}
          >
            Load latest version; keep my draft
          </button>
        )}
      {confirmation ? (
        <div className="confirmation">
          <h3>Confirm this saved action</h3>
          <p>
            {action.kind === "review"
              ? "This is an attributed human decision, not an AI verification. Original findings and review history will be retained."
              : action.kind === "cancel"
                ? "Cancellation is permanent for this workflow. Completed evidence remains available."
                : "The backend will validate current permissions and state before saving."}
          </p>
          <p>
            <strong>Reason:</strong> {reason}
          </p>
          {action.kind === "review" && (
            <ul>
              {findings.map((f) => (
                <li key={f.check_key}>
                  {label(f.check_key)}: <strong>{label(f.verdict)}</strong>
                </li>
              ))}
            </ul>
          )}
          <div className="form-actions">
            <button
              type="button"
              disabled={busy}
              onClick={() => setConfirmation(false)}
            >
              Back to edit
            </button>
            <button
              className="primary"
              disabled={busy}
              onClick={() => void save()}
            >
              {busy
                ? "Saving…"
                : action.kind === "review"
                  ? "Confirm & save review"
                  : "Confirm action"}
            </button>
          </div>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (action.kind === "review" && !images.length) {
              setError(new ApiError("REQUIRED_IMAGE"));
              return;
            }
            setConfirmation(true);
          }}
        >
          {action.kind === "review" && (
            <>
              <div className="notice">
                Original verdict:{" "}
                <strong>
                  {run!.data.output
                    ? label(run!.data.output.verdict)
                    : "No finding recorded"}
                </strong>
                . All checks start uncertain; choose only what the evidence
                supports.
              </div>
              {findings.map((finding, index) => (
                <fieldset key={finding.check_key}>
                  <legend>{label(finding.check_key)}</legend>
                  <label>
                    Verdict for {label(finding.check_key)}
                    <select
                      value={finding.verdict}
                      onChange={(e) =>
                        setFindings((old) =>
                          old.map((f, i) =>
                            i === index
                              ? { ...f, verdict: e.target.value as Verdict }
                              : f,
                          ),
                        )
                      }
                    >
                      <option value="uncertain">Uncertain</option>
                      <option value="pass">Pass</option>
                      <option value="fail">Fail</option>
                    </select>
                  </label>
                  <label>
                    Evidence for {label(finding.check_key)}
                    <textarea
                      required
                      minLength={10}
                      maxLength={2000}
                      value={finding.detail}
                      onChange={(e) =>
                        setFindings((old) =>
                          old.map((f, i) =>
                            i === index ? { ...f, detail: e.target.value } : f,
                          ),
                        )
                      }
                    />
                  </label>
                </fieldset>
              ))}
              <fieldset>
                <legend>Attach saved evidence (1–8)</legend>
                {context.images.length === 0 ? (
                  <p>Upload a photograph before submitting a review.</p>
                ) : (
                  context.images.map((image) => (
                    <label className="check-line" key={image.id}>
                      <input
                        type="checkbox"
                        checked={images.includes(image.id)}
                        disabled={
                          !images.includes(image.id) && images.length >= 8
                        }
                        onChange={(e) =>
                          setImages((old) =>
                            e.target.checked
                              ? [...old, image.id]
                              : old.filter((id) => id !== image.id),
                          )
                        }
                      />
                      Evidence {image.id.slice(0, 8)} · uploaded{" "}
                      {date(image.taken_at)}
                    </label>
                  ))
                )}
              </fieldset>
              <label>
                Actual photograph capture time
                <input
                  type="datetime-local"
                  value={captured}
                  onChange={(e) => setCaptured(e.target.value)}
                  required
                />
              </label>
              <p className="hint">
                Enter the capture time, not the upload time. The backend
                requires a capture within 24 hours.
              </p>
              {run!.manager === "returns" && (
                <label>
                  Returns disposition
                  <select
                    value={disposition}
                    onChange={(e) => setDisposition(e.target.value)}
                  >
                    {[
                      "pending_review",
                      "restock",
                      "refurbish",
                      "liquidate",
                      "dispose",
                    ].map((v) => (
                      <option key={v} value={v}>
                        {label(v)}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </>
          )}
          {action.kind === "route" && (
            <>
              <label>
                Verified route
                <select
                  value={route}
                  onChange={(e) => setRoute(e.target.value)}
                >
                  <option value="fba">FBA → Prep</option>
                  <option value="merchant">Merchant → Pack</option>
                  <option value="3pl">3PL → Pack</option>
                </select>
              </label>
              <label>
                Source reference
                <input
                  required
                  minLength={3}
                  maxLength={300}
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                />
              </label>
            </>
          )}
          {action.kind === "event" && (
            <>
              <label>
                Event type
                <select
                  value={eventKind}
                  onChange={(e) => setEventKind(e.target.value)}
                >
                  <option value="return_received">
                    Return received → Returns
                  </option>
                  <option value="charge_received">
                    Charge received → Recovery review
                  </option>
                </select>
              </label>
              <label>
                Original event ID
                <input
                  required
                  maxLength={120}
                  value={eventId}
                  onChange={(e) => setEventId(e.target.value)}
                />
              </label>
              <label>
                Source reference
                <input
                  required
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                />
              </label>
              <p className="hint">
                Record an event that actually exists. Do not invent a charge or
                return to activate a stage.
              </p>
            </>
          )}
          <label>
            {action.kind === "review" ? "Reason for this review" : "Reason"}
            <textarea
              required
              minLength={10}
              maxLength={2000}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <div className="form-actions">
            <button className="primary" type="submit">
              Review changes <ArrowUpRight size={16} />
            </button>
          </div>
        </form>
      )}
    </Dialog>
  );
}

function UploadPanel({
  api,
  context,
  session,
  onSaved,
}: {
  api: OperationsApi;
  context: Context;
  session: Session;
  onSaved: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<unknown>();
  const [success, setSuccess] = useState("");
  const lock = useRef(false);
  async function upload(file?: File) {
    if (!file || lock.current) return;
    lock.current = true;
    setBusy(true);
    setSuccess("");
    setError(undefined);
    setProgress(0);
    try {
      if (
        !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
        file.size > session.upload_limits.max_bytes ||
        file.size === 0
      )
        throw new ApiError("INVALID_IMAGE");
      const bitmap = await createImageBitmap(file);
      const valid =
        Math.min(bitmap.width, bitmap.height) >=
          session.upload_limits.min_dimension &&
        bitmap.width * bitmap.height <= session.upload_limits.max_pixels;
      bitmap.close();
      if (!valid) throw new ApiError("INVALID_IMAGE");
      const saved = await api.upload(context.workflow.id, file, setProgress);
      setSuccess(
        "Evidence " +
          saved.id.slice(0, 8) +
          " saved. Uploading does not run an inspection.",
      );
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError("INVALID_IMAGE"));
    } finally {
      setBusy(false);
      lock.current = false;
    }
  }
  const allowed = context.actions.upload.allowed;
  return (
    <section className="card">
      <div className="section-head">
        <div>
          <p className="eyebrow">EVIDENCE</p>
          <h2>Photographs, kept private</h2>
        </div>
        <span className="count">{context.images.length}</span>
      </div>
      <p>JPEG, PNG or WebP · up to 10 MiB · 64 px minimum · 20 MP maximum.</p>
      <div className="upload-actions">
        <label className={"file-button " + (!allowed ? "disabled" : "")}>
          <Upload size={17} />
          Choose photograph
          <input
            type="file"
            aria-label="Evidence photograph"
            accept="image/jpeg,image/png,image/webp"
            disabled={!allowed || busy}
            onChange={(e) => {
              void upload(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </label>
        <label className={"file-button " + (!allowed ? "disabled" : "")}>
          <Camera size={17} />
          Use phone camera
          <input
            type="file"
            aria-label="Phone camera photograph"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            disabled={!allowed || busy}
            onChange={(e) => {
              void upload(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </label>
      </div>
      {!allowed && (
        <p className="hint">{explain(context.actions.upload.reason!)}</p>
      )}
      {busy && (
        <div role="status">
          <progress max={100} value={progress} />
          {progress === 100
            ? "Upload sent; waiting for saved confirmation…"
            : `Uploading ${progress}%`}
        </div>
      )}
      {!!error && <ErrorNotice error={error} />}
      <p role="status" className="success-text">
        {success}
      </p>
      <div className="photo-grid">
        {context.images.map((image) => (
          <figure key={image.id}>
            <AuthImage api={api} id={image.id} />
            <figcaption>
              Evidence {image.id.slice(0, 8)}
              <small>
                {date(image.taken_at)} · {(image.bytes / 1024).toFixed(0)} KB
              </small>
            </figcaption>
          </figure>
        ))}
      </div>
      {!context.images.length && (
        <p className="hint">No photographs saved for this workflow.</p>
      )}
    </section>
  );
}

function Findings({ findings }: { findings: Finding[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Check</th>
            <th>Verdict</th>
            <th>Supporting observation</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => (
            <tr key={f.check_key}>
              <td>{label(f.check_key)}</td>
              <td>
                <Badge value={f.verdict} />
              </td>
              <td>{f.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function RunCard({
  run,
  permissions,
  onAction,
}: {
  run: Run;
  permissions: Context["run_actions"][string];
  onAction: (a: Action) => void;
}) {
  const output = run.data.output;
  const latest = run.data.human_reviews.at(-1);
  return (
    <article className="run-card">
      <div className="run-head">
        <div>
          <h3>{label(run.manager)}</h3>
          <small>
            {date(run.created_at)} · run {run.id.slice(0, 8)}
          </small>
        </div>
        <Badge value={run.state} />
      </div>
      <dl className="result-meta">
        <div>
          <dt>Business verdict</dt>
          <dd>
            {latest ? (
              <Badge value={latest.verdict} />
            ) : output ? (
              <Badge value={output.verdict} />
            ) : (
              <span>Not established</span>
            )}
          </dd>
        </div>
        <div>
          <dt>Evidence basis</dt>
          <dd>{basis(latest?.basis || output?.basis || "")}</dd>
        </div>
      </dl>
      {run.data.error && (
        <div className="notice">
          <strong>{explain(run.data.error.code)}</strong>
          <small>{run.data.error.code}</small>
          {run.data.error.safe_action && <p>{run.data.error.safe_action}</p>}
        </div>
      )}
      {output && (
        <details>
          <summary>Original saved findings</summary>
          <p>
            {basis(output.basis)} · Original verdict:{" "}
            <strong>{label(output.verdict)}</strong>
          </p>
          {output.findings.length ? (
            <Findings findings={output.findings} />
          ) : (
            <p>
              No visual findings. Recovery has not established claim
              eligibility.
            </p>
          )}
          {output.evidence_run_ids.length > 0 && (
            <p>
              Linked prior evidence:{" "}
              {output.evidence_run_ids.map((id) => id.slice(0, 8)).join(", ")}
            </p>
          )}
        </details>
      )}
      {run.data.human_reviews.length > 0 && (
        <details>
          <summary>
            Human review history ({run.data.human_reviews.length})
          </summary>
          {run.data.human_reviews.map((review, i) => (
            <section className="review-entry" key={review.at + i}>
              <strong>
                {review.reviewer} · {label(review.verdict)}
              </strong>
              <small>
                {date(review.at)} · {basis(review.basis)}
              </small>
              <p>{review.reason}</p>
              {i > 0 && (
                <p>
                  Previous verdict:{" "}
                  {label(review.original_verdict || "not established")}
                </p>
              )}
              <Findings findings={review.findings} />
            </section>
          ))}
        </details>
      )}
      <div className="run-actions">
        <button
          disabled={!permissions.review.allowed}
          onClick={() => onAction({ kind: "review", run })}
        >
          Manual review <ArrowUpRight size={14} />
        </button>
        <button
          disabled={!permissions.retry.allowed}
          onClick={() => onAction({ kind: "retry", run })}
        >
          Retry processing
        </button>
      </div>
      {!permissions.review.allowed && (
        <p className="hint">Review: {explain(permissions.review.reason!)}</p>
      )}
      {!permissions.retry.allowed && (
        <p className="hint">Retry: {explain(permissions.retry.reason!)}</p>
      )}
    </article>
  );
}

function WorkflowDetail({
  api,
  id,
  session,
  onBack,
}: {
  api: OperationsApi;
  id: string;
  session: Session;
  onBack: () => void;
}) {
  const cache = useQueryClient();
  const [action, setAction] = useState<Action | null>(null);
  const [saved, setSaved] = useState("");
  const query = useQuery({
    queryKey: ["context", id],
    queryFn: () =>
      api.get<Context>("/v1/workflows/" + encodeURIComponent(id) + "/context"),
    refetchInterval: (q) =>
      action
        ? false
        : Math.min(30000, 5000 * 2 ** Math.min(q.state.fetchFailureCount, 3)),
    refetchIntervalInBackground: false,
  });
  const refresh = () => {
    void query.refetch();
    void cache.invalidateQueries({ queryKey: ["overview"] });
  };
  if (!query.data)
    return (
      <>
        <button onClick={onBack}>
          <ArrowLeft size={16} />
          All workflows
        </button>
        {query.error ? (
          <ErrorNotice error={query.error} />
        ) : (
          <p role="status">Loading workflow and evidence…</p>
        )}
        <button onClick={() => void query.refetch()}>Refresh</button>
      </>
    );
  const context = query.data;
  const workflow = context.workflow;
  const missing = (manager: Manager) =>
    workflow.data.policy?.stages.find((s) => s.stage === manager)?.reason ||
    (manager === "returns"
      ? "No return event recorded."
      : manager === "recovery"
        ? "No charge event recorded."
        : manager === "prep" && workflow.data.route !== "fba"
          ? "Not scheduled for this route."
          : manager === "pack" &&
              !["merchant", "3pl"].includes(workflow.data.route)
            ? "Not scheduled for this route."
            : "Waiting for eligible preceding evidence.");
  return (
    <>
      <div className="breadcrumb">
        <button onClick={onBack}>
          <ArrowLeft size={15} />
          All workflows
        </button>
        <span>/</span>
        <span>Unit detail</span>
      </div>
      <div className="page-head">
        <div>
          <p className="eyebrow">UNIT WORKSPACE</p>
          <h1>Order {context.unit.data.order_id}</h1>
          <VisionEvidence api={api} workflowId={id} />
          <details className="identifier-details">
            <summary>Unit and workflow identifiers</summary>
            <p>Unit: {workflow.unit_id}</p>
            <p>Workflow: {workflow.id}</p>
            <button
              onClick={() => {
                void navigator.clipboard
                  .writeText(workflow.unit_id)
                  .then(() => setSaved("Unit identifier copied."))
                  .catch(() =>
                    setSaved("Copy unavailable. Select the identifier above."),
                  );
              }}
            >
              Copy unit ID
            </button>
          </details>
        </div>
        <div className="head-actions">
          <Badge value={workflow.data.state} />
          <button onClick={refresh} disabled={query.isFetching}>
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>
      {query.error && (
        <>
          <ErrorNotice error={query.error} />
          <p className="notice">
            Showing last saved data. Actions are disabled until refresh
            succeeds.
          </p>
        </>
      )}
      {workflow.data.fixture && (
        <div className="fixture-note">
          Synthetic test data · These records do not establish model accuracy.
        </div>
      )}
      <p role="status" className="success-text">
        {saved}
      </p>
      <section className="card unit-summary">
        <div>
          <span className="eyebrow">FULFILLMENT ROUTE</span>
          <h2>{label(workflow.data.route)}</h2>
          <p>
            {workflow.data.route === "fba"
              ? "Receiving → Prep"
              : workflow.data.route === "unknown"
                ? "Route needs a verified source"
                : "Receiving → Pack"}
          </p>
        </div>
        <div>
          <span className="eyebrow">EXPECTED ORDER</span>
          {context.unit.data.lines.map((line) => (
            <p key={line.sku}>
              <strong>{line.sku}</strong>
              <span className="quantity">× {line.quantity}</span>
            </p>
          ))}
          <small>
            Observed product identities and counts are not provided by this
            manual backend.
          </small>
        </div>
        <div>
          <span className="eyebrow">SHIPMENT</span>
          <p>{context.unit.data.shipment_id || "Not recorded"}</p>
          <small>Created {date(workflow.created_at)}</small>
        </div>
      </section>
      {workflow.data.policy && (
        <section className="notice">
          <strong>Policy {workflow.data.policy.version}</strong>
          <p>
            Rules:{" "}
            {workflow.data.policy.rule_ids.join(", ") || "No matching rule"}.{" "}
            {workflow.data.policy.blocked_reasons.join("; ")}
          </p>
          <small>
            Receiving is linked to the inventory receipt; no inbound event is
            created by checkout.
          </small>
        </section>
      )}
      {workflow.data.policy?.blocked_reasons.length ? (
        <details className="card">
          <summary>Review workflow policy configuration</summary>
          <p>
            Requires verified Pod assignment and a published policy version.
            Existing evidence is preserved; started workflows cannot change
            policy here.
          </p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              try {
                await api.post(
                  `/v1/commerce/admin/workflows/${workflow.id}/policy-review`,
                  {
                    expected_version: workflow.version,
                    policy_version: f.get("version"),
                    reason: f.get("reason"),
                  },
                );
                setSaved("Policy review recorded.");
                refresh();
              } catch (error) {
                setSaved(
                  error instanceof Error
                    ? error.message
                    : "Policy review unavailable",
                );
              }
            }}
          >
            <label>
              Published policy version
              <input
                name="version"
                defaultValue={workflow.data.policy.version}
                required
              />
            </label>
            <label>
              Reason for configuration review
              <textarea name="reason" minLength={10} required />
            </label>
            <button disabled={session.role !== "supervisor" || !!query.error}>
              Review configuration
            </button>
          </form>
        </details>
      ) : null}
      <nav aria-label="Current fulfillment route" className="route-overview">
        <ol>
          {(
            [
              "receiving",
              ...(workflow.data.route === "fba"
                ? ["prep"]
                : ["merchant", "3pl"].includes(workflow.data.route)
                  ? ["pack"]
                  : []),
              "returns",
              "recovery",
            ] as Manager[]
          ).map((manager) => {
            const run = workflow.runs
              .filter((r) => r.manager === manager)
              .at(-1);
            const selected = workflow.data.policy?.stages.find(
              (s) => s.stage === manager,
            );
            const state = query.error
              ? "stale"
              : run?.state === "running" && workflow.data.state !== "active"
                ? "blocked"
                : run?.state ||
                  selected?.state.toLowerCase() ||
                  "not_scheduled";
            return (
              <li key={manager} className={"route-stage " + state}>
                <strong>{label(manager)}</strong>
                <span>
                  {state === "stale"
                    ? "Refresh required"
                    : state === "not_applicable"
                      ? "Not applicable"
                      : state === "not_scheduled"
                        ? "Not scheduled"
                        : label(state)}
                </span>
                {!run && <small>{missing(manager)}</small>}
                {state === "running" && (
                  <small role="status">Processing saved evidence</small>
                )}
              </li>
            );
          })}
        </ol>
        {workflow.data.route === "unknown" && (
          <p className="notice">Fulfillment branch needs a verified route.</p>
        )}
      </nav>
      <div className="detail-grid">
        <section>
          <div className="section-head">
            <div>
              <p className="eyebrow">WORKFLOW</p>
              <h2>Every stage, accounted for</h2>
            </div>
          </div>
          <div className="timeline">
            {managers.map((manager, index) => {
              const stage = workflow.runs.filter((r) => r.manager === manager);
              return (
                <section
                  className={
                    "timeline-stage" +
                    (!query.error &&
                    workflow.data.state === "active" &&
                    stage.some((r) => r.state === "running")
                      ? " is-processing"
                      : "")
                  }
                  key={manager}
                  aria-label={label(manager) + " stage"}
                >
                  {!query.error &&
                    workflow.data.state === "active" &&
                    stage.some((r) => r.state === "running") && (
                      <p className="processing-label" role="status">
                        {label(manager)} is processing saved evidence
                      </p>
                    )}
                  <span className="stage-number" aria-hidden="true">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {stage.length ? (
                    stage.map((run) => (
                      <RunCard
                        key={run.id}
                        run={run}
                        permissions={
                          query.error
                            ? {
                                review: {
                                  allowed: false,
                                  reason: "REFRESH_REQUIRED",
                                },
                                retry: {
                                  allowed: false,
                                  reason: "REFRESH_REQUIRED",
                                },
                              }
                            : context.run_actions[run.id]
                        }
                        onAction={setAction}
                      />
                    ))
                  ) : (
                    <div className="not-scheduled">
                      <strong>{label(manager)}</strong>
                      <span>
                        {workflow.data.policy?.stages.find(
                          (s) => s.stage === manager,
                        )?.state === "NOT_APPLICABLE"
                          ? "Not applicable"
                          : "Not scheduled"}
                      </span>
                      <p>{missing(manager)}</p>
                    </div>
                  )}
                </section>
              );
            })}
          </div>
          <details className="card activity-details">
            <summary>Activity trail ({workflow.events.length})</summary>
            <ol className="activity">
              {workflow.events.map((event) => (
                <li key={event.id}>
                  <span>{label(event.data.name)}</span>
                  <small>
                    {event.data.actor} · {date(event.created_at)}
                  </small>
                </li>
              ))}
            </ol>
          </details>
        </section>
        <aside className="detail-aside">
          <UploadPanel
            api={api}
            context={
              query.error
                ? {
                    ...context,
                    actions: {
                      ...context.actions,
                      upload: { allowed: false, reason: "REFRESH_REQUIRED" },
                    },
                  }
                : context
            }
            session={session}
            onSaved={refresh}
          />
          <section className="card">
            <h2>Workflow actions</h2>
            <p>Permissions and eligibility come from the backend.</p>
            <div className="workflow-controls">
              {(["event", "route", "hold", "resume", "cancel"] as const).map(
                (kind) => (
                  <div key={kind}>
                    <button
                      disabled={!!query.error || !context.actions[kind].allowed}
                      onClick={() => setAction({ kind })}
                    >
                      {kind === "event"
                        ? "Record return / charge event"
                        : kind === "route"
                          ? "Resolve route"
                          : label(kind) + " workflow"}
                    </button>
                    {!context.actions[kind].allowed && (
                      <small>{explain(context.actions[kind].reason!)}</small>
                    )}
                  </div>
                ),
              )}
            </div>
          </section>
        </aside>
      </div>
      {action && (
        <ReviewDialog
          api={api}
          context={context}
          session={session}
          action={action}
          onRefresh={refresh}
          onClose={() => setAction(null)}
          onSaved={() => {
            setSaved("Saved by the backend. Refreshing the evidence trail.");
            refresh();
          }}
        />
      )}
    </>
  );
}

function CreateDialog({
  api,
  mode,
  units,
  products,
  onClose,
  onSaved,
}: {
  api: OperationsApi;
  mode: "start" | "unit" | "product";
  units: Unit[];
  products: Product[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({
    route: "unknown",
    unit: units[0]?.id || "",
  });
  const [fixture, setFixture] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const lock = useRef(false);
  const field = (key: string, title: string, required = true) => (
    <label>
      {title}
      <input
        required={required}
        maxLength={key === "description" ? 1000 : 120}
        value={values[key] || ""}
        onChange={(e) => setValues((v) => ({ ...v, [key]: e.target.value }))}
      />
    </label>
  );
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(undefined);
    try {
      let path: string, body: unknown;
      if (mode === "start") {
        path = "/v1/workflows";
        body = { unit_id: values.unit };
      } else if (mode === "product") {
        path = "/v1/catalogue";
        body = {
          sku: values.sku,
          name: values.name,
          visual_description: values.description,
        };
      } else {
        path = "/v1/units";
        const lines = (values.lines || "")
          .split("\n")
          .filter(Boolean)
          .map((line) => {
            const [sku, q] = line.split(",").map((s) => s.trim());
            const quantity = Number(q);
            if (
              !sku ||
              !Number.isInteger(quantity) ||
              quantity < 1 ||
              quantity > 100
            )
              throw new ApiError("INVALID_INPUT");
            return { sku, quantity };
          });
        body = {
          unit_id: values.id,
          order_id: values.order,
          route: values.route,
          shipment_id: values.shipment || null,
          lines,
          fixture,
          source: {},
        };
      }
      await api.post(path, body);
      onSaved();
      onClose();
    } catch (e) {
      setError(e);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <Dialog
      title={
        mode === "start"
          ? "Start a workflow"
          : mode === "unit"
            ? "Register a unit"
            : "Add catalogue product"
      }
      onClose={onClose}
      dirty={Object.keys(values).length > 2 || busy}
      locked={busy}
    >
      {!!error && <ErrorNotice error={error} />}
      <form onSubmit={submit}>
        {mode === "start" ? (
          <>
            <p>
              Choose an existing unit. Starting creates a Receiving run; it does
              not run a model.
            </p>
            <label>
              Registered unit
              <select
                required
                value={values.unit}
                onChange={(e) =>
                  setValues((v) => ({ ...v, unit: e.target.value }))
                }
              >
                <option value="">Choose a unit</option>
                {units.map((unit) => (
                  <option key={unit.id} value={unit.id}>
                    {unit.id} · {unit.data.order_id}
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : mode === "product" ? (
          <>
            {field("sku", "SKU")}
            {field("name", "Product name")}
            {field("description", "Visible description")}
            <p className="hint">
              Metadata only. This does not enable recognition or create
              reference photos.
            </p>
          </>
        ) : (
          <>
            {field("id", "Official unit ID")}
            {field("order", "Order ID")}
            {field("shipment", "Shipment ID", false)}
            <label>
              Verified route
              <select
                value={values.route}
                onChange={(e) =>
                  setValues((v) => ({ ...v, route: e.target.value }))
                }
              >
                <option value="unknown">Unknown — do not infer</option>
                <option value="fba">FBA</option>
                <option value="merchant">Merchant</option>
                <option value="3pl">3PL</option>
              </select>
            </label>
            <label>
              Order lines (one SKU, quantity per line)
              <textarea
                required
                placeholder="EXISTING-SKU, 2"
                value={values.lines || ""}
                onChange={(e) =>
                  setValues((v) => ({ ...v, lines: e.target.value }))
                }
              />
            </label>
            <p className="hint">
              Available SKUs:{" "}
              {products.map((p) => p.data.sku).join(", ") ||
                "None. Add a catalogue product first."}
            </p>
            <label className="check-line">
              <input
                type="checkbox"
                checked={fixture}
                onChange={(e) => setFixture(e.target.checked)}
              />
              This is synthetic software test data
            </label>
          </>
        )}
        <div className="form-actions">
          <button className="primary" disabled={busy}>
            {busy
              ? "Saving…"
              : mode === "start"
                ? "Start Receiving workflow"
                : "Save record"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}

function Workspace({
  api,
  session,
  onDisconnect,
}: {
  api: OperationsApi;
  session: Session;
  onDisconnect: () => void;
}) {
  const [id, setId] = useState(
    new URLSearchParams(location.hash.slice(1)).get("workflow") || "",
  );
  const [page, setPage] = useState("overview");
  const [modal, setModal] = useState<"start" | "unit" | "product" | null>(null);
  const params = new URLSearchParams(location.search);
  const [search, setSearch] = useState(params.get("q") || "");
  const [route, setRoute] = useState(params.get("route") || "");
  const [manager, setManager] = useState(params.get("manager") || "");
  const [status, setStatus] = useState(params.get("status") || "");
  useEffect(() => {
    const handler = () =>
      setId(new URLSearchParams(location.hash.slice(1)).get("workflow") || "");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  useEffect(() => {
    const p = new URLSearchParams();
    if (search) p.set("q", search);
    if (route) p.set("route", route);
    if (manager) p.set("manager", manager);
    if (status) p.set("status", status);
    history.replaceState(
      null,
      "",
      location.pathname + (p.size ? "?" + p : "") + location.hash,
    );
  }, [search, route, manager, status]);
  const data = useQuery({
    queryKey: ["overview"],
    queryFn: async () => {
      const [workflows, units, runs, products] = await Promise.all([
        api.get<Workflow[]>("/v1/workflows"),
        api.get<Unit[]>("/v1/units"),
        api.get<Run[]>("/v1/runs"),
        api.get<Product[]>("/v1/catalogue"),
      ]);
      return { workflows, units, runs, products };
    },
  });
  const open = (value: string) => {
    location.hash = value ? "workflow=" + encodeURIComponent(value) : "";
    setId(value);
  };
  const filtered = (data.data?.workflows || []).filter((w) => {
    const unit = data.data?.units.find((u) => u.id === w.unit_id);
    const stage = data.data?.runs.filter((r) => r.workflow_id === w.id) || [];
    return (
      (!route || w.data.route === route) &&
      (!manager || stage.some((r) => r.manager === manager)) &&
      (!status ||
        w.data.state === status ||
        stage.some((r) => r.state === status)) &&
      `${w.unit_id} ${unit?.data.order_id || ""}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (page !== "review" ||
        stage.some((r) =>
          ["blocked", "review_needed", "retryable"].includes(r.state),
        ))
    );
  });
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <div className="wordmark">
          <Box /> CUBE <span>OPERATIONS</span>
        </div>
        <p className="sidebar-label">WORKSPACE</p>
        <nav aria-label="Operations navigation">
          <button
            className={!id && page === "overview" ? "selected" : ""}
            onClick={() => {
              open("");
              setPage("overview");
            }}
          >
            <LayoutGrid size={18} />
            All workflows
          </button>
          <button
            className={!id && page === "review" ? "selected" : ""}
            onClick={() => {
              open("");
              setPage("review");
            }}
          >
            <ListChecks size={18} />
            Review queue
          </button>
          {session.role === "supervisor" && (
            <>
              <button
                onClick={() => {
                  open("");
                  setPage("commerce");
                }}
              >
                Commerce setup
              </button>
              <button
                onClick={() => {
                  open("");
                  setPage("analytics");
                }}
              >
                Analytics
              </button>
            </>
          )}
        </nav>
        <div className="sidebar-bottom">
          <span className="local-dot" /> OPERATIONS WORKSPACE
          <p>Evidence before decisions.</p>
          <small>Connected to your authenticated workspace.</small>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            Commerce operations <span className="muted">/ Evidence</span>
          </span>
          <div>
            <span className="operator">
              {session.operator} <small>{session.role}</small>
            </span>
            <button
              className="icon-button"
              title="Disconnect"
              aria-label="Disconnect"
              onClick={onDisconnect}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main id="main-content">
          <div className="inference-strip">
            <CircleHelp size={16} />
            <span>
              <strong>
                {session.inference === "blocked"
                  ? "Automatic inspection is blocked."
                  : "Automatic inspection status: " + session.inference}
              </strong>{" "}
              Evidence uploads and attributed manual reviews are available.
            </span>
          </div>
          {!id && page === "commerce" ? (
            <CommerceAdmin api={api} onOpen={open} />
          ) : !id && page === "analytics" ? (
            <AnalyticsPanel api={api} />
          ) : id ? (
            <WorkflowDetail
              key={id}
              api={api}
              id={id}
              session={session}
              onBack={() => open("")}
            />
          ) : (
            <>
              <div className="page-head">
                <div>
                  <p className="eyebrow">THE OPERATIONS DESK</p>
                  <h1>
                    {page === "review"
                      ? "Make the next decision."
                      : "A clearer view of every unit."}
                  </h1>
                  <p>
                    {page === "review"
                      ? "Blocked, uncertain and retry-eligible work, with its evidence intact."
                      : "Follow the work. Find the exceptions. Keep the evidence."}
                  </p>
                </div>
                <button
                  className="primary"
                  disabled={!session.can_write || !data.data || !!data.error}
                  onClick={() => setModal("start")}
                >
                  <Plus size={17} />
                  Start workflow
                </button>
              </div>
              {data.error && (
                <>
                  <ErrorNotice error={data.error} />
                  {data.data && (
                    <p className="notice">
                      Showing stale saved data. Refresh to restore actions.
                    </p>
                  )}
                </>
              )}
              {!data.data ? (
                data.isLoading ? (
                  <div className="card loading" role="status">
                    Loading your workflows…
                  </div>
                ) : (
                  <button onClick={() => void data.refetch()}>
                    Refresh connection
                  </button>
                )
              ) : (
                <>
                  <div className="stats">
                    <div>
                      <span>REGISTERED WORKFLOWS</span>
                      <strong>{data.data.workflows.length}</strong>
                      <small>Actual saved records</small>
                    </div>
                    <div>
                      <span>AWAITING ATTENTION</span>
                      <strong>
                        {
                          data.data.runs.filter((r) =>
                            ["blocked", "review_needed", "retryable"].includes(
                              r.state,
                            ),
                          ).length
                        }
                      </strong>
                      <small>Manager runs needing action</small>
                    </div>
                    <div>
                      <span>REVIEWED RUNS</span>
                      <strong>
                        {
                          data.data.runs.filter(
                            (r) => r.data.human_reviews.length > 0,
                          ).length
                        }
                      </strong>
                      <small>Attributed human decisions</small>
                    </div>
                  </div>
                  <section className="card workflow-list">
                    <div className="section-head">
                      <h2>
                        {page === "review" ? "Review queue" : "Workflows"}
                      </h2>
                      <button
                        className="text-button"
                        onClick={() => void data.refetch()}
                        disabled={data.isFetching}
                      >
                        <RefreshCw size={15} />
                        {data.isFetching ? "Refreshing…" : "Refresh"}
                      </button>
                    </div>
                    <div className="filters">
                      <label>
                        Search unit or order
                        <input
                          type="search"
                          placeholder="Find a unit or order…"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                        />
                      </label>
                      <label>
                        Route
                        <select
                          value={route}
                          onChange={(e) => setRoute(e.target.value)}
                        >
                          <option value="">All routes</option>
                          {["fba", "merchant", "3pl", "unknown"].map((r) => (
                            <option key={r} value={r}>
                              {label(r)}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Manager
                        <select
                          value={manager}
                          onChange={(e) => setManager(e.target.value)}
                        >
                          <option value="">All managers</option>
                          {managers.map((m) => (
                            <option key={m} value={m}>
                              {label(m)}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Status
                        <select
                          value={status}
                          onChange={(e) => setStatus(e.target.value)}
                        >
                          <option value="">All states</option>
                          {[
                            "active",
                            "held",
                            "cancelled",
                            "queued",
                            "running",
                            "blocked",
                            "review_needed",
                            "retryable",
                            "completed",
                          ].map((s) => (
                            <option key={s} value={s}>
                              {label(s)}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                    {filtered.length ? (
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Unit / order</th>
                              <th>Route</th>
                              <th>Workflow state</th>
                              <th>Next attention</th>
                              <th>
                                <span className="sr-only">Open</span>
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {filtered.map((w) => {
                              const stage = data.data!.runs.filter(
                                (r) => r.workflow_id === w.id,
                              );
                              const attention = stage.find((r) =>
                                [
                                  "blocked",
                                  "review_needed",
                                  "retryable",
                                ].includes(r.state),
                              );
                              const unit = data.data!.units.find(
                                (u) => u.id === w.unit_id,
                              );
                              return (
                                <tr key={w.id}>
                                  <td>
                                    <button
                                      className="row-link"
                                      onClick={() => open(w.id)}
                                    >
                                      {w.unit_id}
                                    </button>
                                    <small>
                                      {unit?.data.order_id ||
                                        "Order unavailable"}
                                    </small>
                                    {w.data.fixture && (
                                      <span className="fixture-tag">
                                        Synthetic test data
                                      </span>
                                    )}
                                  </td>
                                  <td>{label(w.data.route)}</td>
                                  <td>
                                    <Badge value={w.data.state} />
                                  </td>
                                  <td>
                                    {attention ? (
                                      <>
                                        <strong>
                                          {label(attention.manager)}
                                        </strong>
                                        <small>{label(attention.state)}</small>
                                      </>
                                    ) : (
                                      <span>
                                        {w.data.state === "held"
                                          ? "Supervisor may resume"
                                          : w.data.state === "cancelled"
                                            ? "No further processing"
                                            : stage.some((r) =>
                                                  [
                                                    "queued",
                                                    "running",
                                                  ].includes(r.state),
                                                )
                                              ? "Processing pending"
                                              : "No pending manager action"}
                                      </span>
                                    )}
                                  </td>
                                  <td>
                                    <button
                                      className="icon-button"
                                      aria-label={"Open " + w.unit_id}
                                      onClick={() => open(w.id)}
                                    >
                                      <ArrowUpRight size={18} />
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <Empty
                        title={
                          data.data.workflows.length
                            ? "No matching workflows"
                            : "No workflows yet"
                        }
                      >
                        {data.data.workflows.length
                          ? "Try different filters. No records have been removed."
                          : "Register a product and unit, then start Receiving. No synthetic records are added automatically."}
                      </Empty>
                    )}
                  </section>
                  <section className="setup-card">
                    <div>
                      <h2>Set up the next unit</h2>
                      <p>
                        {data.data.products.length} catalogue products ·{" "}
                        {data.data.units.length} registered units
                      </p>
                    </div>
                    <div className="head-actions">
                      <button
                        disabled={!session.can_write || !!data.error}
                        onClick={() => setModal("product")}
                      >
                        Add product
                      </button>
                      <button
                        disabled={!session.can_write || !!data.error}
                        onClick={() => setModal("unit")}
                      >
                        Register unit
                      </button>
                    </div>
                  </section>
                </>
              )}
              {modal && data.data && (
                <CreateDialog
                  api={api}
                  mode={modal}
                  units={data.data.units}
                  products={data.data.products}
                  onClose={() => setModal(null)}
                  onSaved={() => void data.refetch()}
                />
              )}
            </>
          )}
          <footer>
            Evidence workspace{" "}
            <span>
              Human decisions stay attributed. Uncertainty stays visible.
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}

function Connected({
  api,
  session,
  onDisconnect,
}: {
  api: OperationsApi;
  session: Session;
  onDisconnect: () => void;
}) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: false, refetchOnWindowFocus: false },
          mutations: { retry: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      {session.role === "customer" ? (
        <CustomerPortal
          api={api}
          session={session}
          onDisconnect={onDisconnect}
        />
      ) : (
        <Workspace api={api} session={session} onDisconnect={onDisconnect} />
      )}
    </QueryClientProvider>
  );
}
function Root() {
  const [connection, setConnection] = useState<{
    api: OperationsApi;
    session: Session;
  } | null>(null);
  const runtime = useRuntime();
  if (runtime.loading)
    return (
      <main>
        <p role="status">Checking workspace configuration�</p>
      </main>
    );
  if (
    runtime.mode !== "hosted" &&
    !["localhost", "127.0.0.1", "[::1]"].includes(location.hostname)
  )
    return (
      <main>
        <h1>Local workspace only</h1>
        <p>
          Start the documented local development server to use this interface.
        </p>
      </main>
    );
  return connection ? (
    <Connected
      {...connection}
      onDisconnect={async () => {
        sessionStorage.removeItem("cube-local-token");
        try {
          await hostedSignOut();
        } finally {
          setConnection(null);
        }
      }}
    />
  ) : runtime.mode === "hosted" ? (
    <HostedLogin
      config={runtime}
      onConnect={(api, session) => setConnection({ api, session })}
    />
  ) : (
    <Login onConnect={(api, session) => setConnection({ api, session })} />
  );
}
createRoot(document.getElementById("root")!).render(<Root />);
