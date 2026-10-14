# ReferDue full-app completion gate

Updated 2026-10-10 following Vishwa's explicit correction: complete the full app before moving to another idea. Three phases organize work; they are not a three-day deadline. Earlier prototype-complete labels do not establish full-app completion.

## Current gate
Phase 3 remains open. Vishwa said he would test the prototype and requested full-app completion after those tests pass. No test results are present in this conversation as of this review. Do not invent a pass or advance the queue. Preserve the existing prototype while preparing the remaining implementation.

## Required core app and acceptance evidence
Source: Notion '2026-10-07 — ReferDue', Core MVP Features, reread 2026-10-10.

| Capability | Current evidence | Completion evidence required |
|---|---|---|
| Persistent business workspaces, owner and team roles | Browser-local prototype only | Server persistence, membership enforcement, cross-workspace denial tests |
| Referrer directory with contact/payment-reference fields | Names on referral records only | Directory CRUD and role permissions; synthetic references only |
| Submission with prospect, date, source, service, estimated value, notes | Partial local form | All source fields, server validation and persistence |
| Passwordless introduction acceptance | Missing | Expiring single-use acceptance; replay/expiry/wrong-recipient tests |
| Fixed/percentage agreed terms | Local values and manual checkbox | Versioned agreement captured before progression; changes audited |
| First accepted introduction attribution | Duplicate warning only | Transactional attribution and concurrent competing-acceptance tests |
| Submitted through customer-paid/commission-paid stages | Partial local stages | Explicit state transition rules and revenue-driven behavior tests |
| Revenue entries and commission calculations | Local tests previously passed | Server-side exact monetary arithmetic, idempotency and concurrent-write tests |
| Duplicate warnings | Local matching | Workspace-scoped normalization and no cross-tenant disclosure |
| Private referrer portal | Filter only, no authorization | Authenticated server-enforced per-referrer access; direct-request denial tests |
| Evidence attachments | Missing | Size/type validation and private authorized upload/download tests |
| Pending, approved, due, paid, overdue ledger | Partial due/paid logic | Approval/due-date rules with boundary-date tests |
| Monthly partner statement | Missing | CSV or PDF scoped by partner/month, totals verified and CSV injection prevented |
| Acceptance/status/approval/payment emails | Missing | Notification outbox and fake-delivery tests; live delivery reserved for Vishwa |
| Append-only sensitive activity history | Editable local history | Application-role update/delete denied; attributable, transactional audit events |
| Record external payments without moving money | Local record entry | Maintain this boundary in every backend/UI flow |

## Sequence after prototype results
1. Resolve reported prototype failures; preserve the passing baseline.
2. Implement local-testable persistence and authorization foundation with synthetic users/data.
3. Integrate end-to-end acceptance, attribution, private portal and ledger workflows.
4. Add private evidence, statements, notification outbox and append-only audit.
5. Run feature, negative authorization, concurrency, recovery and browser acceptance checks. Record commands/results rather than estimated completion percentages.
6. Prepare full-app handoff with each requirement linked to implementation and evidence. Keep any unavailable check explicitly open. Only move to the next eligible idea once all agreed non-sensitive implementation and verification work is complete; list live-operation gates separately.

## Scope boundaries
The source's 'Extra Features for Later' are a future backlog, not part of core completion: CRM/accounting integrations, recurring/split commissions, automated payouts, white-label portals and advanced analytics. Do not quietly substitute a prototype for the core app.

No paid infrastructure, live connections, credentials, real customer data, partner contact, publication or money movement. Build testable adapters using synthetic fixtures. Vishwa alone handles live credentials/accounts, spending, real-data authorization, external commitments, payments and deployment. These manual gates must not be used to label unbuilt ordinary features as complete.

## Review evidence for 2026-10-10
Freshly read the GitHub queue and original Notion idea. Compared the required core feature list against the prior recorded handoff. This was scope reconciliation, not a code test run. No application changes or new test passes claimed. Prior 13-test pass belongs to 2026-10-09.


## Recovery evidence for 2026-10-12
Added an integrity-checked SQLite backup/recovery utility and synthetic recovery tests. The tool creates private copies atomically, refuses overwrite, validates backups read-only and rejects corrupt restore sources. This verifies the application-level recovery procedure locally; it does not verify a future host, its permissions, retention, encryption or off-site storage. Those deployment-specific checks remain part of Vishwa's manual release operation.


## Concurrent release evidence for 2026-10-12 evening
Task `referdue/release-concurrency/r1` added a bounded WSGI concurrency smoke test using synthetic data: 32 authenticated workspace reads across eight threads. Self-test passed and the full Python suite reached 43 tests. This submission awaits independent Checker review; it does not establish production capacity or replace browser, accessibility, security or deployment-host testing.


## Independent Checker verdict — referdue/release-concurrency/r1
Checker verdict: **PASS** for revision 1 at commit `bc3e3542030dacf7c257e7795f8e43ee1a606ed3`. The Checker reproduced the targeted test, all 43 backend tests, and 20 repeated targeted runs covering 640 authenticated reads. This closes the bounded WSGI read-concurrency task only. Browser, accessibility, production-capacity, security and deployment-host gates remain open.


## Chromium CI evidence — reconciled 2026-10-13
Task `referdue/chromium-ci/r1` received an actual independent Checker PASS. Successful GitHub Actions run `38274609227` executed 43 Python tests, 13 Node tests, JavaScript syntax checks and the existing synthetic Chromium workflow covering the core local journey through reload. Implementation commit: `5a5b03bc81ead5d46c4fd1cc0db7fd5add2ab52e`; installed merge commit: `a253cd3b830a3ff54d5f8affed5f195c6a93925b`. Browser execution is now verified for the synthetic loopback workflow. Responsive layout/accessibility assertions, production HTTPS hosting, live integrations, deployment and user validation remain open, so this is not overall release readiness.


## Responsive/accessibility smoke evidence — 2026-10-14
Task `referdue/responsive-accessibility/r1` received an independent Checker PASS at merged commit `1de3c15af5642d4c614d7606547e50236d34b2c1`. GitHub Actions run `38564402199` passed 43 Python tests, 13 Node tests, both JavaScript syntax checks and a real Chromium journey with bounded desktop/mobile fit, accessible-name, language, viewport, heading, live-region and keyboard-focus assertions. This closes the approved smoke-check task only. Full WCAG/assistive-technology coverage, multiple browsers/devices, production HTTPS/live services, deployment and user validation remain open; ReferDue is implemented and self-tested with independently verified bounded tasks, but is not deployed or production-ready.
