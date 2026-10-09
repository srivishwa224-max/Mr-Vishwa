# SaaS Project Build Queue

This file tracks the sequential three-phase build automation. The Idea Vault is a read-only source for idea ordering and current-project exclusions; never edit it.

## Current project
- Name: ReferDue
- Source: Notion page “2026-10-07 — ReferDue”
- Folder: `projects/referdue/`
- Phase 1: Complete (browser prototype; core tests passed; committed to this repository).
- Phase 2: Complete on 2026-10-08. Added deal statuses, duplicate warnings, a local commission ledger with partial payments, and a referrer filter preview. Eight core tests pass. Referrer filtering is not access control.
- Phase 3: In progress on 2026-10-09. Fixed missing DOM counter, fixed commission timing, failed-save state handling and malformed-storage preservation; added amount validation and duplicate-confirmation reset. All 13 regression tests and both module syntax checks pass. Browser acceptance could not run: Chromium executable missing. See `projects/referdue/HANDOFF.md` for verification, recovery, product gaps and manual handoff.
- Next: Finish Phase 3 browser acceptance and any resulting fixes. Do not mark the prototype complete until verified. This project remains a local prototype, not a production-ready SaaS.
- Do not start another project until Phase 3 is complete.

## After ReferDue
Choose the bottom-most idea in Notion’s DAILY SAAS IDEA source that is not marked active/current in “Vishwa — Idea Vault” or otherwise identified as an active project. Work one project at a time, with exactly one phase per scheduled run:
1. Define and build a focused, usable MVP slice.
2. Complete the core workflow and important edge cases.
3. Verify, refine, document, and hand off; leave credentials, real data, spending, payments, live integrations, external outreach, and publication for Vishwa to do or approve.

Record progress here and in the project folder after each phase. Keep all changes inside the project folder and this queue. Do not alter the Idea Vault or existing active projects. Use free-first choices and never expose secrets or personal data in this public repository.
