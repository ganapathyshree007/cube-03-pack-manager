# sharonmedithi0304 · Receiving Manager

## What this is

A Receiving Manager that checks received inventory against PO/product
expectations and produces an evidence-backed PASS / FAIL / UNCERTAIN
verdict. The vision model (not yet connected to a real provider) only
observes; a deterministic engine (`agent/inspection_agent.py`) decides.

## Run it

```
pip install streamlit pandas
streamlit run submissions/sharonmedithi0304/app.py
```
Run from the repository root so `data/receiving_sample.csv` resolves.

## Run the tests

```
cd submissions/sharonmedithi0304/agent
python3 -m unittest test_vision_adapter -v
python3 -m unittest test_model_client -v
python3 -m unittest test_review_layer -v
```
**Result: 52/52 passing.** See `eval-report.md` for the full breakdown
and for why this is a software-test result, not a vision-accuracy number.

## Layout

```
submissions/sharonmedithi0304/
├── README.md         ← this file
├── ARCHITECTURE.md    ← inspection flow, vision boundary, demo UI scope, known contract gap
├── eval-report.md     ← verified test results vs. (not yet performed) vision evaluation
├── app.py             ← Streamlit demo UI, calls inspection_agent directly (see ARCHITECTURE.md §4)
├── contract/
│   └── evidence-record.json   ← 6-check draft contract; does not yet match the 10-check runtime shape (see known gap below)
└── agent/
    ├── inspection_agent.py    ← deterministic decision engine (not reimplemented anywhere else)
    ├── vision_adapter.py      ← one-call-per-unit vision boundary, validates and fails open
    ├── model_client.py        ← provider-agnostic interface + FakeModelClient test double
    ├── test_vision_adapter.py ← 13 tests
    ├── review_layer.py        ← contradictions, uncertainty guide, summary, override log, timeline, queue
    ├── test_review_layer.py   ← 33 tests
    ├── test_model_client.py   ← 6 tests
    ├── test_agent.py          ← demo script (not an automated test; no assertions)
    └── fixtures/
```

## Status

| Face | Deliverable | Status |
|---|---|---|
| 1 | Customer letter, PR/FAQ, one-pager | ☐ not done |
| 2 | CLAUDE.md | ☐ not done |
| 3 | Headless agent on fixtures | ☑ `inspection_agent.py` + `vision_adapter.py`, 19/19 tests passing |
| 4 | Eval report | ☑ software-test results documented; vision-model evaluation explicitly marked not performed |
| 5 | Evidence record page | ☑ `app.py`: summary, expected vs received, WHY trace, conflicts, unknowns, override, timeline, queue, evaluation, failure modes |
| 6 | Cross-pod contract | ☒ `contract/evidence-record.json` exists but has a known mismatch with the runtime shape — not reconciled |

## Known limitations (see ARCHITECTURE.md and eval-report.md for detail)

- No real vision model is connected — `model_client.py` ships only a
  deterministic fake test double.
- `app.py` calls `inspection_agent.inspect_unit()` directly, not
  `vision_adapter.py`, because the sample dataset has no real images to
  run vision inference against. `vision_adapter.py` is real and tested,
  just not wired into this demo.
- `colour`, `variant`, `components` show `UNCERTAIN` for every sample row
  (the CSV has no observed values for them — correct behavior, not a bug).
- The organization filter in `app.py` is a demo data filter, not tenant
  isolation — no database, no row-level security.
- `contract/evidence-record.json` (6 checks) does not match the runtime
  result (10 checks). Documented, not silently changed.
- No held-out vision evaluation set exists in this repository yet.
- Operator overrides are session-only (no database).

## Kill condition

If the vision model cannot reliably distinguish "insufficient evidence"
from "matches expectation" — i.e. it collapses `UNCERTAIN` into `PASS`
under any prompting — the model-facing layer is not usable, regardless
of how well the deterministic engine behind it performs. This has not
yet been tested against a real model because none is connected.

## Why this is different (concrete design choices)

- UNCERTAIN is a first-class verdict; an expected value alone never produces PASS.
- Every UNCERTAIN names what is unknown, why, and what evidence would resolve it.
- Evidence conflicts are flagged and routed to review; they are not turned into FAIL.
- Overrides are append-only and keep the original automated verdict and a required reason.
- The Evaluation tab separates software tests from vision accuracy, which is stated as not performed.

## Demo flow (60-90 s)

1. Sidebar > "Quantity + damage": expected vs received, FAIL, open WHY.
2. "Evidence conflict (colour)": conflict banner, "What is unknown" table.
3. "Identity uncertain": record an ACCEPT with a reason; the automated verdict stays UNCERTAIN; see the timeline.
4. Attention queue tab, then Evaluation tab ("Vision accuracy evaluation not performed").

## Deploy

Streamlit Community Cloud: point at this repo, main file `submissions/sharonmedithi0304/app.py`, `requirements.txt` at repo root. No secrets needed.
