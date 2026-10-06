# PR / FAQ: Returns Manager

## Press Release

**Introducing Returns Manager: Structured, Evidence-Backed Return Inspections**

Processing returns is a critical, time-sensitive operation. Returns Manager introduces a fast, reliable, and visually-assisted workflow to accurately verify returned products. By evaluating incoming return evidence against authoritative catalog data and expected parts lists, Returns Manager deterministically verifies product identity, completeness, and condition. Designed for real-world operations, Returns Manager ensures that when evidence is ambiguous, the system defaults to human review, preventing costly misgradings while preserving full traceability of every decision.

---

## FAQ

**What happens when the image is unclear?**
The agent will return an `UNCERTAIN` verdict for any check it cannot reliably verify and the case will be routed to human review with the status `pending_review`.

**What happens when the model is wrong?**
Operators have the ability to override any decision. The system captures the original verdict, the revised verdict, and the operator's reason, preserving the complete audit trail.

**What happens when the product cannot be identified?**
If the product does not match the catalog reference or is entirely unidentifiable, the identity check will FAIL or become UNCERTAIN, which typically results in the item being routed for liquidation, disposal, or manual review, depending on the disposition rules.

**How does the system prevent hallucinated evidence?**
The model only outputs observations directly visible in the provided image evidence. If it cannot see an expected part or reference, it explicitly flags it as missing or UNCERTAIN.

**How does human review work?**
Operators use the Returns Dashboard to view cases marked as `pending_review`. They can examine the product data, expected parts, reference images, and uploaded evidence, and then manually input the correct verdict.

**Can operators override decisions?**
Yes. Operators can override any automated decision directly from the inspection page.

**Is the original AI decision preserved?**
Yes. When an override occurs, the original AI decision remains completely preserved in the evidence trace for auditing purposes.

**How are organizations isolated?**
Tenant isolation is enforced strictly on the server-side. Data, images, and records belonging to one organization cannot be queried, accessed, or inferred by another organization under any circumstance.

**What happens when the AI API fails?**
The system is designed to fail-open. If the AI service times out or fails, the return is still successfully captured but immediately placed into the `pending_review` state so no physical item is discarded or stalled.

**How does the system handle missing images?**
If no valid images are provided, the system cannot perform a visual inspection and will assign an `UNCERTAIN` verdict to the checks, routing the return to manual review.

**How are condition rules determined?**
The system uses the authoritative Amazon condition scale (New, Renewed, Used - Like New, Used - Very Good, Used - Good, Used - Acceptable, Unacceptable) and does not invent internal taxonomies.

**How is evaluation performed?**
Evaluation is performed using an unseen dataset separated from the development fixtures. Independent human labelers adjudicate cases, and the agent's performance is measured on accuracy, false positives, false negatives, and uncertainty rates.

**How does this work with unseen return images?**
The system performs live visual analysis on newly uploaded images, comparing them against catalog data. It does not rely on matching images to existing rows in a static database.

**Does the system simply match an uploaded image against the seed CSV?**
No. Uploaded images undergo fresh analysis against the structured reference data for that specific order and catalog item. 

**What happens when catalogue/reference images are unavailable?**
If reference images are required but unavailable, the identity check may output `UNCERTAIN` and gracefully defer to human review, accompanied by an explanation that visual reference context is missing.

**What data is authoritative and what data is synthetic?**
The provided sample CSV data is synthetic and used solely for development and fixtures. The published condition scale is authoritative. 

**What would prevent this system from being deployed?**
If the system consistently fails to identify incorrect or incomplete returns (high false negatives), or repeatedly rejects valid returns (high false positives), the autonomous disposition engine would not be enabled in production until the model reliability improved.
