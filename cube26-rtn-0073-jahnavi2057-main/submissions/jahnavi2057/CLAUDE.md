# CLAUDE.md: Constraints & Hard Rules

## Hard Rules
* **Evidence before decision:** Always collect and assess evidence before assigning a disposition.
* **UNCERTAIN is first-class:** Do not force ambiguous or low-quality evidence into a PASS or FAIL. `UNCERTAIN` is a valid, correct response.
* **Never hallucinate visual evidence:** If it is not clearly visible in the image, do not claim it is there.
* **Never silently discard failed cases:** Implement fail-open behavior. Route failures to `pending_review`.
* **Preserve original decisions when overridden:** The initial agent decision must remain intact and viewable after an operator applies an override.
* **Enforce tenant isolation server-side:** An organization must never be able to view, query, or infer data from another organization.
* **Never expose secrets:** Environment variables must handle all API keys. Do not commit secrets.
* **Do not treat synthetic data as authoritative rules:** The `returns_sample.csv` is dummy data. Do not use its output as ground truth policy.
* **Do not invent condition taxonomies:** Use only the authoritative condition scale (New, Renewed, Used - Like New, Used - Very Good, Used - Good, Used - Acceptable, Unacceptable).
* **Do not claim evaluation accuracy without measurement:** Numbers must not be fabricated.
* **Do not claim an AI decision occurred when running mock/demo mode.**
* **New/unseen images must be analyzed as actual image evidence:** Do not mock out image processing when an API is available.
* **Do not map an uploaded image directly to a seed CSV row and copy its decision.**
* **Critical uncertainty routes to review:** Identity or completeness uncertainty must result in `pending_review`.
* **Fail-open behavior is mandatory:** Network or API failures must not drop records.
* **Keep evidence machine-readable:** Ensure JSON output aligns with the agreed schema.
* **Preserve traceability:** The reasoning for every decision must be explicit.

## Forbidden Language / Claims
* Do not use the phrase "100% accurate".
* Do not claim the system is "always correct".
* Do not claim decisions were "AI verified" when mock mode was used.
* Do not state the system is "production ready" unless empirically demonstrated.
* Do not invent Amazon policy claims.
* Do not fabricate evaluation results.
