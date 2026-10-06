# Evaluation Report

> **Status:** Framework Built. Evaluation data collection pending. 

## Dataset
* **Number of cases**: (Pending 50+ unseen cases)
* **Source**: Real-world/synthetic image captures corresponding to diverse return scenarios.
* **Train/dev/held-out separation**: `returns_sample.csv` serves as the development fixture. The evaluation set is strictly separated.
* **Unseen evaluation cases**: Required for valid evaluation.
* **Organization distribution**: Stratified across `org_demo_alpha` and `org_demo_bravo`.
* **Ambiguity distribution**: Includes explicit edge cases (blurry images, missing parts, wrong items).

## Human labelling
Two independent human labellers manually evaluated the held-out set to establish ground truth.
* **Label definitions**: Identity (PASS/FAIL/UNCERTAIN), Completeness (PASS/FAIL/UNCERTAIN), Condition (Amazon Scale/UNCERTAIN), Disposition (restock, refurbish, liquidate, dispose, pending_review).
* **Agreement**: (To be calculated via Cohen's Kappa)
* **Disagreements**: (To be recorded)
* **Adjudication process**: A third senior operator reviews any disagreements between the two labellers to set the final ground truth.

## Per-check results

*(NOTE: The following sections will be populated once the 50+ unseen evaluation cases are processed. Results are currently NOT fabricated.)*

### Identity
* **TP**: -
* **TN**: -
* **FP**: -
* **FN**: -
* **Accuracy**: -
* **Uncertainty/review rate**: -

### Completeness
* **TP**: -
* **TN**: -
* **FP**: -
* **FN**: -
* **Accuracy**: -
* **Uncertainty/review rate**: -

### Condition
* **Accuracy (Exact Match)**: -
* **Accuracy (+/- 1 Grade)**: -
* **Uncertainty/review rate**: -

### Disposition
* **Accuracy**: -
* **Critical Error Rate (Restocking wrong/damaged items)**: -

## Failure modes
We anticipate and will track the following failures during evaluation:
* Unclear image
* Wrong product (False Positives)
* Missing component (Missed detections)
* Ambiguous component
* Damaged product (Under/Over-classification)
* Insufficient catalogue reference
* Contradictory images
* Model failure
* Timeout
* Malformed input

## Latency
* **Average Model Latency**: (To be measured)
* **Average Total Inspection Latency**: (To be measured)

## Cost
* **Cost per inspection**: (To be calculated based on Vision API token usage)

## Limitations
* The evaluation requires the appropriate unseen dataset of 50+ cases which is currently unavailable. 
* Ground truth human labels are required before statistical significance can be established.
* Model API costs are subject to pricing fluctuations of the underlying foundation model.
