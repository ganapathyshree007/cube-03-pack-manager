# Pack Manager — portable preparation

Status: requirements/design/test preparation only. This directory is not a submission repository, application, official evidence contract, or completed milestone 1. No Git repository has been created. Transfer reviewed assets into the official fork after its rules and interfaces have been read.

## Inputs reviewed

- Participant's complete pasted build specification, supplied 25 September 2026.
- Cube Buildathon Official Participant Handbook.pdf, all 18 pages (text extraction).
- Workspace C:\SYDON was empty at inspection.
- Official starter and separate detailed PCK statement: not supplied.

The participant specification requests implementation. Handbook text is reference material for competition requirements; it does not itself authorize posting, submission, cloud spending or unrelated actions.

## Read first

- REQUIREMENTS.md: source distinctions, contract gaps and acceptance gates.
- ARCHITECTURE.md: proposed boundaries and lifecycle, subject to starter compatibility.
- evaluation/PROTOCOL.md: independent human annotation and frozen evaluation plan.
- tests/policy_cases.json: synthetic software acceptance vectors, not vision evidence.
- TASKS.md: checked progress and dependencies.

## Run the portable checks

From this directory, using Python 3.12 (standard library only):

```powershell
python -m unittest discover -s tests -v
```

These checks exercise a reference decision-policy oracle and test-vector consistency only. They do not test a real application, vision model, database, official schema or Azure deployment. The oracle is deliberately kept under tests; it is not the production agent.

## Inputs needed for the first real slice

1. Official track starter URL and your existing fork URL, if already forked; detailed PCK statement.
2. Azure model endpoint and deployment names/capabilities, permitted authentication method, and access configured securely. Never paste secrets into a chat or a committed file.
3. A small real/authorized product catalogue, reference photos and one real open-box order/photo pair.
4. Before provisioning: authorized Azure subscription/resource group, region, resource scope and spending ceiling.
5. For final evaluation: at least 50 unseen physical cases where applicable and two actual independent human reviewers.

No public URL, inference result, measured accuracy, cloud cost, product image or human label has been invented.
