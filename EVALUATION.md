# Evaluation — recognition remains unvalidated

This report separates software reliability, local development experiments, held-out evaluation and hosted verification. Post-competition work is explicitly identified; original snapshot `1e503a0` is preserved.

## Original seven development experiments

One attempted request per distinct recorded RPC scene-date unit, no retries. These were iterative prompt/runtime experiments, not independent human-labelled or held-out evaluation. Source IDs and individual attempt IDs are in [LOCAL_MODEL_RESULTS.md](docs/LOCAL_MODEL_RESULTS.md); ignored local manifests retain hashes and original category labels.

| RPC source ID | Outcome | Recognition result |
|---|---|---|
| 220 | Input context overflow | No observations |
| 228 | 600-second timeout | No observations |
| 1117 | Image token/context overflow | No observations |
| 334 | Output exhausted by thinking | No usable observations |
| 553 | Truncated/empty answer | No usable observations |
| 2528 | Valid JSON, 15 reported instances for 6 scene items | Counted catalogue tiles; zero expected SKU identities verified; UNCERTAIN |
| 1346 | Truncated reference-constrained response | Catalogue enumeration, duplicate IDs; no accepted counts |

Original seven: operationally successful exact order matches **0/7**; valid accepted observation responses **1/7**, and that one was incorrect (**0/1** completed exact matches). Provider/schema failures **6/7 (85.7%)**; returned UNCERTAIN **1/7 (14.3%)**, pending **6/7**; automatic SEAL/STOP coverage **0/7**. Unsafe SEAL count 0, but no labelled defective-order benchmark exists: unsafe-SEAL *rate is undefined*, not evidence of safety. False-stop rate is likewise unmeasured. Full identification/quantity accuracy and latency percentiles cannot be credibly estimated from these tuning cases. No Azure or hosted inference was used.

## Post-competition experiment: RPC 583

A separate eighth development unit used source `20181025-09-18-37-1.jpg`, source ID 583, SHA-256 `521eda31a6d497d5a159313f0b03a462d21c47256a98eddc0158e0a4706e4ce0`. Stable unit `RPC-SCENE-GROUP-20181025`; attempt `08fe2048-690d-4ca2-ad54-2cfe964a1a2a`; isolated development catalogue workspace `rpc-v6-development`. This is a genuinely new source date, not a renamed repeat of an earlier unit. The committed call reservation persists.

Selection used dataset labels to choose a small development scene with duplicates, and three scene categories plus one distractor. This is selection bias and cannot become a held-out test. References were cropped only from original **training** annotations; primary checkout image was never cropped or altered using annotations. Original files and derivative provenance remain private under `.local/`. Expected counts entered deterministic comparison only, never the visual prompt.

Model: `qwen3-vl:2b-instruct`; prompt `pack-observation-1-local-separated-v6-experimental`. Four separate 384-pixel identity references, 1024-pixel primary image last, 16,384 context, 4,000 output cap, temperature zero. Five image inputs; measured 6,359 input + 408 output tokens, within configured context. Exactly one request, no retry.

| Original RPC category (not merchant SKU) | Annotation count | Model-reported count |
|---|---:|---:|
| 64_dessert | 2 | 1 |
| 131_chocolate | 1 | 1 |
| 170_personal_hygiene | 1 | 1 |
| 87_drink (reference-only distractor) | 0 | 1 |

The model reported the correct *total* of four but the wrong composition: it replaced the second snack packet with a drink. It also copied reference SKU identifiers into `label_text` rather than readable packaging text. Thus exact order-level match **0/1**; exact counts for expected categories **2/3**, or **2/4** including the decoy category. These tiny development ratios are not benchmark accuracy. No one-to-one human instance labelling was done, so do not report precision/recall as validated recognition.

Decision: false **STOP & FIX** on this annotation-derived correct research order: **1/1** for this experiment. UNCERTAIN **0/1**, automatic-decision coverage **1/1**, provider/schema failures **0/1**. SEAL count **0/1**; unsafe-SEAL rate on defective orders remains undefined (zero defective units). The experimental review check remained present. Human review is required; this failure is not hidden by the valid JSON.

Model adapter latency **18,578 ms**; worker processing **18,750 ms**. This excludes operator waiting and is not hosted end-to-end latency. External API inference charge: none (local model); electricity/hardware cost not measured. No calibrated confidence or reliable-counting claim is supported.

Across all eight development attempts: **0/8 exact successful orders**, **6/8 provider/schema failures**, **2/8 accepted but incorrect observations**, **1/8 UNCERTAIN**, **6/8 pending**, **1/8 automatic STOP**, **0/8 SEAL**. Do not combine different prompts/models into a single accuracy benchmark.

## Failure modes and scenario coverage

Named failures: context overflow; timeout with CPU/GPU offload; thinking exhausting output; catalogue-reference contamination; unsupported/generic identities; duplicate instance IDs; lost identical-item count; hallucinated reference-only item; SKU-caption leakage into label evidence. Input separation reduces ambiguity in the request but did not solve local-model failure.

| Scenario | Deterministic software checks | Real vision evidence |
|---|---|---|
| Correct order | Covered by synthetic observations | RPC 583 falsely stopped; no validated success |
| Missing item | Covered, absence requires sufficient view | No labelled real packing test |
| Wrong item/variant | Covered for supported exact identities | No validated variant test |
| Extra item | Covered | Model hallucinated a decoy in RPC 583 |
| Wrong quantity | Covered | RPC 583 missed one repeated category |
| Multiple identical products | Covered | Failed repeated category in RPC 583 |
| Visually similar products | Ambiguity rules covered | No held-out labelled cases |
| Ambiguous photographs | Unknown/view/count rules covered | No independent human-labelled benchmark |
| Occlusion, blur/glare, unreadable size, unknown, empty box | Conservative policy fixtures | Required real photographs pending |
| Duplicate submit, timeout, stale review, private images | PostgreSQL/transport tests | Public deployment verification pending |

## Hosted and held-out gates

Hosted model metadata access was verified, but **0 hosted image inference calls and 0 public end-to-end inspections** have been verified. Private local RPC licensing/provenance does not authorize exposing research images in a public deployment. Google free-tier processing requires suitable permitted input photographs.

Held-out sample count **0/50 required minimum**; actual independent human reviewers **0/2**. Exact match, identification precision/recall, unsafe approval rate, false stops, uncertainty, coverage, provider failure rate and latency/cost for held-out/public evaluation are **not available**. Do not substitute backend test counts, an LLM's labels or the eight development cases.

## Held-out protocol and reproducibility

No held-out vision evaluation or actual human labeling has run. Software tests are not recognition accuracy measurements. Handbook requires at least 50 unseen vision units where applicable and two independent actual human reviewers before agent execution. Proposed 64-case target is a project choice.

See evaluation/PROTOCOL.md and header-only CSV templates. Freeze prompts/config/capture protocol; split by physical scene/session, never count extra angles as independent units. Label visible evidence separately from known contents. Preserve independent annotations and explicit adjudication; never substitute an LLM for a human reviewer.

Runner input is JSONL: case_id, physical_scene_id, split="held_out", configuration_frozen=true, scenario, reviewer_a/reviewer_b ({id, labeled_at ISO timestamp, decision}), agent_started_at, adjudicated_decision, automated_decision (null on failure), physical_defect (boolean); optional latency_ms, observed_cost, cost_provenance, checks ({check_key, truth, prediction}), quantities ({sku, truth, prediction, exact_count_known}), sku_matching ({true_positive, false_positive, false_negative}). Distinct reviewer IDs, prior timestamps and unique scenes are enforced. Real provenance still needs human audit.

```powershell
uv run python evaluation/evaluate.py REAL_FROZEN_RESULTS.jsonl output/evaluation
uv run --extra evaluation python evaluation/evaluate.py REAL_FROZEN_RESULTS.jsonl output/evaluation --plots
```

Reports decision/per-check confusion matrices; incorrect approval among defective cases; error among approvals; uncertainty and automatic coverage; operational failures; false stops for clearly correct boxes; exact quantity accuracy/coverage; exact-SKU precision/recall; p50/p95 latency and known costs. All rates include numerator/denominator; zero denominators and undefined kappa are null. Failures and unknown quantities are not quietly excluded. Use original automated outcomes, before human overrides.

SKU matching must be one-to-one exact identity on primary-view instances, not generic categories. Document visually unresolvable exclusions. Cost inputs must share one currency and pricing/billing provenance. Latency means submission-to-result, excluding human waiting, with pending failures separately identified.

Capture correct/wrong/missing/extra/count-error cases, repeated-unit overlap, unreadable variants, glare, blur, occlusion, filler ambiguity, barcode/appearance conflicts and image instructions. Engineering failures are separate reliability tests. No confidence calibration or zero-risk claim is made. Tuning after results makes that set development data and requires a new unseen set.
