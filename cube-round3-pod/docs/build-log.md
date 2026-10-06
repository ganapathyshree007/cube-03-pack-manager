# Build log

Keep this current. Organisers read it, and it is evidence of how the Pod actually worked. One entry per working session; newest first. Be honest about what failed.

| Date (UTC) | Who | What we did | What we learned / what broke | Next |
|---|---|---|---|---|
| _YYYY-MM-DD_ | _@handle_ | _e.g. Wired Receiving agent into agents/receiving/app.py; contract test passes_ | _e.g. our model returns confidence as a percentage; converted to 0..1_ | _e.g. Prep adapter_ |


## 2026-10-05 — local integration continuation

- Created `integration/pod7-operations` from official starter ab72b2413354862b75ad7556fd45440d099cb320. Imported Pack a8feb5c source without research images or provider keys. Original repository remains intact.
- User explicitly left assigned Pod type/shared fork unresolved. Added `pod-assignment.json`; did not infer from starter defaults or publish.
- Fixed Windows evidence reference separators, connection-timeout classification and saving active stage before dispatch. Official 93 tests pass; added cross-platform starter command runner.
- Redesigned access screens, order heading/ID details, collapsible activity and server-state route overview. Public auth configuration failure no longer exposes local-token sign-in. No authentication bypass introduced.
- Reused existing local PostgreSQL, private account and evidence paths; website/API/worker run on loopback port 8014. Provider credentials were not copied and model dispatch is disabled.
- Verified 26 reconciliation tests, 27 provider/auth/storage tests, 37 PostgreSQL tests, six browser fixtures and one real local manual-review browser flow. See evaluation report for scope and initial failures.
- Remaining: real Pack official handler/whole-system durable budget, full stage integrations, safe key configuration, held-out labels, verified Pod assignment/fork, authenticated public deployment and hosted inference. No model accuracy or completion claim.


## 6 October 2026 local commerce continuation

Added versioned product policy, customer ordering/returns, conditional scheduling, state tracker and persisted analytics. Added migrations 003/004 and official PostgreSQL contract adapters. Preserved original commits and existing database. Fixed reservation INSERT detection using RETURNING and mobile navigation wrap. Final backend suite: 271 passed with PostgreSQL enabled; browser: 2 real local + 6 fixtures passed; production build and scoped Ruff passed. Migration head 004 verified. No external deployment or live model call. See LOCAL_COMMERCE.md and evaluation.md for boundaries.
