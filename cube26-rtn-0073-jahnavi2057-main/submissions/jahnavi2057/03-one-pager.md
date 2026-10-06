# One Pager: Returns Manager

## Problem
Processing customer returns requires fast, accurate operational judgment. Operators must verify product identity, check for completeness against an expected parts list, grade the condition accurately, and decide the next step (disposition). Doing this manually leads to inconsistent grading, missed missing parts, and misidentified products, all of which directly impact margin and downstream customer satisfaction.

## Solution
Returns Manager is an evidence-backed application that streamlines the return inspection process. It leverages visual evidence to deterministically check identity, completeness, and condition against authoritative reference data and condition scales. It ensures ambiguous cases are flagged as `UNCERTAIN` for human review, and produces a highly structured evidence record for every return.

## Workflow

```text
Return Evidence
      ↓
Identity
      ↓
Completeness
      ↓
Condition
      ↓
Disposition
      ↓
Evidence Record
```

## Key metrics

| Metric                | Definition | Target / Measurement |
| --------------------- | ---------- | -------------------- |
| Identity accuracy     | % of items correctly identified against reference | > 95% |
| Completeness accuracy | % of items where missing/present parts are correctly identified | > 90% |
| Condition accuracy    | % of items graded correctly according to authoritative scale | > 85% |
| Disposition accuracy  | % of items assigned the correct downstream routing | > 90% |
| UNCERTAIN rate        | % of cases routed to human review due to ambiguity | < 20% |
| Human review rate     | Total % of cases requiring human review | < 25% |
| False positive rate   | Rate at which failed returns are incorrectly passed | < 5% |
| False negative rate   | Rate at which valid returns are incorrectly failed | < 5% |
| Inspection latency    | Time taken for automated inspection | < 5000ms |

*(Note: Actual measurements will be populated upon completion of the evaluation phase).*

## Kill condition
If evaluation demonstrates that the system cannot reliably distinguish critical identity/completeness failures from valid returns without unacceptable false positives/false negatives, the autonomous decision workflow should not proceed to production and must remain review-assisted.
