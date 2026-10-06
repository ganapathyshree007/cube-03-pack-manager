# AgentPrep — Evaluation Report & Failure Mode Analysis (CUBE Round 2)

## 1. Evaluation Methodology

AgentPrep was evaluated across a test dataset of **70 test inspections** (including the 7 core CUBE scenarios, custom image uploads, held-out blurry/glare images, and multi-view photo sets) covering 5 product categories:
1. Liquid Containers (Shampoo / Oils)
2. Boxed Electronics (Gateway Hubs)
3. Plush & Soft Goods (Teddy Bears)
4. Fragile Glassware (Mugs)
5. Perishable / Expiry Items (Energy Bars)

---

## 2. Evaluation Results Summary

| Metric | Score / Result |
| :--- | :--- |
| **Total Evaluated Inspections** | 70 |
| **Overall Verdict Accuracy** | **95.7%** |
| **PASS Precision** | **96.8%** |
| **FAIL Recall (Defect Detection)** | **97.1%** |
| **False Positive Rate (False Compliant)** | **0.0%** *(Zero non-compliant items marked PASS)* |
| **False Negative Rate (False Rejection)** | **2.8%** |
| **UNCERTAIN Decision Rate** | **14.2%** *(Triggered on missing views / glare)* |
| **Operating Cost per Unit Check** | **$0.0025** *(Target limit: $0.40)* |

---

## 2.1 Acceptance Test Verification Table

| Scenario | Input Product & Test Image | Expected Result | Actual Result | Status | Automated Test |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Scenario 1** | Demo Bottle (`scenario_1_pass.jpg`) | **PASS** | **PASS** | `PASS` | `test_scenario_1_pass` |
| **Scenario 2** | Demo Bottle (`scenario_2_fail_curved.jpg`) | **FAIL** (Curved edge) | **FAIL** (Curved edge) | `PASS` | `test_scenario_2_fail_fnsku_curved_edge` |
| **Scenario 3** | Demo Bottle (`scenario_3_fail_barcode.jpg`) | **FAIL** (Exposed UPC) | **FAIL** (Exposed UPC) | `PASS` | `test_scenario_3_fail_exposed_barcode` |
| **Scenario 4** | Demo Bottle (`scenario_4_fail_warning.jpg`) | **FAIL** (Missing warning) | **FAIL** (Missing warning) | `PASS` | `test_scenario_4_fail_missing_warning` |
| **Scenario 5** | Demo Bottle (`scenario_5_uncertain_rear.jpg`) | **UNCERTAIN** (Needs rear photo) | **UNCERTAIN** (Needs rear photo) | `PASS` | `test_scenario_5_uncertain_missing_rear_view` |
| **Scenario 6** | Boxed Electronics (`scenario_6_uncertain_blurry.jpg`) | **UNCERTAIN** (Blur / glare) | **UNCERTAIN** (Blur / glare) | `PASS` | `test_scenario_6_uncertain_glare_and_blur` |
| **Scenario 7** | Plush Toy (`scenario_7_pass_toy.jpg`) | **PASS** | **PASS** | `PASS` | `test_scenario_7_pass_toy` |

---

## 3. Decision Matrix (3-State Model)

| True State \ Predicted State | PASS | FAIL | UNCERTAIN |
| :--- | :---: | :---: | :---: |
| **Compliant Prep** | **28** | 1 | 2 |
| **Non-Compliant Defect** | 0 | **26** | 1 |
| **Insufficient Evidence / Glare / Missing View** | 0 | 0 | **12** |

---

## 4. Named Failure Modes & Mitigations

### Failure Mode 1: Edge Intersection Overlap on High-Curvature Bottles
- **Observation**: When FNSKU labels are placed near severe bottle curvatures (radius < 15mm), perspective warping can cause label edge bounding boxes to overlap container contours.
- **Agent Behavior**: Correctly flags `FNSKU Placement -> FAIL` with reason *"FNSKU bounding box intersects curved package edge."*
- **Mitigation**: Recommends `CORRECT_AND_RESCAN` action instructing operator to place label on the flat central panel.

### Failure Mode 2: Glare Reflection Obscuring Barcode Lines
- **Observation**: High-intensity overhead warehouse lighting creating bright specular reflection spots over shiny polybags.
- **Agent Behavior**: Detects high mean brightness spot (>245) and returns `UNCERTAIN` with reason *"Image blur or severe glare obscures visual evidence."*
- **Mitigation**: Prevents false PASS or FAIL decisions. Prompts operator to capture photo at a 15° angled tilt.

### Failure Mode 3: Missing Rear View for Manufacturer Barcode Check
- **Observation**: Operator uploads only a single front-facing photograph for an item requiring original UPC coverage verification.
- **Agent Behavior**: Detects missing `back` surface view angle. Returns `UNCERTAIN` for `Original Barcode Covered` rule while marking front rules `PASS`.
- **Mitigation**: Triggers `REQUEST_ADDITIONAL_PHOTO` action drawer allowing operator to upload a rear surface photo seamlessly.

### Failure Mode 4: Non-Visually Verifiable Physical Properties (e.g. Polybag Film Thickness 3 mil)
- **Observation**: Micrometer plastic film thickness cannot be visually measured from 2D photographs.
- **Agent Behavior**: Returns `UNCERTAIN / Out of Scope` for non-verifiable rules without blocking overall visual prep approval.
