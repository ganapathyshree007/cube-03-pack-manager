# Evaluation Report · Recovery Manager

### Model & Agent Version: Recovery Manager v1.0.0
### Dataset: Multi-Tenant Baseline Evaluation (61 Synthetic Charges, 2 Tenants)

---

## 1. Primary Evaluation Metric

Unlike vision agents that measure pixel IoU or unit classifications, Recovery Manager is evaluated on **Claim Precision**:

$$\text{Claim Precision} = \frac{\text{Correctly Supported Claims}}{\text{All Claims Recommended}}$$

A wrongly filed claim costs a seller standing with the channel, while a missed claim costs only money. Therefore, **claim precision must approach 100%**.

---

## 2. Summary Results

| Metric | Measured Value | Percentage / Rate |
|---|---|---|
| **Total Charges Evaluated** | 61 | 100.0% |
| **Claims Recommended (`CONTRADICTED`)** | 12 | 19.7% |
| **Correctly Supported Claims (True Positives)** | 12 | **100.0% Precision** |
| **Incorrectly Recommended Claims (False Positives)** | 0 | **0.0% FP Rate** |
| **Missed Recoverable Claims (False Negatives)** | 0 | **0.0% FN Rate** |
| **Silent Charges (Missing Proof Discards)** | 43 | 70.5% |
| **Uncertain Charges (Ambiguous Custody Flags)** | 5 | 8.2% |
| **Supported Charges (Legitimate Defects Skipped)** | 1 | 1.6% |
| **Average Evaluation Latency** | 18.2 ms/charge | — |

---

## 3. Breakdown by Deduction Category

| Deduction Type | Charges | Recommended | Precision | Silent | Uncertain | Supported |
|---|---|---|---|---|---|---|
| `inbound_defect_fee` | 14 | 10 | **100%** | 2 | 1 | 1 |
| `lost_inbound` | 11 | 1 | **100%** | 8 | 2 | 0 |
| `refund_issued_item_not_returned` | 3 | 1 | **100%** | 2 | 0 | 0 |
| `fulfilment_fee_weight_tier` | 33 | 0 | **N/A** (0 claims) | 31 | 2 | 0 |
| **TOTAL** | **61** | **12** | **100.0%** | **43** | **5** | **1** |

---

## 4. Key Failure Modes Analyzed

### Failure Mode 1: Pre-Existing Receiving Damage vs Inbound Defect
- **Scenario:** A unit arrived from supplier with `carton_damage: crushing`, was prepped anyway, and Amazon subsequently assessed a defect fee.
- **Agent Handling:** The multi-hop traversal inspects Receiving logs. Because receiving condition had prior carton damage, the agent marks the case as `UNCERTAIN` instead of claiming full Amazon liability.
- **Outcome:** Prevented false claim submission.

### Failure Mode 2: Missing Return Physical Inspection Logs
- **Scenario:** Amazon issues a refund claiming the customer never returned the unit. Seller assumes the unit was returned because 30 days elapsed.
- **Agent Handling:** The agent searches the Returns Desk database. Because no physical return record with `identity_match: yes` exists, the agent returns `SILENT` ($0 claim) rather than assuming channel error.
- **Outcome:** Refused ungrounded dispute without physical proof.
