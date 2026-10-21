# EO submission: ReferDue submission validation r1

- project_id: referdue
- task_id: submission-validation
- revision: r1
- producer: EO
- consumer: Checker
- status: SUBMITTED
- artifact_ref: projects/referdue/backend/workflows.py; projects/referdue/backend/test_submission_validation.py
- artifact_version: application commit 5deb6f21d640c2fa23287bec9cfbab30bf07be12; test commit 5cd159eb0302c80e2b546191d5b3e0ef73c2d471
- blocker: none
- next_action: Checker independently reproduce the targeted and full backend suites and review the workspace-partner boundary.

## Requirement-to-change mapping

- Persisted submission evidence: the new test checks all referral and detail fields, whitespace trimming, normalized email/identity, estimate cents, starting stage and audit event.
- Validation and atomic rejection: the new test checks missing/invalid required, date, email, amount, length and type cases and asserts referral/detail/activity counts do not change.
- Authorization and isolation: the new test checks unauthorized actors and foreign-workspace partner IDs. Workflows.submit now validates that a non-legacy partner belongs to the requested workspace and returns a deliberate access denial before any insert.

## EO self-test evidence

Executed with synthetic data only:

- cd projects/referdue/backend && python3 -m unittest test_submission_validation.py — PASS, 3 tests.
- cd projects/referdue && python3 -m unittest discover -s backend -p 'test_*.py' — PASS, 59 tests.
- cd projects/referdue && npm test — PASS, 13 tests.
- cd projects/referdue && node --check app.mjs && node --check core.mjs && node --check backend/workspace.js — PASS.

An initial targeted run exposed the foreign-partner path as a raw SQLite integrity error; EO corrected it to a deliberate PermissionError and reran the targeted and full suites successfully.

## Known limits

This bounded task did not run browser, HTTP, live-service, load, accessibility, deployment or production-host checks. It does not resolve CAM decisions on directory CRUD, versioned terms or recipient identity, and it does not establish project or production readiness.

## Rollback

Revert the two artifact commits above. No schema migration or real data was used.
