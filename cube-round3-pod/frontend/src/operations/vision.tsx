import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { OperationsApi } from "./api";

type Item = {
  instance_id: string;
  candidates: string[];
  variant: string | null;
  match_status: string;
  evidence: string;
  visible_attributes: string[];
  model_score: number | null;
  region: { x: number; y: number; width: number; height: number } | null;
};
type Evidence = {
  record_id: string;
  stage: string;
  decision: { verdict: string; reason: string };
  payload: {
    visual_observations?: {
      source_image_id: string;
      totals?: { sku: string; variant: string; count: number }[];
      instances: Item[];
      suppressed: unknown[];
      region_limitation: string;
    };
    comparison?: {
      sku: string;
      expected: number;
      observed: number;
      difference: number | null;
    }[];
    basis?: string;
    deterministic_decision?: string;
  };
};

function Scene({
  api,
  id,
  items,
}: {
  api: OperationsApi;
  id: string;
  items: Item[];
}) {
  const [url, setUrl] = useState("");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    setUrl("");
    setFailed(false);
    void api
      .image(id)
      .then((blob) => {
        if (active) {
          objectUrl = URL.createObjectURL(blob);
          setUrl(objectUrl);
        }
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [api, id]);
  if (failed)
    return (
      <p role="alert">
        This private photograph is unavailable or access was denied.
      </p>
    );
  if (!url) return <p>Loading private photograph…</p>;
  return (
    <div style={{ position: "relative", maxWidth: 680 }}>
      <img
        src={url}
        alt="Primary package photograph used for counting"
        style={{ display: "block", width: "100%" }}
      />
      {items.map((i) =>
        i.region ? (
          <div
            key={i.instance_id}
            aria-label={`Model region ${i.instance_id}`}
            style={{
              position: "absolute",
              left: `${i.region.x * 100}%`,
              top: `${i.region.y * 100}%`,
              width: `${i.region.width * 100}%`,
              height: `${i.region.height * 100}%`,
              border: "2px solid #f59e0b",
              pointerEvents: "none",
            }}
          >
            <span style={{ background: "#fff", color: "#111", fontSize: 12 }}>
              {i.instance_id}
            </span>
          </div>
        ) : null,
      )}
    </div>
  );
}

export function VisionEvidence({
  api,
  workflowId,
}: {
  api: OperationsApi;
  workflowId: string;
}) {
  const [open, setOpen] = useState(false);
  const query = useQuery({
    queryKey: ["official-vision", workflowId],
    enabled: open,
    queryFn: async () => {
      const rows = await api.get<{ id: string }[]>(
        `/v1/pod/workflows?platform_id=${encodeURIComponent(workflowId)}`,
      );
      const details = await Promise.all(
        rows.map((r) =>
          api.get<{ evidence: Record<string, Evidence> }>(
            `/v1/pod/workflows/${encodeURIComponent(r.id)}`,
          ),
        ),
      );
      return details
        .flatMap((d) => Object.values(d.evidence))
        .filter((e) => e.stage === "pack");
    },
    refetchInterval: open ? 5000 : false,
  });
  return (
    <details onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>Visual inspection evidence</summary>
      <p>
        Experimental model observations, deterministic comparison and human
        reviews are separate. No automatic clearance is implied.
      </p>
      {query.isLoading && <p role="status">Loading saved inspection…</p>}
      {query.error && (
        <p role="alert">
          Inspection evidence could not be loaded. No success is assumed.
        </p>
      )}
      {query.data?.length === 0 && (
        <p>
          No saved model observations. Live inspection requires a configured
          provider, verified route and unused whole-unit call budget.
        </p>
      )}
      {query.data?.map((e) => (
        <article key={e.record_id}>
          <h3>
            {e.decision.verdict} · {e.payload.basis || "Inspection status"}
          </h3>
          <p>{e.decision.reason}</p>
          {e.payload.visual_observations && (
            <>
              <Scene
                api={api}
                id={e.payload.visual_observations.source_image_id}
                items={e.payload.visual_observations.instances}
              />
              <p>{e.payload.visual_observations.region_limitation}</p>
              <p>
                Deterministic result: {e.payload.deterministic_decision}.
                Overlapping detections removed:{" "}
                {e.payload.visual_observations.suppressed.length}.
              </p>
              <div style={{ overflowX: "auto" }}>
                <table>
                  <caption>
                    Expected versus observed — unknown differences remain
                    unresolved
                  </caption>
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Expected</th>
                      <th>Observed visible</th>
                      <th>Difference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.payload.comparison?.map((r) => (
                      <tr key={r.sku}>
                        <td>{r.sku}</td>
                        <td>{r.expected}</td>
                        <td>{r.observed}</td>
                        <td>{r.difference ?? "Unresolved"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <h4>Supported visible totals by SKU and variant</h4>
              <ul>
                {e.payload.visual_observations.totals?.map((t) => (
                  <li key={`${t.sku}:${t.variant}`}>
                    {t.sku}
                    {t.variant ? ` / ${t.variant}` : ""}: {t.count}
                  </li>
                ))}
              </ul>
              <ul>
                {e.payload.visual_observations.instances.map((i) => (
                  <li key={i.instance_id}>
                    <strong>
                      {i.instance_id}: {i.match_status}
                    </strong>{" "}
                    — {i.candidates.join(", ") || "Unknown product"}
                    {i.variant ? ` / ${i.variant}` : ""}
                    <p>{i.evidence}</p>
                    <p>{i.visible_attributes.join("; ")}</p>
                    {i.model_score !== null && (
                      <p>Uncalibrated model score: {i.model_score}</p>
                    )}
                  </li>
                ))}
              </ul>
              <p>
                Use the existing evidence upload and stage review controls below
                to record a new photograph or attributed human review. A
                recapture does not reset the model-call budget.
              </p>
            </>
          )}
        </article>
      ))}
    </details>
  );
}
