# Build Brief: Returns Manager

## Product
Returns Manager.

## User
Returns/warehouse/operations reviewer.

## Core job
Determine:
1. Is this the item that was sold?
2. Is it complete?
3. What condition is it in?
4. What should happen next?

## Inputs
* order information
* SKU/ASIN
* product/catalogue information
* expected parts
* reference images where available
* return evidence images
* metadata (organization, captured timestamp, etc.)

## Outputs
* structured checks
* confidence
* evidence
* disposition
* uncertainty/review state
* evidence record

## Constraints
* Individual build. Must be completely working by the deadline.
* No data sharing or state leaking between tenants (organizations).
* Must fail-open to a review state rather than crashing or discarding evidence.
* Evidence contract must strictly follow the official schema to be compatible with Recovery Manager.
* Visual analysis must handle genuinely unseen images.
* Model calls should be batched to limit latency and API costs.
* Synthetic data must not be interpreted as absolute policy. 

## Non-goals
* Automated physical sorting (robotics/hardware).
* Processing of returns for more than the assigned product domain.
* Building an entire warehouse management system; this application specifically addresses the *Returns Inspection* phase.
* Implementing a generalized chat interface. The UI must be professional and task-oriented.
