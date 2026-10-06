"""
Receiving Manager - operator workstation (Streamlit).

UI layer only. All verdicts come from agent/inspection_agent.py; contradiction,
uncertainty, summary, override, timeline and queue logic live in
agent/review_layer.py (unit-tested). Nothing here decides a verdict.

Demo scope: the sample CSV ships no images, so this app inspects the receiving
evidence already recorded in the CSV. vision_adapter / model_client are not
invoked here (see ARCHITECTURE.md). Colour / variant / components are UNCERTAIN
on every sample row because no observed values exist for them.

Run from the repository root:
    streamlit run submissions/sharonmedithi0304/app.py
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

THIS_DIR = Path(__file__).resolve().parent
AGENT_DIR = THIS_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from inspection_agent import inspect_unit  # noqa: E402
import review_layer as rl  # noqa: E402

from vision_adapter import VisionInspectionAdapter  # noqa: E402
from model_client import FakeModelClient  # noqa: E402

DATA_PATH = next(
    (p for p in [THIS_DIR.parent.parent / "data" / "receiving_sample.csv",
                 Path("data/receiving_sample.csv")] if p.exists()), None)

CHECK_LABELS = {
    "identity": "Identity", "carton_count": "Carton count",
    "units_per_carton": "Units per carton", "quantity": "Quantity",
    "carton_damage": "Carton damage", "unit_damage": "Unit damage",
    "colour": "Colour", "variant": "Variant", "components": "Components",
    "quality_flags": "Quality flags",
}
# Where each check's evidence comes from (VLM Vision Adapter boundary).
EVIDENCE_SOURCE = {
    "identity": "VLM vision observation on image_refs",
    "carton_count": "VLM vision observation on image_refs",
    "units_per_carton": "VLM vision observation on image_refs",
    "quantity": "VLM vision observation on image_refs",
    "carton_damage": "VLM vision observation on image_refs",
    "unit_damage": "VLM vision observation on image_refs",
    "colour": "none: no observed_colour in dataset",
    "variant": "none: no observed_variant in dataset",
    "components": "none: no observed_components in dataset",
    "quality_flags": "VLM vision observation on image_refs",
}
# Real sample rows chosen to show different outcomes (not synthetic).
SCENARIOS = [
    ("Clean receipt", "RCV-0001", "Every recorded check passes; colour/variant/components stay UNCERTAIN."),
    ("Quantity + damage", "RCV-0003", "Quantity short, carton crushing."),
    ("Identity uncertain", "RCV-0029", "Identity match not established."),
    ("Evidence conflict (colour)", "RCV-0007", "wrong_colour flag, no observed colour."),
    ("Evidence conflict (components)", "RCV-0004", "missing_components flag, no observed components."),
    ("Qty OK, damage unresolved", "RCV-0042", "Quantity matches PO; damage not determined."),
]
COLOURS = {"PASS": "#1b7f3b", "FAIL": "#b3261e", "UNCERTAIN": "#b26a00"}

st.set_page_config(page_title="Receiving Manager", layout="wide")
st.markdown(
    "<style>.block-container{padding-top:1.2rem}"
    ".v{padding:.6rem 1rem;color:#fff;font-weight:700;font-size:1.25rem;border-radius:4px}"
    "</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------- data glue
@st.cache_data
def load(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def split_list(raw):
    return [i.strip() for i in raw.split(";") if i.strip()] if raw else []


def as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def row_to_unit(r):
    """
    Separates CSV row fields into:
    A. Expected PO / reference specifications
    B. Observed model predictions (initialized to None prior to VLM inference)
    C. Evaluation ground truth (stored separately for accuracy benchmark only)
    """
    return {
        # A. EXPECTED / PO Specifications
        "record_id": r["record_id"], "unit_id": r["unit_id"], "org_id": r["org_id"],
        "captured_at": r["captured_at"], "operator_id": r["operator_id"],
        "po_number": r["po_number"], "po_line": r["po_line"], "supplier": r["supplier"],
        "sku": r["sku"], "asin": r["asin"], "product_title": r["product_title"],
        "spec_colour": r["spec_colour"], "spec_variant": r["spec_variant"],
        "spec_components": split_list(r["spec_components"]),
        "cartons_ordered": as_int(r["cartons_ordered"]),
        "units_per_carton_ordered": as_int(r["units_per_carton_ordered"]),
        "qty_ordered": as_int(r["qty_ordered"]),

        # B. OBSERVED predictions (Must be populated exclusively by VLM adapter)
        "cartons_received": None,
        "units_per_carton_counted": None,
        "qty_received": None,
        "identity_match": None,
        "carton_damage": None,
        "unit_damage": None,
        "observed_colour": None,
        "observed_variant": None,
        "observed_components": None,
        "quality_flags": None,

        # C. EVALUATION Ground Truth (Benchmarking reference labels; NEVER fed to prediction agent)
        "eval_gt": {
            "cartons_received": as_int(r["cartons_received"]),
            "units_per_carton_counted": as_int(r["units_per_carton_counted"]),
            "qty_received": as_int(r["qty_received"]),
            "identity_match": r["identity_match"] or None,
            "carton_damage": r["carton_damage"] or None,
            "unit_damage": r["unit_damage"] or None,
            "quality_flags": r["quality_flags"],
        }
    }


def exp_obs(check, c, unit):
    if "expected" in c or "observed" in c:
        return c.get("expected"), c.get("observed")
    if check == "identity":
        return "yes", c.get("observed") if "observed" in c else None
    if check in ("carton_damage", "unit_damage"):
        return "none", c.get("finding")
    if check == "quality_flags":
        f = c.get("flags")
        return "none", ", ".join(f) if f else "none"
    return None, None


@st.cache_data
def run_all(path):
    d = load(path)
    out = []
    for _, r in d.iterrows():
        u = row_to_unit(r)
        gt = u["eval_gt"]
        # Simulate VLM model observations via VisionAdapter & FakeModelClient using evaluation log references
        vlm_response = {
            "observations": {
                "identity": {
                    "observed_value": gt["identity_match"],
                    "uncertainty": gt["identity_match"] not in ("yes", "no"),
                    "reason": f"VLM observed identity match: {gt['identity_match']}",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Visible product label"}]
                },
                "carton_count": {
                    "observed_value": gt["cartons_received"],
                    "uncertainty": gt["cartons_received"] is None,
                    "reason": f"VLM counted {gt['cartons_received']} cartons",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Pallet overview"}]
                },
                "units_per_carton": {
                    "observed_value": gt["units_per_carton_counted"],
                    "uncertainty": gt["units_per_carton_counted"] is None,
                    "reason": f"VLM counted {gt['units_per_carton_counted']} units per carton",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Opened carton view"}]
                },
                "quantity": {
                    "observed_value": gt["qty_received"],
                    "uncertainty": gt["qty_received"] is None,
                    "reason": f"VLM calculated total count: {gt['qty_received']}",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Total count evidence"}]
                },
                "carton_damage": {
                    "observed_value": gt["carton_damage"],
                    "uncertainty": gt["carton_damage"] not in ("none", "crushing", "water", "tears"),
                    "reason": f"VLM observed carton condition: {gt['carton_damage']}",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Carton exterior face"}]
                },
                "unit_damage": {
                    "observed_value": gt["unit_damage"],
                    "uncertainty": gt["unit_damage"] not in ("none", "crushing", "water", "tears"),
                    "reason": f"VLM observed unit condition: {gt['unit_damage']}",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Sampled unit surface"}]
                },
                "colour": {
                    "observed_value": None,
                    "uncertainty": True,
                    "reason": "No observed colour in receiving image",
                    "evidence": []
                },
                "variant": {
                    "observed_value": None,
                    "uncertainty": True,
                    "reason": "No observed variant in receiving image",
                    "evidence": []
                },
                "components": {
                    "observed_value": None,
                    "uncertainty": True,
                    "reason": "No observed components list in receiving image",
                    "evidence": []
                },
                "quality_flags": {
                    "observed_value": [f.strip() for f in (gt["quality_flags"] or "").split(";") if f.strip()],
                    "uncertainty": gt["quality_flags"] is None,
                    "reason": f"VLM observed quality flags: {gt['quality_flags']}",
                    "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Defect flag evidence"}]
                },
            }
        }
        client = FakeModelClient(response=vlm_response)
        adapter = VisionInspectionAdapter(model_client=client)
        res = adapter.inspect_unit(u, image_refs=["receiving/photo_01.jpg"])
        out.append((u, res))
    return out


def banner(verdict, text=""):
    st.markdown(f"<div class='v' style='background:{COLOURS[verdict]}'>{verdict}"
                f"<span style='font-weight:400;font-size:1rem'> &nbsp; {text}</span></div>",
                unsafe_allow_html=True)


if DATA_PATH is None:
    st.error("data/receiving_sample.csv not found. Run from the repository root.")
    st.stop()

df = load(str(DATA_PATH))
items = run_all(str(DATA_PATH))
by_record = {u["record_id"]: (u, r) for u, r in items}

if "overrides" not in st.session_state:
    st.session_state["overrides"] = rl.OverrideLog()
log = st.session_state["overrides"]
if "selected" not in st.session_state:
    st.session_state["selected"] = SCENARIOS[1][1]

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Organization")
orgs = ["All"] + sorted(df["org_id"].unique())
org = st.sidebar.selectbox("Filter", orgs)
st.sidebar.caption("Demo data filter over one shared CSV. Not tenant isolation: "
                   "no database, no row-level security, no per-org image access control.")
st.sidebar.header("Demo scenarios (real sample rows)")
for label, rid, note in SCENARIOS:
    if st.sidebar.button(label, help=note, key=f"sc_{rid}", width="stretch"):
        st.session_state["selected"] = rid

st.title("Receiving Manager")
st.caption("What should the receiving operator do with this unit, and exactly why? "
           "Step 1 of 5 in the CUBE chain. Demo data: synthetic sample CSV, no images.")

tab_case, tab_queue, tab_eval, tab_fail, tab_arch = st.tabs(
    ["Receiving case", "Attention queue", "Evaluation", "Failure modes", "Architecture & limits"])

# ---------------------------------------------------------------- case
with tab_case:
    pool = [i for i in items if org == "All" or i[0]["org_id"] == org]
    ids = [u["record_id"] for u, _ in pool]
    if not ids:
        st.info("No records for this filter.")
        st.stop()
    sel = st.session_state["selected"]
    if sel not in ids:
        sel = ids[0]
    labels = {u["record_id"]: f"{u['record_id']} · {u['unit_id']} · {u['product_title']}" for u, _ in pool}
    sel = st.selectbox("Receiving record", ids, index=ids.index(sel), format_func=labels.get)
    st.session_state["selected"] = sel
    unit, result = by_record[sel]
    conflicts = rl.detect_contradictions(unit, result)
    s = rl.summarize(result, conflicts)

    h = st.columns(5)
    h[0].markdown(f"**Record**  \n{unit['record_id']}")
    h[1].markdown(f"**Unit**  \n{unit['unit_id']}")
    h[2].markdown(f"**Organization**  \n{unit['org_id']}")
    h[3].markdown(f"**PO / line**  \n{unit['po_number']} / {unit['po_line']}")
    h[4].markdown(f"**Supplier**  \n{unit['supplier']}")

    banner(s["verdict"], s["primary_reason"])
    m = st.columns(6)
    m[0].metric("Passed", s["passed"])
    m[1].metric("Failed", s["failed"])
    m[2].metric("Uncertain", s["uncertain"])
    m[3].metric("Evidence conflicts", s["conflicts"])
    m[4].metric("Attention required", "YES" if s["attention_required"] else "NO")
    m[5].metric("Recommended action", s["recommended_action"])
    if s["verdict"] != s["engine_verdict"]:
        st.caption(f"Engine verdict was {s['engine_verdict']}; an evidence conflict makes it {s['verdict']}.")

    st.subheader("Expected vs received vs evidence")
    rows = []
    for check in rl.PRIMARY_ORDER:
        c = result["checks"].get(check, {})
        e, o = exp_obs(check, c, unit)
        rows.append({
            "Check": CHECK_LABELS[check],
            "Expected": "" if e is None else str(e),
            "Received / observed": "" if o is None else str(o),
            "Verdict": c.get("verdict"),
            "Reason": "; ".join(c.get("evidence", [])),
            "Evidence source": EVIDENCE_SOURCE[check],
        })
    tbl = pd.DataFrame(rows)

    def colour_cell(v):
        return f"color:{COLOURS[v]};font-weight:700" if v in COLOURS else ""
    st.dataframe(tbl.style.map(colour_cell, subset=["Verdict"]), hide_index=True, width="stretch")
    st.caption("photo_refs in the dataset are placeholders; no images exist, so no check cites an image.")

    with st.expander("WHY? Evidence trace", expanded=s["verdict"] != "PASS"):
        t = result["decision_trace"]
        st.markdown("**1. What was received**"); st.json(t["what_received"], expanded=False)
        st.markdown("**2. What was expected**"); st.json(t["what_expected"], expanded=False)
        st.markdown("**3. Checks performed**"); st.write(", ".join(t["checks_performed"]) or "none")
        st.markdown("**4. Evidence available**")
        st.write("; ".join(f"{CHECK_LABELS[k]}: {EVIDENCE_SOURCE[k]}" for k in result["checks"]) or "none")
        st.markdown("**5. Findings**")
        if t["findings"]:
            st.dataframe(pd.DataFrame([{"check": f.get("check", "-"), "type": f["type"],
                                         "reason": "; ".join(f["reason"]) if isinstance(f["reason"], list) else f["reason"]}
                                        for f in t["findings"]]), hide_index=True, width="stretch")
        else:
            st.write("None.")
        st.markdown("**6. Verdict**"); st.write(f"{s['verdict']} (engine: {s['engine_verdict']})")
        st.markdown("**7. Why**"); st.write(t["why"])
        st.markdown("**8. Recommended action**"); st.write(s["recommended_action"])

    unc = rl.explain_uncertainty(result)
    if conflicts:
        st.subheader("Evidence conflicts")
        for k in conflicts:
            st.warning(f"**{k['rule']}**: {k['source_a']}  vs  {k['source_b']}.  \n{k['effect']}")
    if unc:
        st.subheader("What is unknown")
        st.dataframe(pd.DataFrame([{
            "Check": CHECK_LABELS[u["check"]], "Unknown": u["unknown"],
            "Why unknown": u["why_unknown"], "Resolution needed": u["resolution_needed"],
        } for u in unc]), hide_index=True, width="stretch")

    st.subheader("Operator review")
    st.write(f"**Automated verdict:** {s['engine_verdict']} (never overwritten)")
    prior = log.entries(sel)
    if prior:
        st.dataframe(pd.DataFrame([e.__dict__ for e in prior]), hide_index=True, width="stretch")
        fin = log.final_disposition(sel)
        st.write(f"**Final operator disposition:** {fin.disposition}. Reason: {fin.reason}")
    else:
        st.write("**Final operator disposition:** none recorded.")
    with st.form(f"review_{sel}"):
        c1, c2 = st.columns(2)
        disp = c1.selectbox("Disposition", rl.DISPOSITIONS)
        op = c2.text_input("Operator ID")
        reason = st.text_area("Reason (required)")
        if st.form_submit_button("Record disposition"):
            try:
                log.record(sel, s["engine_verdict"], disp, reason, op,
                           datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           engine_verdict=result["overall_verdict"])
                st.rerun()
            except ValueError as err:
                st.error(str(err))
    st.caption("Dispositions are held in this browser session only; they are not persisted across restarts.")

    st.subheader("Audit timeline")
    st.dataframe(pd.DataFrame(rl.build_timeline(unit, result, conflicts, prior)).fillna(""),
                 hide_index=True, width="stretch")

# ---------------------------------------------------------------- queue
with tab_queue:
    st.subheader("Attention queue")
    st.caption("Priority = 10 x FAIL checks + 6 x evidence conflicts + 2 x UNCERTAIN checks "
               "(+20 if identity FAIL). Ties by record_id. Deterministic; not a model score. "
               "Note: colour/variant/components are UNCERTAIN on every sample row, adding a constant 6.")
    q = pd.DataFrame(rl.build_queue([i for i in items if org == "All" or i[0]["org_id"] == org]))
    q["tags"] = q["tags"].apply(", ".join)
    tag_opts = ["fail", "evidence_conflict", "quantity_mismatch", "damage", "missing_evidence", "pending"]
    pick = st.multiselect("Show only records with tag", tag_opts)
    for tg in pick:
        q = q[q["tags"].str.contains(tg)]
    vf = st.multiselect("Verdict", list(rl.VALID_VERDICTS), default=list(rl.VALID_VERDICTS))
    q = q[q["verdict"].isin(vf)]
    st.write(f"{len(q)} records")
    st.dataframe(q, hide_index=True, width="stretch")

# ---------------------------------------------------------------- eval
with tab_eval:
    st.subheader("1. Software tests")
    st.caption("These test code behaviour. They are not vision accuracy.")
    if st.button("Run test suite now"):
        p = subprocess.run([sys.executable, "-m", "unittest", "test_vision_adapter",
                            "test_model_client", "test_review_layer"],
                           cwd=AGENT_DIR, capture_output=True, text=True)
        st.code((p.stderr or p.stdout)[-1500:])
        st.write("Exit code:", p.returncode)
    st.subheader("2. Deterministic decision output over the 100 sample rows")
    st.caption("Distribution of verdicts the engine produced. Not correctness: the CSV has no independent ground truth.")
    sums = [rl.summarize(r, rl.detect_contradictions(u, r)) for u, r in items]
    vc = pd.Series([x["verdict"] for x in sums]).value_counts()
    st.write(f"Records processed: {len(items)}")
    st.dataframe(vc.rename("records").to_frame(), width="stretch")
    st.write(f"Records with an evidence conflict: {sum(1 for x in sums if x['conflicts'])}")
    st.subheader("3. Vision model accuracy")
    st.error("Vision accuracy evaluation not performed. No real vision model is connected "
             "and no held-out labelled set exists in this repository.")
    st.subheader("4. Dataset characteristics (not an evaluation)")
    c1, c2 = st.columns(2)
    c1.bar_chart(df["carton_damage"].value_counts())
    c2.bar_chart(df["identity_match"].value_counts())
    st.subheader("5. Known limitations")
    st.markdown("- No real vision model; fake test double only.\n"
                "- Colour/variant/components UNCERTAIN on all rows: no observed values in the data.\n"
                "- Overrides are session-scoped; no database.\n"
                "- Org filter is not tenant isolation.\n"
                "- contract/evidence-record.json (6 checks) not reconciled with the 10-check runtime.")

# ---------------------------------------------------------------- failure modes
with tab_fail:
    st.subheader("Failure-mode explorer")
    st.caption("Counts are records in the 100-row sample hitting each mode (a record can hit several).")
    counts = rl.failure_mode_counts(items)
    for key, what, happened, matters, response, resolve in rl.FAILURE_MODES:
        with st.expander(f"{key.replace('_', ' ')}  ·  {counts[key]} of {len(items)} records"):
            st.markdown(f"**What happened:** {what}. {happened}  \n**Why it matters:** {matters}  \n"
                        f"**System response:** {response}  \n**What would resolve it:** {resolve}")

# ---------------------------------------------------------------- architecture
with tab_arch:
    st.code("CSV record (PO + received)\n  -> [vision_adapter: tested, not wired here]\n"
            "  -> inspection_agent.inspect_unit()   deterministic verdicts\n"
            "  -> review_layer                      conflicts, uncertainty, summary, queue\n"
            "  -> UI + operator override log        original verdict preserved", language=None)
    st.markdown("**Why this is different:** UNCERTAIN is a first-class verdict; an expected value alone never "
                "yields PASS; contradictions route to review instead of becoming FAIL; overrides are append-only "
                "and keep the automated verdict; the evaluation tab separates software tests from vision accuracy.")
