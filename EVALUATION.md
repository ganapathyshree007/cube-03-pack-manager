# Evaluation — results unreported

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
