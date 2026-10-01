# Local model research results — 1 October 2026

**Inference is connected; reliable product identification and counting are NOT established.**

Seven local research requests used distinct source-day groups with one request per attempted unit. Failed units were not retried. These are development experiments, not a held-out accuracy benchmark. The initial five integration attempts all failed; two additional distinct scenes tested the instruction-model correction. No Azure model calls were made.

| RPC case | Result |
|---|---|
| 220 | Input exceeded context capacity; saved pending. |
| 228 | Large multi-image request timed out; saved pending. |
| 1117 | Separate images still exceeded the smaller context; saved pending. |
| 334 | Thinking model exhausted output allowance; saved pending. |
| 553 | Thinking model produced no final answer within allowance; saved pending. |
| 2528 | Instruction model returned valid JSON in 27.016 seconds, but described 15 catalogue references rather than the 6 scene items. No expected SKU identity was verified. Decision: UNCERTAIN. |
| 1346 | Reordered images and SKU-constrained output still enumerated references and exhausted context. Saved pending; no successful counts asserted. |

Current adapter: explicit `qwen3-vl:2b-instruct`, one request with a labelled reference sheet and primary image, strict observation validation, deterministic reconciliation, no retries. Runtime: Ollama 0.35.0 on RTX 3050 6GB / approximately 16GB RAM. The bare 4B tag resolved to a thinking model; disabling thinking did not produce a final answer within the configured output cap.

The pipeline saved all evidence and refused to treat incomplete output as approval. Local model results now require human review even if their raw checks would pass. This safeguards operations but does not fix recognition accuracy. Further model/prompt evaluation is required; the project is not a validated automatic inspection system.

RPC original category IDs were retained. Training-reference crops use official training bounding boxes; checkout images were not cropped using annotations. Expected checkout counts were used only for scoring, never supplied to the model. Original photographs, cropped-reference provenance and detailed reports remain in ignored `.local/` for local noncommercial research. Source: https://rpc-dataset.github.io/ ; CC BY-NC-SA 4.0. No claim is made about the user's products, hidden contents, or real shipping-box performance.

Supabase authentication code, private-storage adapter and free Render configuration are prepared. Dedicated cloud resources, credentials and hosted end-to-end verification remain incomplete. No public deployment URL is claimed.
