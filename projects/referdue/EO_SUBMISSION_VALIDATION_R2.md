# EO submission: ReferDue submission validation r2

- project_id: referdue
- task_id: submission-validation
- revision: r2
- producer: EO
- consumer: Checker
- status: SUBMITTED
- artifact_ref: projects/referdue/backend/workflows.py; projects/referdue/backend/test_submission_validation.py
- artifact_version: application commit f6b48310d9b2ce3a0330db5718a094d5f57fb5d2; test commit 4130b2ca4d968f6cd6e2947edcfe748343d475de
- predecessor: r1 Checker FAIL
- blocker: none
- next_action: Checker independently reproduce revision 2 and verify duplicate-warning precedence.

## Correction

Partner/prospect required-field validation and the workspace-partner authorization check now execute before duplicate detection can return. A new regression test first creates a local duplicate, then proves blank partner, blank prospect and a foreign-workspace partner are rejected with the expected exception and unchanged referral/detail/activity counts.

## EO self-test evidence

- Targeted submission suite: PASS, 4 tests.
- Full backend suite: PASS, 60 tests.
- Node suite: PASS, 13 tests.
- JavaScript syntax checks for app.mjs, core.mjs and backend/workspace.js: PASS.

Browser, HTTP, live-service, load, accessibility, deployment and production-host checks were not run. This revision does not establish whole-project readiness.
