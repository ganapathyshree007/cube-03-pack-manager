# Recovery reconnaissance findings

Recorded 6 October 2026 against local commit 13309f7. No rules or runtime behavior changed. Existing organiser findings F-07 through F-15 remain in decisions.md.

| ID | Evidence / conflict | Consequence and proposed handling (pending approval) |
|---|---|---|
| RCY-01 | Task names data/upstream and data/README.md; neither exists. Actual data is under data/sample with its own README. | Ask whether to use these as synthetic import fixtures; preserve samples unchanged. |
| RCY-02 | No normalized charge/report/claim tables; current events have incomplete monetary/context fields. | New internal persistence required; do not invent missing currency, marketplace, fee date or type for old events. |
| RCY-03 | Returns create RETURN-* internal units with original_unit_id/original_order_id links. Operational worker retrieves only same-workflow runs. | Join explicit tenant-scoped relationships; unit_id equality alone is insufficient. |
| RCY-04 | Organiser F-08: Receiving IDs can mean PO lines; fee IDs mean single units. Commerce units can also represent multi-item orders. | Exact ID is not proof of identical physical scope. Preserve scope and quantities; conflict -> UNCERTAIN. |
| RCY-05 | No custody-transfer timestamps in sample columns; weight-tier has no measured weight/dimensions; F-10/F-11 flag supplier/channel and FBA-return custody ambiguity. | Cannot adjudicate these from generic PASS or sample timestamps. Require sourced custody/measurement evidence. |
| RCY-06 | Hard constraint says missing evidence -> UNCERTAIN/human review; Phases 3/4 also allow missing evidence -> SILENT/no claim. Official contract permits SILENT with needs_human=false only if nothing remains for a person to decide. | Ask for distinction; recommend required missing/conflicting evidence always review, not silent dismissal. |
| RCY-07 | Hard constraint 5 allows placeholder claims behind human authorization, while Phase 4 requires placeholder rules to retain CLAIM_ELIGIBILITY_UNVERIFIED fallback. | Ask before enabling claim eligibility/export. Recommend placeholders yield review-only synthetic previews; human action cannot manufacture policy authority. |
| RCY-08 | Task prefers unit_id first; contract section 9 says prefer refs when bare ID scope is ambiguous. | Strong IDs generate candidates, but all supplied identifiers/scope must agree; never force a match on a bare ID. |
| RCY-09 | Existing RunOutput.claim_supported is Literal[False]; official adapter returns unsupported_claim, which schema permits as free text but is not a recommended Recovery outcome. | Add adjudicator before fallback; map supported new outcomes through official contract, internal projection additively/versioned. Never weaken safety tests merely to permit claims. |
| RCY-10 | Existing sample expected outcomes are explicitly generated from organiser stubs; flags/amounts are dummy data. No independent claim labels or authoritative channel policies supplied. | Cannot call sample agreement real claim precision. Independent evaluation remains blocked pending labels/sources. |
| RCY-11 | Fee CSV includes damaged_in_warehouse (one row), beyond four proposed initial rules; nine rows have amount 0.00. | Retain unsupported types and ambiguous zero amounts for review; do not drop rows or infer entitlement. |
| RCY-12 | Official previous_evidence is defined as same-workflow evidence; new requirement includes separate return workflows. | Use validated original envelopes with explicit linked provenance in additive context/payload, preserve source subjects; document mapping before Phase 3. Do not change organiser envelope. |
| RCY-13 | CSV/XLSX normalization loses verbatim encoding/quoting/formulas without original file retention. | Preserve tenant-private original bytes/hash and row/sheet positions; expose safe values without executing spreadsheet formulas. |

No external issues or messages have been posted. These are local findings for user/team review.
