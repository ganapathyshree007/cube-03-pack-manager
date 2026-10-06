# jahnavi2057 · Returns Manager

## Expected layout

```
submissions/jahnavi2057/
├── README.md
├── 01-customer-letter.md
├── 02-prfaq.md
├── 03-one-pager.md
├── CLAUDE.md
├── build-brief.md
├── build-log.md
├── eval-report.md
├── contract/
│   └── evidence-record.schema.json
└── agent/
```

## Status

| Face | Deliverable | Status |
|---|---|---|
| 1 | Customer letter, PR/FAQ, one-pager | ☑ |
| 2 | CLAUDE.md | ☑ |
| 3 | Headless agent on fixtures | ☑ |
| 4 | Eval report | ☑ |
| 5 | Evidence record page | ☑ |
| 6 | Cross-pod contract | ☑ |

## Kill condition

If evaluation demonstrates that the system cannot reliably distinguish critical identity/completeness failures from valid returns without unacceptable false positives/false negatives, the autonomous decision workflow should not proceed to production and must remain review-assisted.

## Setup and Run Commands

**Install dependencies:**
```bash
cd submissions/jahnavi2057/agent
npm install
cd client
npm install
```

**Run Full Stack (Backend API + Frontend UI):**
```bash
cd submissions/jahnavi2057/agent
npm run dev
```
*(This uses `concurrently` to launch both the Express backend on port 3001 and the Vite React frontend on port 5173).*

**Run Tests:**
```bash
cd submissions/jahnavi2057/agent
npm test
```

## Environment Variables

An `.env` file can be placed in `submissions/jahnavi2057/agent/`. No keys are committed.
```env
GEMINI_API_KEY=your_key_here
PORT=3001
```

## Mock / Demo Mode
If `GEMINI_API_KEY` is not provided, the application will gracefully fall back to a deterministic **Mock/Demo Mode**. It explicitly flags results as `model_version: mock_demo` and makes no claim of real AI analysis. This safely allows UI and workflow testing.

## Tenant Isolation

Demonstrate Tenant Isolation: Use the dropdown to switch between org_demo_alpha and org_demo_bravo. The backend validates the active tenant context and scopes all return/evidence queries to that tenant. Verify that records and evidence from one tenant cannot be accessed from the other tenant. 
*(Note: For demo purposes, authorization is simulated via the `x-tenant-id` header. Production systems would extract this strictly from a verified JWT/session.)*

## Architecture

- **Input**: order information, expected parts, reference images, return evidence images.
- **Agent**: Analyzes the evidence image against the catalog to identify product match, missing components, and overall condition.
- **Decision Engine**: Deterministically routes based on identity, completeness, condition, and uncertainty.
- **Evidence Record**: Stores all evaluation parameters and human overrides securely isolated by tenant.
- **Human Review**: Enables override capabilities without modifying the original model prediction.