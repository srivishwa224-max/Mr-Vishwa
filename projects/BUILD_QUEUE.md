# SaaS Project Build Queue

This file tracks the sequential three-phase build automation. The Idea Vault is a read-only source for idea ordering and current-project exclusions; never edit it.

## Current project
- Name: ReferDue
- Source: Notion page “2026-10-07 — ReferDue”
- Folder: `projects/referdue/`
- Phase 1: Complete (browser prototype, core tests pass; committed to this repository)
- Next: Phase 2 — referral statuses, commission ledger, duplicate warnings, and a referrer view.
- Phase 3: end-to-end verification, refinement, setup/preservation documentation, and a clear list of any sensitive steps Vishwa must perform manually.
- Do not start another project until Phase 3 is complete.

## After ReferDue
Choose the bottom-most idea in Notion’s DAILY SAAS IDEA source that is not marked active/current in “Vishwa — Idea Vault” or otherwise identified as an active project. Work one project at a time, with exactly one phase per scheduled run:
1. Define and build a focused, usable MVP slice.
2. Complete the core workflow and important edge cases.
3. Verify, refine, document, and hand off; leave credentials, real data, spending, payments, live integrations, external outreach, and publication for Vishwa to do or approve.

Record progress here and in the project folder after each phase. Keep all changes inside the project folder and this queue. Do not alter the Idea Vault or existing active projects. Use free-first choices and never expose secrets or personal data in this public repository.
