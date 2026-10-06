import React from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { VisionEvidence } from "../src/operations/vision";
export function mount() {
  const image = new Blob([new Uint8Array([])], { type: "image/png" });
  const fake = {
    get: async (path: string) =>
      path.includes("platform_id")
        ? [{ id: "fixture" }]
        : {
            evidence: {
              p: {
                record_id: "p",
                stage: "pack",
                decision: {
                  verdict: "UNCERTAIN",
                  reason: "Software fixture, not inference",
                },
                payload: {
                  basis: "experimental_model",
                  deterministic_decision: "uncertain",
                  comparison: [
                    { sku: "A", expected: 2, observed: 1, difference: null },
                  ],
                  visual_observations: {
                    source_image_id: "test",
                    instances: [
                      {
                        instance_id: "one",
                        candidates: ["A"],
                        variant: null,
                        match_status: "uncertain",
                        evidence: "Unclear label",
                        visible_attributes: [],
                        model_score: null,
                        region: null,
                      },
                    ],
                    suppressed: [],
                    region_limitation: "No model regions supplied",
                  },
                },
              },
            },
          },
    image: async () => image,
  };
  const mount = document.createElement("div");
  document.body.replaceChildren(mount);
  createRoot(mount).render(
    React.createElement(
      QueryClientProvider,
      { client: new QueryClient() },
      React.createElement(VisionEvidence, { api: fake, workflowId: "fixture" }),
    ),
  );
}
