# SaaS Project Build Queue

This file tracks the sequential three-phase build automation. The Idea Vault is a read-only source for idea ordering and current-project exclusions; never edit it.

## Current coordination rule — 2026-10-15
This section supersedes the historical automatic-selection instruction below. CAM controls project activation. Continue only unresolved approved ReferDue work. After evidence-backed completion, hand off for CAM/Vishwa review and STOP; do not independently choose or activate another product. Without an explicitly selected next project, report `AWAITING NEXT PROJECT SELECTION`. The bottom-up idea-selection procedure applies only after new explicit authorization to this worker.

Current verified baseline: bounded Chromium workflow and responsive/accessibility smoke tasks have recorded independent Checker PASS (latest evidence: commit `fe61439f60df2648312ec054ac711d10273015be`, run `38564402199`). These do not establish full accessibility, release readiness, deployment or user validation. Phase 3 remains open.

Next safe task: map the remaining core acceptance criteria to current implementation and test evidence before requesting release approval. Do not treat every unperformed optional audit as approved new scope; separate required gaps from future work. Production-host checks, credentials, live SMTP and deployment remain approval-gated.

Documentation reconciliation only on 2026-10-15: inspected queue, current handoff, completion gate and latest Notion report. No code changes, test execution, new Checker verdict, deployment or project activation.

## Current project
- Name: ReferDue
- Source: Notion page “2026-10-07 — ReferDue”
- Folder: `projects/referdue/`
- Phase 1: Complete (browser prototype; core tests passed; committed to this repository).
- Phase 2: Complete on 2026-10-08. Added deal statuses, duplicate warnings, a local commission ledger with partial payments, and a referrer filter preview. Eight core tests pass. Referrer filtering is not access control.
- Phase 3: In progress on 2026-10-09. Fixed missing DOM counter, fixed commission timing, failed-save state handling and malformed-storage preservation; added amount validation and duplicate-confirmation reset. All 13 regression tests and both module syntax checks pass. Browser acceptance could not run: Chromium executable missing. See `projects/referdue/HANDOFF.md` for verification, recovery, product gaps and manual handoff.
- Scope correction 2026-10-10: Vishwa requires the full core app before moving to another project. Prototype test success alone is insufficient. See `projects/referdue/FULL_APP_COMPLETION.md` for the source-backed requirements and verification gates.
- Next: Complete responsive visual/accessibility review and production-host release verification in `projects/referdue/CURRENT_HANDOFF.md`. Synthetic Chromium end-to-end testing is independently verified. Vishwa authorized autonomous continuation; Phase 3 stays open. Live credentials, spending, real data and deployment remain manual handoff gates.
- Do not start another project until Phase 3 is complete.

## Historical selection procedure — superseded by current coordination rule
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

### Account security and preservation — 2026-10-11
Committed email ownership verification, expiring single-use recovery tokens, reset session revocation, persistent request throttles, an HTTPS-only WSGI boundary, corresponding UI and tests, and legacy backend detail completion preserving ledger/identity. All 39 Python tests passed; workspace and browser-test JavaScript syntax passed. No live services or deployment. Phase 3 remains open: browser acceptance and release verification remain unproven; see CURRENT_HANDOFF.md. No next project selected.


### Backup and recovery verification — 2026-10-12
Added a private SQLite backup, integrity-check and restore utility with atomic creation and no-overwrite safeguards. All 42 Python tests passed; both JavaScript syntax checks passed. Playwright is installed but its Chromium executable remains absent, so browser/visual acceptance is still unverified. Phase 3 remains open; next complete browser acceptance in a browser-capable environment and finish release verification. No next project selected.


### Concurrent release verification — 2026-10-12 evening
Added task `referdue/release-concurrency/r1`: 32 synthetic authenticated workspace reads across eight WSGI threads, with exact workspace isolation assertions. Self-test passed; the full Python suite reached 43 tests and both JavaScript syntax checks passed. Submitted for independent Checker review; no Checker verdict was claimed at commit time. This is not a production capacity benchmark. Phase 3 remains open for browser/accessibility and production-host release checks. No next project selected.


### Checker reconciliation — release concurrency r1 — 2026-10-12
Independent Checker issued PASS for commit `bc3e3542030dacf7c257e7795f8e43ee1a606ed3`: targeted concurrency test reproduced, all 43 backend tests passed, and 20 repeated targeted runs covered 640 authenticated reads without failure. Task `referdue/release-concurrency/r1` is READY_FOR_NEXT. Phase 3 remains open for browser/accessibility and production-host release checks; this is not overall release readiness. No next project selected.


### Chromium CI state reconciliation — 2026-10-13
Recognized newer CAM/EO/Checker evidence from task `referdue/chromium-ci/r1`. The free GitHub Actions workflow passed on 2026-10-12: 43 Python tests, 13 Node tests, JavaScript syntax checks and the full synthetic Chromium journey passed. Independent Checker verdict: PASS; implementation commit `5a5b03bc81ead5d46c4fd1cc0db7fd5add2ab52e`, successful run `38274609227`, installed merge commit `a253cd3b830a3ff54d5f8affed5f195c6a93925b`. The former “Chromium unavailable” blocker is historical and closed. Phase 3 remains open for responsive visual/accessibility review, production HTTPS/live-service verification and Vishwa’s release approval. No next project selected.


### Responsive/accessibility smoke verification — 2026-10-14
Task `referdue/responsive-accessibility/r1` is PASS / READY_FOR_NEXT. Commit `1de3c15af5642d4c614d7606547e50236d34b2c1` installed bounded Chromium assertions for desktop and 390×844 mobile horizontal fit, visible-control accessible names, language/viewport metadata, one visible H1, the status live region and visible keyboard focus while preserving the full synthetic journey. GitHub Actions run `38564402199` passed 43 Python tests, 13 Node tests, both JavaScript syntax checks and the real Chromium workflow. Independent Checker reproduced the non-browser suites, inspected the exact diff/logs and issued PASS. This is not a full WCAG audit or production-host verification. Phase 3 remains open for remaining release-readiness review, production HTTPS/live-service checks and Vishwa's release approval. No next project selected.
