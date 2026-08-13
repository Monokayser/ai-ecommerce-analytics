# v1.12.2 Release Notes

This release introduces a persistent, accessible chat launcher and reframes the AI workspace as an autonomous analytics agent.

## Improvements

- Added an always-visible lower-right AI launcher on every application section.
- Added direct, query-parameter-driven routing to the agent workspace.
- Added a compact 58×58 mobile launcher and full keyboard/focus support.
- Changed the composer from question-only wording to outcome-oriented task delegation.
- Added an autonomous task receipt covering understanding, planning, validation, analysis, and delivery.
- Automatically selects the recommended visualization and prepares verified report downloads after execution.
- Preserved read-only SQL validation, query limits, safe fallback, explicit filters, and evidence-based responses.

## Verification

- 104 Python tests pass with 87.88% measured coverage.
- The launcher, routing, task composer, complete task execution, exports, mobile placement, accessibility, and reduced-motion behavior are covered by automated tests.
