# AgentPrep — Preparation Rules & Decision Semantics Registry

> **Visual Prep Compliance Agent for Inbound Fulfillment**  
> Comprehensive specification of product-specific rules, evaluation logic, evidence requirements, and 3-State decision semantics.

---

## 1. Core Decision Philosophy: "Never Invent Evidence"

AgentPrep enforces strict, deterministic compliance evaluation across all inbound e-commerce goods. The foundational rule across the entire agent pipeline is:

$$\text{Decision} \in \{\text{PASS}, \text{FAIL}, \text{UNCERTAIN}\}$$

- **PASS**: Granted **only** when direct, unambiguous visual evidence proves full compliance with the requirement.
- **FAIL**: Granted **only** when visual evidence directly proves a violation of the requirement (e.g., FNSKU label overlaps a curved edge or an exposed barcode is visible).
- **UNCERTAIN**: Granted whenever evidence is **insufficient**, **blurry**, **obscured by glare**, **missing required camera views**, or when the requirement is **physically non-verifiable** from 2D photographs.

> **Operational Safeguard**: The system **never** converts uncertainty into failure, and **never** converts uncertainty into success. Falsely guessing PASS risks severe Amazon inbound defect penalties ($25.00/unit), while falsely guessing FAIL stalls warehouse operations.

---

## 2. Visually Verifiable vs. Out-of-Scope Requirements

| Category | Requirement | Visually Verifiable? | Evaluation Method | Agent Behavior if Missing / Inconclusive |
| :--- | :--- | :---: | :--- | :--- |
| **Packaging** | Polybag Enclosure | **YES** | Object detection & boundary analysis | `UNCERTAIN` if image blurred / obscured |
| **Packaging** | Polybag Heat Sealing | **YES** | Seal edge integrity analysis | `FAIL` if open seam; `UNCERTAIN` if view missing |
| **Packaging** | Film Thickness (1.5 / 3.0 mil) | **NO** | Out of visual scope | **Always `UNCERTAIN`** (Requires micrometer) |
| **Packaging** | Drop-Test Durability | **NO** | Out of visual scope | **Always `UNCERTAIN`** (Requires drop rig) |
| **Packaging** | Adhesive Peel Strength | **NO** | Out of visual scope | **Always `UNCERTAIN`** (Requires tensile test) |
| **Warning** | Suffocation Warning Print | **YES** | OCR text & legibility detection | `FAIL` if missing; `UNCERTAIN` if folded/blurred |
| **Warning** | Handling Marks (This Way Up) | **YES** | Symbol / OCR pattern detection | `FAIL` if missing; `UNCERTAIN` if obscured |
| **Labeling** | FNSKU Placement (Flat Surface) | **YES** | Barcode geometry & contour check | `FAIL` if overlapping curved edge/seam |
| **Labeling** | Original Barcode Covered | **YES** | UPC/EAN detection on rear view | `FAIL` if exposed; `UNCERTAIN` if rear view missing |
| **Perishable** | Expiration Date Legibility | **YES** | OCR date parsing (EXP MM/YYYY) | `FAIL` if missing/expired; `UNCERTAIN` if unreadable |

---

## 3. Product-Specific Rule Specifications

### Product A: Demo Bottle (`DEMO-BOTTLE-001`)
- **Product Name**: Liquid Container (500ml Shampoo / Essential Oils)
- **ASIN**: `B08N5WRWNW`
- **SKU**: `LQD-BTL-001`
- **Category**: Liquid / Bottle
- **Required Camera Views**: `front`, `back`

#### Applicable Rules:
1. **Polybag Presence** (`bottle_polybag_presence`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: Clear protective polybag must fully enclose bottle to contain potential liquid leaks.
   - *PASS*: Polybag boundary encompasses product contour.
   - *FAIL*: No polybag detected around liquid container.
2. **Polybag Sealing** (`bottle_polybag_sealing`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: Continuous heat-seal or tape closure across polybag opening.
   - *PASS*: Heat seal detected intact with zero open seams.
   - *FAIL*: Open slit or unsealed flap detected.
3. **Suffocation Warning** (`bottle_suffocation_warning`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: Required print *"WARNING: TO AVOID DANGER OF SUFFOCATION..."* present and legible.
   - *PASS*: Warning text detected and OCR confidence $\ge 0.85$.
   - *FAIL*: Polybag opening $\ge 5$ inches without warning text.
4. **FNSKU Placement** (`bottle_fnsku_placement`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: FNSKU barcode must be positioned completely on a flat package surface.
   - *PASS*: Bounding box does not intersect curved container edges or heat seams.
   - *FAIL*: Bounding box overlaps bottle curvature or edge seam.
   - *Recommended Action*: Reposition FNSKU label entirely onto flat front surface.
5. **Original Barcode Covered** (`bottle_manufacturer_barcode`)
   - *Verifiable*: Yes (Camera: `back`)
   - *Evaluation*: Original manufacturer UPC/EAN barcode must be fully covered.
   - *PASS*: Original barcode completely obscured or covered by opaque label.
   - *FAIL*: Original UPC barcode visible and scan-capable.
   - *UNCERTAIN*: Rear camera view not provided (`REQUEST_ADDITIONAL_PHOTO`).
6. **Plastic Thickness (3 mil min)** (`bottle_plastic_thickness`)
   - *Verifiable*: No (Physical property)
   - *Status*: `UNCERTAIN` (Does not block visual approval).

---

### Product B: Boxed Electronics (`DEMO-ELEC-002`)
- **Product Name**: Boxed Electronics Hub (Smart Gateway)
- **ASIN**: `B09K8Y7Z1X`
- **SKU**: `ELE-HUB-002`
- **Category**: Boxed Electronics
- **Required Camera Views**: `front`, `back`

#### Applicable Rules:
1. **FNSKU Placement** (`elec_fnsku_placement`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: FNSKU label placed flat on smooth box face without crossing box folds/edges.
2. **Original Barcode Covered** (`elec_manufacturer_barcode`)
   - *Verifiable*: Yes (Camera: `back`)
   - *Evaluation*: Manufacturer serial / UPC barcode completely covered.
3. **Handling Marks Visible** (`elec_handling_mark`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: Orientation arrows (`THIS WAY UP`) or `FRAGILE` symbol clearly printed.
4. **Drop-Test Certification** (`elec_drop_test_certification`)
   - *Verifiable*: No (Out of visual scope $\rightarrow$ `UNCERTAIN`).
- *Does NOT Require*: Polybagging or Suffocation Warning.

---

### Product C: Plush Toy (`DEMO-TOY-003`)
- **Product Name**: Plush Bear Toy (Soft Plushie)
- **ASIN**: `B07V2X9C8L`
- **SKU**: `TOY-PLSH-003`
- **Category**: Plush & Soft Goods
- **Required Camera Views**: `front`

#### Applicable Rules:
1. **Polybag Presence** (`toy_polybag_presence`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: Plush toy must be sealed in a clean, transparent polybag to prevent dust/soil contamination.
2. **Suffocation Warning Legibility** (`toy_suffocation_warning`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: Legible suffocation warning statement on polybag exterior.
3. **FNSKU Placement** (`toy_fnsku_placement`)
   - *Verifiable*: Yes (Camera: `front`)
   - *Evaluation*: FNSKU label affixed to exterior of polybag.
- *Does NOT Require*: Expiry date or fragile handling marks.

---

## 4. Evidence Sufficiency & Action Synthesis

When an inspection completes, the **Decision Agent** aggregates all check evaluations:

```
IF any verifiable rule is FAIL:
    OVERALL = FAIL
    Action = CORRECT_AND_RESCAN
    Rescan Required = True

ELSE IF any verifiable rule is UNCERTAIN:
    OVERALL = UNCERTAIN
    Action = REQUEST_ADDITIONAL_PHOTO (or HUMAN_REVIEW)
    Rescan Required = True

ELSE (all verifiable rules PASS):
    OVERALL = PASS
    Action = PASS
    Rescan Required = False
```

### Action Types:
- `PASS`: Unit meets all compliance standards. Proceed to packing/shipment.
- `CORRECT_AND_RESCAN`: Defect identified. Operator is provided clear instructions on how to correct the unit (e.g. peel and reposition FNSKU, cover exposed UPC).
- `REQUEST_ADDITIONAL_PHOTO`: Missing camera angle or blurred image. Operator captures supplementary photo (e.g. rear surface).
- `HUMAN_REVIEW`: Ambiguous edge cases requiring warehouse lead sign-off.
