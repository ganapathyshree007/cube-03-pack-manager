# Findings — not posted externally

RULES.md engineering rule 2, complete text:

> Make **one** call per unit carrying all checks, never one call per check. At prep volumes that is the difference between a 90% gross margin and none.

That section does not define unit. data/README.md defines unit_id:

> The unit this record is about. It's the same ID in all five repos, which is the join key for the chain.

Participant instruction: at most one inference request in total, including vision/controller calls and failures; no automatic retries. Implementation shares a durable budget across organization + unit_id. Retakes preserve evidence for human review without resetting it. Organizer clarification on corrected setups/auxiliary captures remains pending; no exemption is assumed.

RULES.md fail-open behavior saves pending captures and lets operators continue. The participant forbids errors granting AI seal permission. Implementation preserves records and human review, leaves the automated outcome null, and does not control physical equipment.

GITHUB-GUIDE.md permits root-level development in the own fork and says no PR-to-main submission workflow. Legacy submissions/_TEMPLATE, PR template and submission-guard still require author-named branches/subdirectories. Root-level own-fork workflow is followed; legacy files are unchanged. No organizer issue/PR has been sent.

The referenced official evidence contract and domain brief are absent. The eight scenario labels originate in the participant specification; the repository supports the underlying checks but does not enumerate an official eight-label list.
