# Eval Report

This report distinguishes two different things on purpose. Do not read
one as evidence for the other.

## 1. Software tests (verified, automated, deterministic)

**Result: 52/52 passing** (19 pre-existing + 33 new in `test_review_layer.py`).

Run with:
```
cd submissions/sharonmedithi0304/agent
python3 -m unittest test_vision_adapter -v
python3 -m unittest test_model_client -v
python3 -m unittest test_review_layer -v
```
All three at once: `python3 -m unittest test_vision_adapter test_model_client test_review_layer`.
(`python -m unittest discover` from the submission root currently reports
0 tests, because `agent/` has no `__init__.py` and its modules use flat
imports. Run from inside `agent/`, as above, or point discovery directly
at `agent/`: `python -m unittest discover -s submissions/sharonmedithi0304/agent -p "test_*.py"`.)

Breakdown:
- `test_vision_adapter.py` — 13 tests. Covers: one call per unit, evidence
  preservation, malformed/type-invalid/JSON-string responses, model
  exceptions failing open, empty `image_refs` producing `UNCERTAIN` with
  zero model calls, ambiguous observations, evidence referencing an
  unavailable image rejected, malformed evidence rejected, optional
  `location` valid/invalid handling.
- `test_model_client.py` — 6 tests. Covers the `FakeModelClient` test
  double (predefined response, payload recording, call count, injected
  exception) plus one adapter integration test asserting exactly one
  model call, a `PASS` verdict on a fully consistent fixture, all 10
  checks present, and evidence traced to the supplied `source_ref`.

These tests verify **code behavior**: that the deterministic engine
computes the verdict it should given a known input, and that the adapter
enforces its validation and fail-open rules. They do not measure
real-world vision accuracy, because no real vision model is called
anywhere in this repository.

## 2. Vision model evaluation

**Status: not performed. No real vision model is connected.**

`agent/model_client.py` defines a provider-agnostic interface and a
deterministic fake test double only (`FakeModelClient`). No provider has
been selected, no API key is configured, and no inference call to any
real model has been made in this repository.

Consequently, there is no FP/FN/UNCERTAIN breakdown, no agreement score,
and no accuracy figure to report for vision observation quality, because
none has been measured. Any number here would be invented; per project
rules, none is given.

`data/README.md` describes an intended held-out, two-labeller-agreed
evaluation set of ~50 units for this purpose. That set is not present in
this repository.

## 3. Dataset characteristics (not an evaluation)

`data/receiving_sample.csv` is 100 rows of reference/dummy data used for
schema design, per `data/README.md`. The counts below describe this CSV
as shipped. They are not accuracy figures and this file is not a
held-out evaluation set.

| Characteristic | Count |
|---|---|
| Total records | 100 |
| `org_demo_alpha` | 67 |
| `org_demo_bravo` | 33 |
| `identity_match = yes` | 94 |
| `identity_match = no` | 3 |
| `identity_match = uncertain` | 3 |
| `carton_damage = none` | 74 |
| `carton_damage = crushing` | 11 |
| `carton_damage = tears` | 6 |
| `carton_damage = uncertain` | 5 |
| `carton_damage = water` | 4 |
| `unit_damage = none` | 89 |
| `unit_damage = uncertain` | 4 |
| `unit_damage = crushing` | 3 |
| `unit_damage = tears` | 2 |
| `unit_damage = water` | 2 |

These same counts are reproduced live, with quantity/carton/units-per-carton
mismatch counts and quality-flag distribution, on the "Dataset Overview"
tab of `app.py`.

## 4. What this means for the demo app

`app.py` runs every one of the 100 sample rows through the real
`inspection_agent.inspect_unit()` (verified: processed with 0 errors).
`colour`, `variant`, and `components` return `UNCERTAIN` for all 100
rows, because the sample CSV has no `observed_colour` / `observed_variant`
/ `observed_components` fields — correct behavior given the missing
evidence, not a defect.

## 5. Deterministic decision output over the 100 sample rows (not accuracy)

Produced by running every row through `inspect_unit()` + `review_layer`.
The CSV has no independent ground truth, so this describes behaviour, not correctness.

| Output | Records |
|---|---|
| Final verdict FAIL | 41 |
| Final verdict UNCERTAIN | 59 |
| Final verdict PASS | **0** |
| Records with an evidence conflict | 12 |

**Finding:** no sample row can reach PASS, because colour, variant and components
have no observed values in the data, so those checks are UNCERTAIN on all 100 rows.
This is the engine refusing to treat an expected value as evidence. A PASS path is
exercised only in unit tests, using fully observed inputs.

Failure-mode counts (records hitting each mode; one record can hit several):
missing colour/variant/component evidence 100 each; quantity mismatch 15;
carton or units-per-carton mismatch 15; damage 23; damage unresolved 9;
identity uncertain 3; identity mismatch 3; conflicting evidence 12.

## 6. Priority formula (attention queue)

`score = 10 x FAIL checks + 6 x evidence conflicts + 2 x UNCERTAIN checks (+20 if identity FAIL)`;
ties broken by record_id. Deterministic, not a model score.

## 7. Contradiction rules (agent/review_layer.py)

C1/C2/C3: quality flag (wrong_colour / wrong_variant / missing_components) vs a
colour / variant / components check that is UNCERTAIN or PASS.
C4: quantity PASS while carton or unit damage is UNCERTAIN.
C5: quantity PASS while carton count or units-per-carton FAILS.
C6: identity "yes" while wrong_variant / wrong_colour is flagged.
A conflict never changes a check verdict. It routes the unit to review, and
turns an engine PASS into UNCERTAIN.

## 8. Known limitations

- No vision evaluation (section 2). No FP/FN numbers exist.
- Overrides live in Streamlit session state (optional JSONL via `OverrideLog(path=...)`
  in code, not enabled in the UI). No database.
- Org filter is a display filter, not tenant isolation.
- UI behaviour was smoke-tested with Streamlit's AppTest, not with automated browser tests.
- `contract/evidence-record.json` still lists 6 checks vs 10 at runtime.
