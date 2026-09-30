# Legacy evidence mapping and 1.1 migration

**30 September update:** the participant supplied Evidence Contract 1.1 and the Recovery check registry. See [supplied-data review](SUPPLIED_DATA_REVIEW.md) for the implemented reader, exact hash serialization, legacy limitations and outstanding capture/review requirements. The table below describes the retained legacy workspace export, not the official contract. Do not present it as 1.1 compliance.

No organizer schema, sample JSON output or validation fixtures ship in the supplied starter. CSV rows are explicitly synthetic and are not an evidence contract. Handbook p. 11 supplies names and verdict meanings, not complete types/enums. Current schema_version is provisional-0.1; compatibility is unverified.

| Field | Current representation |
|---|---|
| record_id | attempt UUID |
| organization_id | authenticated organization |
| client_id | currently same as organization; distinct client boundary pending |
| agent | PCK |
| subject | order snapshot including unit_id, channel and lines |
| captured_at | server receipt time in UTC, not camera-freshness proof |
| operator_label | authenticated actor or explicit local development identity |
| images | stable UUID and original/transformed SHA-256 hashes |
| checks | positive keys, PASS/FAIL/UNCERTAIN, null confidence, detail, model_version, latency_ms, image_ids |
| outcome | seal/stop_and_fix/uncertain or null on pending; actor/time |
| overrides | attributed original/new human outcome, reason and timestamp |
| status | draft/queued/running/completed/pending |
| content_hash | SHA-256 of canonical export core |

Check keys: input_valid, view_sufficient, identity_verified, quantity_matches, no_unexpected_items. Outcome values are project choices, not confirmed official enums.

New uploads retain the original bytes privately alongside the normalized display/model JPEG. Original downloads require the same tenant authorization as image access (`GET /images/{id}/source`). The original may contain camera metadata; the normalized copy has metadata removed. Both copies are removed when a demo expires. Older uploads created before original retention was implemented return 404 for the source download; their original hash alone does not reconstruct those bytes.

Canonicalization uses sorted JSON object keys, compact separators, UTF-8, ensure_ascii=false, allow_nan=false; arrays retain order. Hash every export field except content_hash, overrides, superseded_by, packed_acknowledgement and compatibility. The hash changes when a pending record completes, but completed automated cores do not change with review/supersession. It is a checksum, not authentication, anchoring or WORM protection.

Clarify exact types/nullability, schema version, client ownership, check/outcome/status enums, image fields, hash algorithm and timestamp semantics. No real-inspection example exists yet. Software fixtures cannot fulfill that deliverable.
