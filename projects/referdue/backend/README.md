# Backend foundation — 2026-10-10

Python standard-library SQLite repository, built with synthetic fixtures and no live services. Run `python3 -m unittest discover -s backend -p 'test_*.py' -v` from the project folder. Six tests passed: persistence after reopen, cross-workspace access denial, owner-only membership management, cross-workspace partner constraint/transaction rollback, audit update/delete rejection and parameterized SQL handling.

This is an internal persistence component, not an HTTP API or complete backend. Actor IDs must come from a trusted authentication layer; never accept them directly from browser input. Authentication, sessions, endpoint authorization, secure referrer portal, production migrations, backup/restore and frontend integration remain unfinished. SQLite file owners can alter/drop audit triggers, so this does not claim administrator-proof audit integrity. Use a private database path outside any static web root; never commit database files.

The existing browser prototype is unchanged. No browser pass or user acceptance is claimed. Further work: trusted login/session integration and API boundary, then full referral/commission workflows and source checklist. No paid accounts, credentials, real data, outreach or deployment used.

## Connected local workspace — evening update 2026-10-10

Run from this directory: `python server.py --database /path/outside/project/referdue.sqlite`. On Windows use `py server.py --database C:\Users\YOUR_NAME\referdue.sqlite`. Open http://127.0.0.1:4174. Use a synthetic email and a new sample-only password (12–128 characters), never a real account password. Create a workspace, add a partner, and record an introduction. Another sample account can register, then an owner can add its email as a team member. Refresh/restart preserves SQLite data. Sign-out invalidates the session.

The new minimal connected workspace is a functional development screen, not a redesign of the original UI. The existing commission prototype is preserved separately and is not yet integrated. No automatic migration from localStorage occurs.

Verification: 12 Python tests passed, including real HTTP requests for registration, cookie flags, session use/logout, host/origin rejection and refusal to serve database/source paths. Account tests cover expiry, hashing, forged actor rejection, role checks and login throttling. `node --check backend/workspace.js` passed. Browser interaction/visual checks were not performed.

Development limits: Python HTTPServer is loopback-only and is not suitable for production. Passwords use salted scrypt; sessions store token hashes, expire in one hour, and use HttpOnly/SameSite=Strict cookies. Cookie Secure requires HTTPS and is intentionally absent on this loopback HTTP development server. Email ownership verification, recovery, persistent distributed throttling, HTTPS serving, concurrency/load tests and production session hardening remain open. The global in-memory login throttle is only a development guard. No live email is sent. Production deployment remains prohibited until these and the full-app checklist are verified.

## Connected commission ledger — 2026-10-10
The development workspace now records one-time fixed/percentage terms and customer-revenue/external-commission events through authenticated API routes. All monetary storage uses integer cents, percentage rates use hundredths of a percent, and half-up rounding applies to total earned commission. Fixed fees accrue once after positive revenue. The database transaction serializes payment checks; request IDs prevent retry duplication. UI retains the request ID for a failed attempt while its contents remain unchanged. No money is moved.

Verified: all 16 Python tests passed, including ledger route authorization, partial payments, overpayment rejection, fixed fees, cent rounding, invalid amounts, repeated requests and conflicting IDs; workspace.js syntax check passed. Browser interaction and multi-connection concurrency stress tests remain unverified. Terms are insert-only through this API, not mutually accepted contracts. Commission approval, due dates/overdue states, corrections/refunds, acceptance/attribution, private referrer portal, attachments, statements and notifications remain incomplete. The original prototype stays separate; no existing browser records were migrated. Phase 3 remains open.
