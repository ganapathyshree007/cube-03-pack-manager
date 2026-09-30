# Submission readiness

Build opens 25 Sep 2026 09:00 IST; submission opens 27 Sep; deadline 1 Oct 2026 18:00 IST. Check any separate organizer cutoff. No resubmission. Publishing and one-shot submission require explicit participant instructions.

## Participant-provided submission checklist audit — 30 September

| Required item | Verified status |
|---|---|
| Official track fork and implementation pushed | Public fork verified; current source pushed. This does not establish feature completion. |
| README: problem, solution, setup, usage, assumptions/limitations | Covered; model and cloud limitations explicitly disclosed. |
| ARCHITECTURE: components, flow, model use, engineering decisions | Covered, including one-call reservation, deterministic comparison, RLS and human review. |
| Demo video and accessible link | Missing. Script exists; no recording or uploaded link. |
| Live deployment URL, if applicable | Missing. India-only Azure eligibility blocked. Checklist wording is conditional; do not assume it waives requirements elsewhere. |
| Published Round 2 LinkedIn post with track and CodeQuesters/Sydon.AI tags | Missing. Draft only; official tag selection and publication pending. |
| All submission links accessible | Repository checked; video, post and deployment links do not yet exist. |

Do not mark submission ready from repository/tests alone. A local recording can truthfully demonstrate orders, evidence capture, pending status, review and export; it cannot demonstrate live AI results while the provider is unconfigured. Genuine model testing and evaluation remain uncompleted engineering goals even though this short submission checklist does not list a dataset upload.

- [x] Clone supplied fork; read rules/problem statement/data.
- [x] Implement conservative one-call workflow, UI and provisional evidence export.
- [x] Test real PostgreSQL isolation, pending evidence, review and retake.
- [x] Author architecture, evaluation protocol, deployment runbook and submission drafts.
- [x] Compile Bicep templates locally.
- [x] Implement optional isolated demo quotas/expiry, pagination, product archival and packed acknowledgement.
- [ ] Verify these controls in the deployed environment.
- [ ] Confirm official evidence schema and unit-budget interpretation.
- [ ] Supply genuine authorized products/images and provenance.
- [ ] Configure/capability-test Azure; run real inference locally.
- [x] Receive India-only scope and existing $100 student-credit authorization with a 30-day target.
- [ ] Resolve region/model access, verify remaining credit/expiry, deploy and verify hosted sign-in/inference with laptop off.
- [ ] Run frozen held-out evaluation with two prior independent human labels.
- [ ] Generate actual official-schema evidence example.
- [x] Test one-call crash recovery and competing workers locally.
- [x] Build and execute Docker image in GitHub CI.
- [ ] Run cloud reliability checks.
- [ ] Record/verify live demo video.
- [x] Commit/push source within authorized window; check links.
- [ ] Approve/publish LinkedIn post with tags and record URL.
- [ ] Check final official form for additional requirements.
- [ ] Explicitly authorize one-shot submission before deadline.

Locally implemented/tested is distinct from real-provider tested, cloud deployed, public URL verified and held-out evaluated. Those latter gates remain pending.
