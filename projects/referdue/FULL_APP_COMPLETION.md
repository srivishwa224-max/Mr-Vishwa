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
