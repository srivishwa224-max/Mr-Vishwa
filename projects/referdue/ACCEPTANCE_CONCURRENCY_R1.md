# Acceptance concurrency PASS — 2026-10-17

Task `referdue/acceptance-concurrency/r1` is independently verified PASS / READY_FOR_NEXT at test commit `eef820e34fe499d44feefc52f863b42a917c0395`. Added `backend/test_acceptance_concurrency.py` under ReferDue; application code unchanged. Self-tests: 2 targeted, 45 Python, 13 Node tests passed; both JavaScript syntax checks passed. Checker independently reproduced 45 backend tests and 100 repetitions of the two-test suite (200 race cases), with no corrections. See `projects/referdue/CHECKER_ACCEPTANCE_CONCURRENCY_R1.md` for the bounded verdict.

This closes the audit's concurrent acceptance evidence gap, not Phase 3 or overall release readiness. Next recommended bounded task: workspace-isolated duplicate-normalization tests from the acceptance audit, subject to CAM coordination. Directory CRUD/versioned terms/recipient identity scope decisions remain with CAM. No browser or live-service checks were rerun today. Credentials, real data, spending, live services and deployment remain approval-gated. No next project activated. Earlier submission states below are historical.

# Acceptance concurrency verification — 2026-10-17

- project_id: referdue
- task_id: acceptance-concurrency
- revision: r1
- producer: EO-compatible continuation worker
- consumer: independent Checker
- artifact_ref: projects/referdue/backend/test_acceptance_concurrency.py
- artifact_version: eef820e34fe499d44feefc52f863b42a917c0395
- status: SUBMITTED / AWAITING_CHECKER

## Starting state and approved scope
Fresh queue, CURRENT_HANDOFF.md, FULL_APP_COMPLETION.md, October 16 audit and latest Notion report identify concurrent acceptance as the next bounded task. Existing Chromium/accessibility and WSGI-read Checker results remain valid for their scopes. No newer activation or conflicting state was found in those sources. Phase 3 remains open.

## Change and acceptance mapping
Added two synthetic, temporary-SQLite tests. Separate worker-owned connections synchronize at a barrier before acceptance; the scheduler may choose either winner. Competing introductions share an email but have distinct companies/phones, so the loser attempts a unique company attribution insertion before encountering the shared email conflict. Assertions require exactly one winner and claim, exactly three winner-owned keys, one outbox record and acceptance audit event, no loser stage/token change, and rejection of winner-token replay. The second test races the same token and requires exactly one successful consumption.

No application behavior changed. No network, credentials, real records, payout or external service used. The tests are bounded concurrency coverage, not exhaustive interleaving proof or load testing. No HTTP concurrency or recipient-identity claim is made.

## Self-test evidence actually executed
From the local ReferDue folder:
- python -m unittest discover -s backend -p 'test_acceptance_concurrency.py' -v: 2 passed.
- python -m unittest discover -s backend -p 'test_*.py': 45 passed.
- node --test tests/core.test.mjs: 13 passed.
- node --check backend/workspace.js: exit 0.
- node --check backend/browser_check.cjs: exit 0.

git hash-object confirmed local store.py and workflows.py exactly matched freshly fetched repository blobs f5b9ae817f3c6a994fdaa879ab174143a0644028 and b867e921e119e6e9aa988cbc94596694d1ccf284. The committed new test was read back. Full-suite counts describe local execution; no new remote CI/browser run is claimed.

## Limits and next action
Await actual independent Checker outcome before marking this task PASS. No browser, live email, deployment-host, penetration, accessibility or capacity test was run today. Whole-app completion and production readiness remain unclaimed. After this task passes, a useful next bounded unit is the workspace-isolated duplicate-normalization matrix identified in the acceptance audit, subject to current CAM coordination. CAM must resolve directory CRUD/versioned terms/recipient-identity scope differences. Vishwa retains live services, credentials, real data, spending, publication, deployment and final acceptance. Do not activate another project.

Rollback: this revision only adds a test; revert that specific test commit if CAM requests it. No database migration or application rollback is required.
