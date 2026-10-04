export type Manager = "receiving" | "prep" | "pack" | "returns" | "recovery";
export type Verdict = "pass" | "fail" | "uncertain";
export type Route = "fba" | "merchant" | "3pl" | "unknown";
export interface Finding {
  check_key: string;
  verdict: Verdict;
  detail: string;
}
export interface Review {
  reviewer: string;
  at: string;
  reason: string;
  verdict: string;
  findings: Finding[];
  image_ids: string[];
  original_verdict: string | null;
  basis: string;
}
export interface Output {
  basis: "human" | "fixture_human" | "deterministic_evidence_review";
  verdict: string;
  findings: Finding[];
  image_ids: string[];
  evidence_run_ids: string[];
  claim_supported: false;
}
export interface Run {
  id: string;
  workflow_id: string;
  manager: Manager;
  state: string;
  version: number;
  created_at: string;
  retry_at: string | null;
  data: {
    correlation_id: string;
    output: Output | null;
    human_reviews: Review[];
    error: { code: string; retryable?: boolean; safe_action?: string } | null;
  };
}
export interface Workflow {
  id: string;
  unit_id: string;
  version: number;
  created_at: string;
  data: {
    state: string;
    route: Route;
    fixture: boolean;
    routing_error?: string;
  };
  runs?: Run[];
  events?: {
    id: string;
    created_at: string;
    run_id: string | null;
    data: { name: string; actor: string; detail: unknown };
  }[];
}
export interface Unit {
  id: string;
  data: {
    order_id: string;
    route: Route;
    fixture: boolean;
    shipment_id: string | null;
    lines: { sku: string; quantity: number }[];
  };
}
export interface ImageRef {
  id: string;
  bytes: number;
  dimensions: number[];
  taken_at: string;
}
export interface Permission {
  allowed: boolean;
  reason: string | null;
}
export interface Context {
  workflow: Workflow & { runs: Run[]; events: NonNullable<Workflow["events"]> };
  unit: Unit;
  images: ImageRef[];
  actions: Record<string, Permission>;
  run_actions: Record<string, { review: Permission; retry: Permission }>;
}
export interface Session {
  operator: string;
  organization: string;
  role: string;
  can_write: boolean;
  inference: string;
  checks: Partial<Record<Manager, string[]>>;
  upload_limits: {
    max_bytes: number;
    min_dimension: number;
    max_pixels: number;
  };
}
export interface Product {
  id: string;
  data: { sku: string; name: string; visual_description: string };
}

const explanations: Record<string, string> = {
  AUTH_REQUIRED: "Your local session is missing or expired. Connect again.",
  FORBIDDEN: "Your role cannot perform this action.",
  SUPERVISOR_REQUIRED: "A supervisor account is required.",
  STALE_REVIEW:
    "This run changed. Refresh and compare the saved findings before reviewing again. Your draft is still here.",
  STALE_WORKFLOW:
    "The workflow changed. Refresh before confirming a new action.",
  INVALID_INPUT: "Check the required fields and their values.",
  AUTOMATIC_ADAPTER_BLOCKED:
    "Automatic inspection is unavailable. Upload evidence for an attributed manual review.",
  CLAIM_REVIEW_NOT_IMPLEMENTED:
    "Claim approval is unavailable. Recovery only gathers evidence for review.",
  RETRY_NOT_ALLOWED: "This run is not eligible for a technical retry.",
  RETRY_BACKOFF: "The safe retry waiting period has not ended.",
  RETRY_BUDGET_EXHAUSTED:
    "The retry or call budget is exhausted. Human review is required.",
  REVIEW_NOT_ALLOWED:
    "Review is unavailable while the workflow is paused, cancelled or processing.",
  RECEIVING_NOT_APPROVED:
    "Receiving must be approved before this fulfillment stage can be reviewed.",
  WORKFLOW_NOT_ACTIVE: "Resume the workflow before adding evidence or events.",
  INVALID_TRANSITION:
    "This action is not available in the current workflow state.",
  DISPATCH_OUTCOME_UNKNOWN:
    "A request may already have been sent. Do not run inference again; inspect the saved evidence.",
  PREDECESSOR_REVISED:
    "Earlier receiving evidence changed. This stage needs a fresh review.",
  NOT_FOUND: "This record is unavailable or belongs to another organization.",
  DATABASE_UNAVAILABLE:
    "The local database is unavailable. Saved work is retained.",
  STALE_OR_INVALID_CAPTURE:
    "Use the actual capture time, within the last 24 hours.",
  IDENTITY_UNRESOLVED: "Identity has not been established.",
  NETWORK_ERROR:
    "Cannot reach the local API. Check the API process and refresh saved state.",
  REQUEST_TIMEOUT:
    "The request timed out. Its outcome is unknown. No automatic resubmission was made; refresh saved state before acting.",
  REQUEST_IN_FLIGHT: "This request is already in progress.",
  INVALID_RESPONSE:
    "The API returned an unexpected response. No success has been assumed.",
};
export const explain = (code: string) =>
  explanations[code] || code.toLowerCase().replaceAll("_", " ");
export class ApiError extends Error {
  constructor(
    public code: string,
    public status = 0,
  ) {
    super(explain(code));
  }
}

export class OperationsApi {
  private keys = new Map<string, string>();
  private inFlight = new Set<string>();
  constructor(
    private token: string,
    readonly base = "/operations-api",
    private timeoutMs = 15000,
  ) {
    if (base !== "/operations-api")
      throw new Error(
        "Use the local development proxy; configure INTEGRATED_API_TARGET on the Vite server.",
      );
  }
  private async response(response: Response) {
    if (!response.ok) {
      let code =
        (
          {
            401: "AUTH_REQUIRED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "INVALID_INPUT",
            429: "RATE_LIMITED",
          } as Record<number, string>
        )[response.status] || "SERVER_ERROR";
      try {
        const body = await response.json();
        const candidate = body?.error?.code;
        if (typeof candidate === "string" && /^[A-Z_]{3,80}$/.test(candidate))
          code = candidate;
      } catch {
        /* Never display raw server bodies. */
      }
      throw new ApiError(code, response.status);
    }
    return response;
  }
  async get<T>(path: string): Promise<T> {
    const value = await this.request<unknown>(path);
    const schema = path.endsWith("/context") ? contextSchema : schemas[path];
    if (schema && !schema.safeParse(value).success)
      throw new ApiError("INVALID_RESPONSE");
    return value as T;
  }
  async image(id: string): Promise<Blob> {
    return this.request<Blob>(
      "/v1/images/" + encodeURIComponent(id),
      {},
      async (response) => {
        if (
          !/^image\/(jpeg|png|webp)/.test(
            response.headers.get("content-type") || "",
          )
        )
          throw new ApiError("INVALID_RESPONSE");
        return response.blob();
      },
    );
  }
  private async request<T>(
    path: string,
    init: RequestInit = {},
    parse: (response: Response) => Promise<T> = (response) => response.json(),
  ): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await this.response(
        await fetch(this.base + path, {
          ...init,
          credentials: "omit",
          signal: controller.signal,
          headers: { ...init.headers, Authorization: "Bearer " + this.token },
        }),
      );
      return await parse(response);
    } catch (e) {
      if (e instanceof ApiError) throw e;
      if (e instanceof SyntaxError) throw new ApiError("INVALID_RESPONSE");
      throw new ApiError(
        controller.signal.aborted ? "REQUEST_TIMEOUT" : "NETWORK_ERROR",
      );
    } finally {
      clearTimeout(timer);
    }
  }
  async post<T>(path: string, body: unknown): Promise<T> {
    const fingerprint = path + JSON.stringify(body);
    if (this.inFlight.has(fingerprint)) throw new ApiError("REQUEST_IN_FLIGHT");
    const key = this.keys.get(fingerprint) || crypto.randomUUID();
    this.keys.set(fingerprint, key);
    this.inFlight.add(fingerprint);
    try {
      const result = await this.request<T>(path, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": key },
        body: JSON.stringify(body),
      });
      if (
        !result ||
        typeof result !== "object" ||
        !("id" in result) ||
        typeof result.id !== "string"
      )
        throw new ApiError("INVALID_RESPONSE");
      this.keys.delete(fingerprint);
      return result;
    } finally {
      this.inFlight.delete(fingerprint);
    } // Keep key on an ambiguous failure; never retry automatically.
  }
  async upload(
    workflowId: string,
    file: File,
    onProgress: (value: number) => void,
  ): Promise<{ id: string }> {
    const digest = Array.from(
      new Uint8Array(
        await crypto.subtle.digest("SHA-256", await file.arrayBuffer()),
      ),
    )
      .map((x) => x.toString(16).padStart(2, "0"))
      .join("");
    const fingerprint = workflowId + digest;
    if (this.inFlight.has(fingerprint)) throw new ApiError("REQUEST_IN_FLIGHT");
    const key = this.keys.get(fingerprint) || crypto.randomUUID();
    this.keys.set(fingerprint, key);
    this.inFlight.add(fingerprint);
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open(
        "POST",
        this.base +
          "/v1/workflows/" +
          encodeURIComponent(workflowId) +
          "/images",
      );
      xhr.setRequestHeader("Authorization", "Bearer " + this.token);
      xhr.setRequestHeader("Idempotency-Key", key);
      xhr.timeout = this.timeoutMs;
      const finish = () => this.inFlight.delete(fingerprint);
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable)
          onProgress(Math.round((event.loaded / event.total) * 100));
      };
      xhr.onload = () => {
        finish();
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText);
            if (!result.id) throw new Error();
            this.keys.delete(fingerprint);
            resolve(result);
          } catch {
            reject(new ApiError("INVALID_RESPONSE"));
          }
        } else {
          let code = "UPLOAD_FAILED";
          try {
            const candidate = JSON.parse(xhr.responseText)?.error?.code;
            if (/^[A-Z_]{3,80}$/.test(candidate)) code = candidate;
          } catch {}
          reject(new ApiError(code, xhr.status));
        }
      };
      xhr.onerror = () => {
        finish();
        reject(new ApiError("NETWORK_ERROR"));
      };
      xhr.ontimeout = () => {
        finish();
        reject(new ApiError("REQUEST_TIMEOUT"));
      };
      const form = new FormData();
      form.append("file", file);
      xhr.send(form);
    });
  }
}
import { z } from "zod";

const findingSchema = z.object({
  check_key: z.string(),
  verdict: z.enum(["pass", "fail", "uncertain"]),
  detail: z.string(),
});
const outputSchema = z.object({
  basis: z.string(),
  verdict: z.string(),
  findings: z.array(findingSchema),
  image_ids: z.array(z.string()),
  evidence_run_ids: z.array(z.string()),
  claim_supported: z.literal(false),
});
const reviewSchema = z.object({
  reviewer: z.string(),
  at: z.string(),
  reason: z.string(),
  verdict: z.string(),
  findings: z.array(findingSchema),
  image_ids: z.array(z.string()),
  original_verdict: z.string().nullable(),
  basis: z.string(),
});
const runSchema = z
  .object({
    id: z.string(),
    workflow_id: z.string(),
    manager: z.enum(["receiving", "prep", "pack", "returns", "recovery"]),
    state: z.string(),
    version: z.number(),
    created_at: z.string(),
    retry_at: z.string().nullable(),
    data: z.object({
      correlation_id: z.string(),
      output: outputSchema.nullable(),
      human_reviews: z.array(reviewSchema),
      error: z
        .object({
          code: z.string(),
          safe_action: z.string().optional(),
          retryable: z.boolean().optional(),
        })
        .nullable(),
    }),
  })
  .passthrough();
const workflowSchema = z
  .object({
    id: z.string(),
    unit_id: z.string(),
    version: z.number(),
    created_at: z.string(),
    data: z.object({
      state: z.string(),
      route: z.enum(["fba", "merchant", "3pl", "unknown"]),
      fixture: z.boolean(),
      routing_error: z.string().optional(),
    }),
  })
  .passthrough();
const unitSchema = z
  .object({
    id: z.string(),
    data: z.object({
      order_id: z.string(),
      route: z.string(),
      fixture: z.boolean(),
      shipment_id: z.string().nullable(),
      lines: z.array(z.object({ sku: z.string(), quantity: z.number() })),
    }),
  })
  .passthrough();
const permissionSchema = z.object({
  allowed: z.boolean(),
  reason: z.string().nullable(),
});
const schemas: Record<string, z.ZodType> = {
  "/v1/session": z.object({
    operator: z.string(),
    organization: z.string(),
    role: z.string(),
    can_write: z.boolean(),
    inference: z.string(),
    checks: z.record(z.string(), z.array(z.string())),
    upload_limits: z.object({
      max_bytes: z.number(),
      min_dimension: z.number(),
      max_pixels: z.number(),
    }),
  }),
  "/v1/workflows": z.array(workflowSchema),
  "/v1/units": z.array(unitSchema),
  "/v1/runs": z.array(runSchema),
  "/v1/catalogue": z.array(
    z.object({
      id: z.string(),
      data: z.object({
        sku: z.string(),
        name: z.string(),
        visual_description: z.string(),
      }),
    }),
  ),
};
const contextSchema = z.object({
  workflow: workflowSchema.extend({
    runs: z.array(runSchema),
    events: z.array(
      z.object({
        id: z.string(),
        created_at: z.string(),
        run_id: z.string().nullable(),
        data: z.object({
          name: z.string(),
          actor: z.string(),
          detail: z.unknown(),
        }),
      }),
    ),
  }),
  unit: unitSchema,
  images: z.array(
    z.object({
      id: z.string(),
      bytes: z.number(),
      dimensions: z.array(z.number()),
      taken_at: z.string(),
    }),
  ),
  actions: z.record(z.string(), permissionSchema),
  run_actions: z.record(
    z.string(),
    z.object({ review: permissionSchema, retry: permissionSchema }),
  ),
});
