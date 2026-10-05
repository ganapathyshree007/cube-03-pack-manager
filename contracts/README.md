# Pod integration contracts — provisional

These JSON Schemas are generated from this repository's typed contracts. They describe this implementation, not a verified Round 3 organiser schema. No teammate source code was copied. Preserve original source IDs and require explicit verified mappings; organization scopes every unit/workflow/run.

- `unit-input`: entry point, explicit fulfillment route and expected lines.
- `manager-output`: current persisted human/deterministic outputs for all five managers.
- `visual-input`: prepared synthetic-only scene/reference boundary for four visual managers; no expected counts allowed.
- `visual-observation`: prepared structured visual observations, distinct from an approved business verdict. Not dispatched or persisted as a working AI result yet.
- `evidence-1.1`: existing official evidence export projection; Round 3 applicability unverified.

Receiving precedes either Prep (FBA) or Pack (merchant/3PL). Returns requires a return event. Recovery requires a charge event, consumes saved evidence and never performs image inference or issues a claim in this implementation. Execution state is separate from business verdict. Manual review retains original results and attribution. See `docs/INTEGRATION_COMPARISON.md` for source conflicts.

The supplied organiser email asks teams to agree on contracts before orchestration. This existing integration was developed before that email was supplied; these contracts now document it for team review. Do not misrepresent that sequence. Obtain teammate agreement and the actual Round 3 repository link before treating this as the Pod submission.
