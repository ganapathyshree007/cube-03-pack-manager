# Evaluation protocol — no results yet

Use real authorized merchandise/photos and record provenance. Generated images are not operational held-out evidence. Use a separate development set for prompt/capture/threshold tuning. Split by physical scene and capture session; alternate views and transformations are not independent units. Keep test image access away from prompt tuning.

Proposed 64 unique held-out cases: 6 per participant-specified scenario (48) plus 16 covering occlusion, glare, unreadable size, barcode/appearance conflict, filler ambiguity and other hard cases. The starter PCK statement confirms the content/quantity/extra checks but does not enumerate eight official labels; retain participant scenario coverage without claiming organizer-defined labels. Minimum per handbook: 50 unseen vision units where applicable. No unseen-SKU claim unless separately tested.

Copy labels-template.csv independently for reviewer A and B. Each actual person labels before any agent evaluation and without seeing the other's labels or model output. Capture visible evidence first; keep known physical contents distinct. Lock and hash the originals. An adjudicator records disagreements in adjudication-template.csv without overwriting either original. Abstentions/unknowns are valid; do not force a known physical answer from an ambiguous photo.

Freeze dataset manifest, hashes, split, prompt/config/model versions and capture protocol before evaluation. A case with changed contents is a new setup; duplicate captures remain grouped. Run original automated decisions before overrides. Keep operational failures in reporting with their own count; do not quietly exclude them from coverage or error denominators.

Required report:

- Three-class decision confusion matrix (SEAL, STOP & FIX, UNCERTAIN) and separate operational-failure tally.
- Per-check confusion matrices; raw human agreement and Cohen's kappa on paired nonmissing labels. Report paired count and exclusions. Undefined kappa (expected agreement=1) is null, not 1.
- Incorrect approval among defective cases: defective cases receiving SEAL / all physically defective cases.
- Error among approvals: defective cases receiving SEAL / all SEAL cases.
- Uncertainty rate: UNCERTAIN / all attempted cases; automatic decision coverage: completed SEAL or STOP & FIX / all attempted cases.
- False stops: STOP & FIX on adjudicated clearly correct, sufficiently visible cases / all such cases.
- Exact quantity accuracy across all SKU/case pairs with known physical quantities; unknown predictions count as not exact. Also report exact-prediction coverage.
- SKU precision/recall using one-to-one matching of distinct primary-view instances, only accepting verified exact SKU identities. Define eligibility for visually unresolvable ground truth; report excluded/unknown counts separately.
- Latency p50/p95 with definition (submission-to-result and model execution separately), sample count, paused duration separately and failures included in latency summaries where available.
- Observed token usage and cost only with documented provider billing/pricing provenance; unavailable cost is null.

Every rate reports numerator and denominator; zero denominator means undefined/null. Generate charts only from recorded runs. Zero observed harmful approvals in 50 cases does not prove zero risk. Tuning after final results converts that set into development data and requires a new unseen set.

The templates contain headers only. No reviewers, photos or labels have been simulated. A production evaluation runner must consume the real starter's export schema after it is obtained.
