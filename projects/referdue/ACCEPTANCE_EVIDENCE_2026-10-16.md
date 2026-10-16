# ReferDue core acceptance evidence audit — 2026-10-16

## Decision and evidence boundary
Phase 3 remains open. This completes the approved documentation audit, not development completion or a new independent Checker verdict. No code changed and no tests were executed in this run.

Starting point: current BUILD_QUEUE.md and CURRENT_HANDOFF.md agreed that this audit was next. Reviewed current server.py, store.py, workflows.py, test_workflows.py, test_store.py, test_ledger.py, test_concurrency.py and test_notifications.py. Compared FULL_APP_COMPLETION.md with the original ReferDue idea's 16 core MVP features and the latest October 15 Notion report. Repository baseline: 502a7b7540969f27eeac654f3318603ae96d8823.

The existing handoff records bounded independent Checker PASS for concurrency and Chromium/accessibility smoke checks. Those historical results stand; they are not a whole-product PASS. No newer separate CAM activation was established. ReferDue remains current.

## Requirement map
Paths below are relative to this project. Test references describe inspected assertions, not fresh execution.

| Core requirement | Current code / evidence | Remaining qualification |
| --- | --- | --- |
| Workspace and owner/team roles | backend/store.py authorization and membership; test_store.py cross-workspace denial and owner-only membership tests | No broad production authorization audit claimed |
| Referrer contact/payment-reference directory | backend/server.py partners route and partner_profiles persistence | Create/list exists; update/delete not implemented. Later checklist says CRUD, original core only says directory: CAM scope decision required |
| Submission fields | Workflows.submit validates/persists prospect, company, contacts, service, date, estimate, source, notes; test_workflows.py submission helpers and legacy preservation | Not every invalid-field boundary has an explicit test |
| Passwordless acceptance | issue/capability/preview/accept; expiry, reissue and replay tests | Bearer possession, not independent recipient identity. Later wrong-recipient gate cannot be claimed satisfied |
| Fixed/percentage terms before progression | Store.set_terms; issue requires terms; test_stage_and_term_guards and ledger tests | Insert-only immutable agreement, not editable/versioned terms. Later versioning gate requires CAM clarification |
| First accepted introduction wins | accept uses BEGIN IMMEDIATE and unique attribution keys; test_acceptance_preview_replay_and_first_claim | Test is sequential. No demonstrated simultaneous competing-acceptance test; payment concurrency is not equivalent |
| Eight referral stages | Workflows.stage and derived summary stages; test_stage_and_term_guards; approval/payment tests | Selected transition coverage, not exhaustive transition matrix |
| Manual revenue and exact commission | Store integer-cents arithmetic and record_payment; test_ledger.py rounding/fixed/percent/retry tests; test_concurrency.py overpayment race | Not a financial/accounting certification |
| Normalized duplicate warning | Workflows.submit company/email/phone normalization; test_duplicate_warning_does_not_insert | Full normalization matrix and independent tenant-isolation duplicate test remain unproven |
| Private partner portal | Workflows.portal capability-scoped query; test_private_portal_only_selected_partner | Bearer access must remain private; not recipient-account identity |
| Evidence attachments | add_evidence/evidence size, signature, extension and access checks; test_evidence_validation_and_access | Exact 1 MB boundary tests and browser download UX not established; no malware scanning |
| Commission status ledger | Workflows.summary/approve/payment; test_approval_due_and_overdue | Day-before/on/after due and paid asserted; production timezone policy still needs review |
| Monthly PDF or CSV | Workflows.statement CSV; test_monthly_statement_opening_and_csv_safety | CSV satisfies original OR requirement. PDF is not mandatory. UTC month semantics must be disclosed |
| Email notifications | Transactional outbox and dry-run-first adapter; test_notifications.py fake failure/retry/success; payment rollback test | Live SMTP/deliverability unverified and reserved for approval; private link delivery remains manual |
| Append-only sensitive history | Store._log and update/delete triggers; test_audit_cannot_be_updated_or_deleted; transactional rollback tests | Acceptance actor is capability label; database administrator can bypass triggers |
| No money movement | Manual ledger recording only in inspected workflow; fake notification transport | No payout provider or real transaction was invoked; maintain this boundary |

## Scope reconciliation, not silent acceptance changes
The original idea requires PDF OR CSV and terms recorded before progression, not negotiated term revisions. The later checklist introduces directory CRUD, versioned changes and wrong-recipient proof. Keep these visible as unresolved scope/acceptance decisions; do not waive the checklist or implement expanded behavior without CAM approval. Pricing, billing limits and pilots appear in the idea's broader plan, not its 16-feature core list; CAM must decide any release requirement. CRM integrations, recurring/split commissions and automated payouts remain future backlog.

## Next safe unit
Add a deterministic two-connection competing-acceptance test using synthetic data. Assert exactly one winner, one claim, no partial attribution keys/stage/outbox changes for the loser, and single-use behavior. Test competing duplicate introductions and same-token replay under contention. This verifies an already required attribution guarantee without expanding product scope. Submit actual results for independent Checker review; do not infer a PASS from the transaction syntax.

## Verification and release limits
This run performed source/test-assertion inspection only. No Python, Node, browser, live integration, security penetration, load or deployment test was executed. Historical handoff reports 43 Python and 13 Node tests plus Chromium smoke checks; these were not rerun today. No new regressions or corrections were runtime-demonstrated.

Status: implemented local application with bounded historical verification; not declared development-complete, release-ready, deployed, production-ready or user-validated. Vishwa/CAM retain live credentials/services, production setup, real data, spending, deployment and acceptance decisions. No next project selected.
