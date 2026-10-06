# Source provenance

Visual extension after c1cafac: target-owned code adds optional Region/variant/attribute/score fields to both the backend and imported Pack schema, postprocessing in backend/pod/visual_observations.py, private raw-output persistence, an evidence-view UI and offline instance metrics. Imported Pack source is therefore adapted, not a byte-identical snapshot. No teammate visual/provider code, weights or restricted photos were imported for this extension. Provider configuration remains disabled.

Local integration branch: `integration/pod7-operations`. No team fork URL is verified and no external push has been made. The upstream push URL is disabled locally.

| Component | Source | Source commit | Current use |
|---|---|---|---|
| Official starter, schemas, flows and five agent entry points | https://github.com/Cube-Build-A-Thon/cube-round3-pod | ab72b2413354862b75ad7556fd45440d099cb320 | Organiser stubs retained, with Windows path and connection-timeout fixes |
| Pack backend and local integrated operations platform | https://github.com/ganapathyshree007/cube-03-pack-manager | a8feb5c | Imported `backend/`, `frontend/`, locked dependencies and tests; local platform with PostgreSQL official-contract adapter |
| Pack vision/reconciliation core | Same Pack source | a8feb5c | `agents/pack/source/`; imported, not yet connected to `agents.pack.app.handle` |

The original Round 2 Pack commit `1e503a0` remains in the original repository. No backdating or replacement of the original submission is intended.

The following older teammate checkouts were inspected read-only in the earlier review. Their commit identities do not identify the later extracted archives audited below:

| Agent | Repository | Inspected commit | Limitation |
|---|---|---|---|
| Receiving | https://github.com/sharonmedithi0304/cube26-rcv-0286-sharonmedithi0304 | b5c4d1a | Starter/sample content; executable integration unresolved |
| Prep | https://github.com/fasihafatima06/cube26-prp-0310-fasihafatima06 | cf6187d | Scenario/filename-driven behavior is not visual recognition |
| Returns | https://github.com/Jahnavi2057/cube26-rtn-0073-jahnavi2057 | 01db82b | In-memory/mock paths need a real contract and durability adapter |
| Recovery | https://github.com/charan-dss-01/cube26-rcy-0079-charan-dss-01 | 267b142 | Rule/optional-model implementation; supported claim integration unverified |

Private account files were reused only in ignored local storage; no credentials or research images are included in tracked source. Existing licenses and organiser files remain in place. Deployment must not expose restricted RPC images.

## Extracted teammate archive audit — 6 October 2026

Exact folder names and inspected source SHA-256 values are in `docs/TEAM_SOURCE_HASHES.json`; the full comparison is `docs/TEAM_AGENT_COMPARISON.md`. Archive commit identities are unverified. Before/after file-content manifests confirm all four source folders remained unchanged. Tests that write files were run only in target-owned scratch copies.

| Source | Adaptation in this project | Changes and exclusions |
|---|---|---|
| `C:\SYDON\cube26-rcv-0286-sharonmedithi0304-main\submissions\sharonmedithi0304\agent\inspection_agent.py`, Sharon Medithi | `backend/pod/receiving_checks.py` | Reimplemented explicit recorded comparisons in the official check format; strict types, absent quality flags stay unknown, component duplicate counts preserved. No model transport, Streamlit app or provisional envelope copied. |
| `C:\SYDON\cube26-prp-0310-fasihafatima06-main\backend\app\agents\evidence_agent.py`, Fasiha Fatima | `backend/pod/prep_checks.py` | Adapted required-view coverage to authorized, explicitly human-recorded image IDs; tri-state quality flags, no scores or simulated features, no scenario/filename model fallback. |
| Returns archive, Jahnavi | Audit only; existing target human disposition retained | No-key mock, retrying vision transport, caller-selected tenant authentication and unsafe substring disposition logic excluded. |
| Recovery archive, Charan | Audit only | No parser, verdict reasoning or claim service imported; separate Recovery approval gate respected. |

The new adapters do not claim their own observed image findings or teammate model accuracy. Local fixture and fake-transport tests are reported separately from application tests and live performance.
