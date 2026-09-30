# Supplied files and dataset review — 30 September 2026

## Relevance to Pack Manager

| Input | Finding | Use |
|---|---|---|
| `pack-174d81cc-378f-4dbc-b736-be275e530d3f.json` | Our own `provisional-0.1` draft, fictional stationery catalogue, no images or observations | Historical software example, not product data or a successful inspection |
| `pack-manager-design-review.md` | Direct Pack workflow feedback | Separate presence/count checks, decoy catalogue entries, uncertainty and pending metrics, explicit capture protocol |
| `evidence-contract (1).md` | Supplied fixed Evidence Contract 1.1 | Target interoperability schema and four endpoints |
| `recovery-data-contract.md` | Primarily Recovery Manager; section 5 defines Pack's required check registry, section 4 requires shipment IDs | Preserve `all_items_present`, `quantities_correct`, `no_extra_items`, `order_matches_manifest`; no need to implement reimbursement claims in Pack |

The attachments are reference material, not authorization to send messages, change shared documents, or publish participant information.

## Organiser Drive

[Supplied collection](https://drive.google.com/drive/folders/1R8sk5n_OCvtidlbkyiL0IT6NBZpjT86Q) is titled **CUBE 2026 — RTN PRODUCT COLLECTION**. This is Returns-oriented data, not an identified Pack order dataset.

Inspected Product 01's details and accessories image on 30 September. The collection assigns `RTN-001`, `UNIT-001`, `ORD-001`; its document explicitly says the order ID is synthetic. SKU and ASIN are unknown. These IDs must not be re-labelled as merchant SKUs or real orders. The document has incomplete/unselected condition fields. Its accessories photograph shows a laptop, packaging and a cable, with contents not all exposed; it cannot prove box completeness. This is a sample review, not a completed audit of every product folder.

Possible use: inspect reference appearance and identify photo-quality/occlusion challenges. Before catalogue import, obtain a verified product-to-SKU mapping, confirm the relevant reference view, and review permission for reuse outside the competition. Public link access is not a commercial redistribution licence. Do not publish participant names, relationship fields, shipping labels or original photos in GitHub or a public demo. No shared source documents were modified and no identities were invented.

Still needed for Pack evaluation: actual order manifests and exposed multi-item scenes with independent human counts; correct packs, shortage, excess, wrong SKU, lookalike variants, unknown items, occlusion, bad lighting and unreadable labels. Returns accessory photographs alone do not supply those labels or scenarios.

## Public research development set

The separately prepared [RPC dataset](https://rpc-dataset.github.io/) by Xiu-Shen Wei, Quan Cui, Lei Yang, Peng Wang, Lingqiao Liu and Jian Yang uses **CC BY-NC-SA 4.0** for academic/noncommercial research; see the [original Kaggle distribution](https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset). Commercial deployment/use is not granted by this licence. Keep this research set separate from customer catalogue data and retain attribution/share-alike obligations for permitted derivatives.

`scripts/prepare_rpc.py` downloaded original annotation files, six reference photographs and five checkout scenes under ignored `.local/datasets/rpc`. Category identifiers are preserved from source annotations, not asserted as merchant SKUs. Expected counts are constructed research manifests copied from source annotations, not real shipping orders. All five scenes are development data; zero held-out scenes and no model evaluation have been completed. The small subset is bounded by the current reference-image limit.

| Scenario | Current research support |
|---|---|
| Multiple visible instances and catalogue identification | RPC annotations can support development comparisons |
| Wrong item, shortage, excess | Can construct explicitly synthetic manifests, not independent real packing examples |
| Products inside shipping boxes, hidden layers, real customer variants | Not established by RPC checkout scenes |
| Performance on this user's products | Not established |
| Production accuracy, uncertainty rate, latency or cost | Not measured |

Freeze manifests with `python -m evaluation.dataset --manifest … --root … --output …`. The validator checks original-file hashes, image validity, duplicate content, IDs and scene/session split leakage. It does not replace human annotation or prove accuracy.

## Contract migration status

Implemented: four required Pack check names alongside existing internal checks; presence separate from exact quantity; unresolved observations cannot assert exact counts; optional shipment ID on order API/CSV; strict 1.1 models and authenticated `/v1/records/{record_id}` reader for eligible captures. Hash uses image hashes in array order, followed by compact UTF-8 JSON of checks with sorted object keys and no NaN. This serialization choice needs cross-pod agreement because the supplied contract does not specify it.

Legacy local organization strings export as deterministic UUIDv5 identifiers; real UUID organizations remain unchanged. This compatibility mapping does not change database tenant authorization. `client_id` remains null because no separate client identity is established. Exact observed totals remain null unless counts are known. Pending records do not invent checks or model results. Old draft captures and outcome-only reviews cannot be truthfully translated and return a conflict on the contract reader; the legacy workspace export remains available.

**Not yet fully contract compliant:** paginated Recovery feed, capture allocation/completion endpoints, guided rear-camera 2–3 shots, direct signed browser-to-storage upload, per-check reasoned overrides, scoped public record sharing, and full lifecycle/immutability migration. The older workspace export remains explicitly provisional. Do not label the entire app as 1.1 compliant based on the reader alone.

Repository rule, verbatim: “Make **one** call per unit carrying all checks, never one call per check. At prep volumes that is the difference between a 90% gross margin and none.” The nearby section is “Batch your model calls”; it does not define unit more precisely. The user's conservative restriction remains: at most one inference attempt per evaluation unit across captures, no model retries or extra explanation calls.
