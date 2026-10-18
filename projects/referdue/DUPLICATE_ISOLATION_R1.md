# Duplicate isolation verification — 2026-10-18

project_id: referdue
 task_id: duplicate-isolation
 revision: r1
 producer: EO
 consumer: Checker
 artifact_version: 0a13cd1511715bd7aa03dcb53639207e8b14527c
 artifact_ref: backend/test_duplicate_isolation.py
 status: SUBMITTED / AWAITING_CHECKER

Starting state: current queue/handoff and October 17 Notion report agree acceptance concurrency is PASS and duplicate normalization/isolation is next. Prior bounded Checker results preserved. Phase 3 open.

Added five synthetic tests: independent company/email/phone normalization with unchanged database on warning; identical records across workspaces return only local IDs; unauthorized actor denied without writes; explicit confirmation adds local duplicate; empty email and short phone do not match unrelated companies. No production code changed. Rollback is removal of this added test only if requested; no migration.

Actual commands from local ReferDue folder:
- python -m unittest discover -s backend -p 'test_duplicate_isolation.py' -v: 5 passed.
- python -m unittest discover -s backend -p 'test_*.py': 50 passed.

Local workflows.py blob b867e921e119e6e9aa988cbc94596694d1ccf284 matched fresh repository content. No browser, Node, remote CI, accessibility, load, live-service or deployment tests run today. No runtime defect observed. Workflow-level tests do not establish complete HTTP/browser isolation or exhaustive Unicode/phone normalization policy.

Next action: independent Checker review. Next recommended bounded gap after PASS: evidence attachment size boundaries and access-denial tests from the core audit. CAM retains scope decisions about directory CRUD, versioned terms and recipient identity. Vishwa retains credentials, live services, spending, real data, deployment and final release approval. No next project selected; no production-ready claim.
