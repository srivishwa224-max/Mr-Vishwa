# Backend foundation — 2026-10-10

Python standard-library SQLite repository, built with synthetic fixtures and no live services. Run `python3 -m unittest discover -s backend -p 'test_*.py' -v` from the project folder. Six tests passed: persistence after reopen, cross-workspace access denial, owner-only membership management, cross-workspace partner constraint/transaction rollback, audit update/delete rejection and parameterized SQL handling.

This is an internal persistence component, not an HTTP API or complete backend. Actor IDs must come from a trusted authentication layer; never accept them directly from browser input. Authentication, sessions, endpoint authorization, secure referrer portal, production migrations, backup/restore and frontend integration remain unfinished. SQLite file owners can alter/drop audit triggers, so this does not claim administrator-proof audit integrity. Use a private database path outside any static web root; never commit database files.

The existing browser prototype is unchanged. No browser pass or user acceptance is claimed. Further work: trusted login/session integration and API boundary, then full referral/commission workflows and source checklist. No paid accounts, credentials, real data, outreach or deployment used.
