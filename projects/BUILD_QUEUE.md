# SaaS Project Build Queue

This file tracks the sequential three-phase build automation. The Idea Vault is a read-only source for idea ordering and current-project exclusions; never edit it.

## Current project
- Name: ReferDue
- Source: Notion page “2026-10-07 — ReferDue”
- Folder: `projects/referdue/`
- Phase 1: Complete (browser prototype; core tests passed; committed to this repository).
- Phase 2: Complete on 2026-10-08. Added deal statuses, duplicate warnings, a local commission ledger with partial payments, and a referrer filter preview. Eight core tests pass. Referrer filtering is not access control.
- Phase 3: In progress on 2026-10-09. Fixed missing DOM counter, fixed commission timing, failed-save state handling and malformed-storage preservation; added amount validation and duplicate-confirmation reset. All 13 regression tests and both module syntax checks pass. Browser acceptance could not run: Chromium executable missing. See `projects/referdue/HANDOFF.md` for verification, recovery, product gaps and manual handoff.
- Scope correction 2026-10-10: Vishwa requires the full core app before moving to another project. Prototype test success alone is insufficient. See `projects/referdue/FULL_APP_COMPLETION.md` for the source-backed requirements and verification gates.
- Next: Resolve the engineering and browser acceptance gates in `projects/referdue/CURRENT_HANDOFF.md`. Vishwa authorized autonomous continuation; do not wait for repeated approval. Phase 3 stays open. Live credentials, spending, real data and deployment remain manual handoff gates.
- Do not start another project until Phase 3 is complete.

## After ReferDue
Choose the bottom-most idea in Notion’s DAILY SAAS IDEA source that is not marked active/current in “Vishwa — Idea Vault” or otherwise identified as an active project. Work one project at a time, with exactly one phase per scheduled run:
1. Define and build a focused, usable MVP slice.
2. Complete the core workflow and important edge cases.
3. Verify, refine, document, and hand off; leave credentials, real data, spending, payments, live integrations, external outreach, and publication for Vishwa to do or approve.

Record progress here and in the project folder after each phase. Keep all changes inside the project folder and this queue. Do not alter the Idea Vault or existing active projects. Use free-first choices and never expose secrets or personal data in this public repository.

## Authorized continuation — 2026-10-10
Vishwa said to go ahead now. Added backend/store.py, backend/test_store.py and backend/README.md under ReferDue: SQLite persistence, workspace membership checks and append-only activity triggers. Six Python unit tests passed using synthetic fixtures. This is not integrated with login or UI and is not a complete app. Phase 3 remains open; next implement trusted authentication/API boundary and remaining full-app requirements. Do not wait for prototype feedback to continue independent implementation, and do not assume feedback passed.

### Evening continuation — 2026-10-10
Added local account registration/login, salted password hashing, expiring hashed sessions, logout, a loopback HTTP API with Host/Origin checks, and a minimal connected workspace page for workspaces/partners/team/referral introductions. 12 Python tests pass including real HTTP boundary tests; JavaScript syntax check passes. No browser acceptance claimed. Existing commission prototype is separate; full ledger integration, secure referrer portal, acceptance/attribution, evidence, statements, notifications and production auth hardening remain. Continue Phase 3; do not advance to another idea.

### Commission integration — 2026-10-10
Added authenticated persistent commission terms and revenue/payment ledger to the connected workspace. Sixteen Python tests and JavaScript syntax check pass. Browser and concurrency stress checks remain open. Continue Phase 3: full referral fields/stages, acceptance/attribution, referrer-only access, approval/due dates, evidence, statements, notifications and production hardening. No next project selected.

### Core workflow continuation — 2026-10-10
Implemented full referral capture and duplicate warnings, expiring acceptance links with first-accepted claims, read-only partner capability portal, guarded stages, owner approval/due dates, private evidence, monthly CSV statements and a dry-run-first notification worker. All 28 Python tests passed; JavaScript syntax passed. Chromium installation failed due to invalid download, so browser acceptance remains unverified. CURRENT_HANDOFF.md is the current authoritative status; earlier entries are historical. Production email ownership/recovery/throttling, production serving/security checks, legacy-data migration and browser/UI review remain assistant engineering work, not Vishwa-only tasks. No phase completion or next-project selection.
