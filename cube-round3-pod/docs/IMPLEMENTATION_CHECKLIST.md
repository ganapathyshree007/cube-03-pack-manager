# Implementation checklist — local commerce continuation

- [x] Inspect baseline, rules, schema and migration history; preserve prior commits.
- [x] Restore omitted evaluation module; baseline full suite: 253 tests passed.
- [x] Add tenant-scoped official workflow queue/store and real-contract adapters.
- [x] Add migrations 003 (official records) and 004 (commerce records); preserve existing data.
- [x] Add versioned product policy with explicit unknown-policy/Pod holds and branch guards.
- [x] Add role-separated customer catalogue, transactional stock/order requests and owned returns.
- [x] Add event/evidence-gated Recovery, linked inventory receipts and no checkout Receiving event.
- [x] Add customer UI, policy/setup controls and persisted-data analytics.
- [x] Expanded concurrency/failure verification: 271 backend tests passed with PostgreSQL enabled.
- [x] Browser verification: two real local workflows and six labelled fixture tests passed; mobile navigation regression fixed.
- [x] Production build and scoped Ruff checks passed; current runbook and verification documented.
- [x] Local changes reviewed for this checkpoint; retained on integration/pod7-operations without publishing.
- [ ] Verified Pod assignment and shared fork (external information still unavailable).
- [ ] Actual vision inference and held-out accuracy (missing safely configured provider and labels).

Latest instruction: local-only. Do not publish/deploy, create paid resources or edit teammate repositories. The old organiser CLI remains labelled sample-stub execution; application adapters never replay it as real observations.

Remaining implementation limits: complete official-evidence UI, separate declared response models for every commerce projection, automatic cancellation stock release/return restocking, teammate automatic visual adapters and physical phone-camera verification. None is represented as completed.
