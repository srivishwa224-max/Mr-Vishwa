# Duplicate isolation PASS — 2026-10-18

Task `referdue/duplicate-isolation/r1` independently PASS / READY_FOR_NEXT at `0a13cd1511715bd7aa03dcb53639207e8b14527c`. Added five synthetic normalization, no-write and workspace-isolation tests; production code unchanged. Self-test and independent Checker each passed 5 targeted and 50 backend tests; no corrections. See ReferDue's `CHECKER_DUPLICATE_ISOLATION_R1.md`. Earlier submission statuses below are historical.

Phase 3 remains open. Next recommended bounded verification: evidence attachment size boundaries and authorized access/denial cases from the core audit, subject to CAM coordination. Directory CRUD/versioned terms/recipient-identity scope decisions remain unresolved with CAM. No browser, Node, live-service, deployment or load testing performed today. No next project activated. Credentials, real data, spending, live services, deployment and release approval remain reserved for Vishwa.

# Acceptance concurrency PASS — 2026-10-17

Task `referdue/acceptance-concurrency/r1` is independently verified PASS / READY_FOR_NEXT at test commit `eef820e34fe499d44feefc52f863b42a917c0395`. Added `backend/test_acceptance_concurrency.py` under ReferDue; application code unchanged. Self-tests: 2 targeted, 45 Python, 13 Node tests passed; both JavaScript syntax checks passed. Checker independently reproduced 45 backend tests and 100 repetitions of the two-test suite (200 race cases), with no corrections. See `projects/referdue/CHECKER_ACCEPTANCE_CONCURRENCY_R1.md` for the bounded verdict.

This closes the audit's concurrent acceptance evidence gap, not Phase 3 or overall release readiness. Next recommended bounded task: workspace-isolated duplicate-normalization tests from the acceptance audit, subject to CAM coordination. Directory CRUD/versioned terms/recipient identity scope decisions remain with CAM. No browser or live-service checks were rerun today. Credentials, real data, spending, live services and deployment remain approval-gated. No next project activated. Earlier submission states below are historical.

# Acceptance audit checkpoint — 2026-10-16

Completed the core requirement-to-code/test evidence map: ACCEPTANCE_EVIDENCE_2026-10-16.md (audit commit bbd7da629148ee024fa48757f984ba4be2c2adad). Documentation-only review; no tests executed or new Checker verdict. Phase 3 remains open. Existing bounded Checker PASS results are preserved.

Next safe unit: deterministic concurrent competing-acceptance tests with synthetic data, asserting one winner and atomic loser rollback. Existing payment concurrency tests do not prove acceptance concurrency. CAM must resolve stricter later-checklist wording on directory CRUD, versioned terms and recipient identity; this audit does not waive or expand scope. CSV meets the original PDF-or-CSV feature. No project activation or deployment authorized.

# Current coordination checkpoint — 2026-10-15

ReferDue remains in Phase 3. The latest bounded browser/accessibility Checker PASS below stands; older Chromium-unavailable statements are historical, not current blockers. No new code or tests were executed for this documentation checkpoint.

Next safe unit: reconcile each required core acceptance criterion in FULL_APP_COMPLETION.md with current implementation and named tests, distinguishing verified requirements, unverified requirements and future backlog. The original table is a dated baseline, not evidence that subsequently implemented features are still absent. Do not declare development complete until that mapping supports it.

CAM/Vishwa alone activates the next project. At verified completion, hand off and stop; do not follow the historical automatic-selection procedure. Live services, credentials, spending, production deployment and final approval remain reserved for Vishwa. No new Checker verdict is claimed for this documentation-only update.

## Responsive/accessibility smoke Checker result — 2026-10-14
- Task `referdue/responsive-accessibility/r1` is PASS / READY_FOR_NEXT at merged commit `1de3c15af5642d4c614d7606547e50236d34b2c1`.
- Successful run [38564402199](https://github.com/srivishwa224-max/Mr-Vishwa/actions/runs/38564402199) executed 43 Python tests, 13 Node tests, both JavaScript syntax checks and the real Chromium journey on a disposable loopback database.
- Chromium asserted desktop and 390×844 mobile horizontal fit, accessible names on visible controls, document language, responsive viewport metadata, exactly one visible H1, the status live region and visible keyboard focus.
- Independent Checker reproduced 43/43 Python and 13/13 Node tests, inspected the exact diff and CI logs, and issued PASS with no correction.
- Scope limit: this is a two-state Chromium smoke check, not a full WCAG audit, assistive-technology test, multi-browser/device review or production-host verification.
- Phase 3 remains open. Live SMTP, credentials, real data, deployment and release approval remain reserved for Vishwa.

## Chromium CI reconciliation — 2026-10-13
This section supersedes the older statements below that Chromium is absent or browser acceptance is unexecuted.
- Task `referdue/chromium-ci/r1` is PASS / READY_FOR_NEXT. A free GitHub Actions workflow runs the existing synthetic browser script on Chromium headless shell with read-only repository permissions and no secrets.
- Verified run [38274609227](https://github.com/srivishwa224-max/Mr-Vishwa/actions/runs/38274609227) completed successfully on 2026-10-12. Actual evidence: 43 Python tests passed, 13 Node tests passed, both JavaScript syntax checks passed, and the Chromium journey completed account verification through workspace, referral acceptance, revenue, approval, payment recording and reload.
- Independent Checker inspected the exact implementation, run result and job logs, reproduced the 43 Python and 13 Node tests, and issued PASS with no correction.
- Installed workflow commit: `a253cd3b830a3ff54d5f8affed5f195c6a93925b`. No deployment, credential, real data, live service or paid service was used.
- Remaining browser-related gate: the script changes to a mobile viewport but does not assert responsive layout or accessibility. Production HTTPS hosting and live-service behavior are also unverified.
- Phase 3 remains open. Do not select another project.

## Checker result — referdue/release-concurrency/r1 — 2026-10-12
- Independent Checker retrieved commit `bc3e3542030dacf7c257e7795f8e43ee1a606ed3`, reproduced the targeted test and all 43 backend tests, and issued PASS.
- Checker also repeated the targeted test 20 times; all passed, covering 640 authenticated reads.
- Task state: PASS / READY_FOR_NEXT. Scope remains a synthetic concurrency smoke check only, not production capacity or overall release readiness.
- Immutable record: `CHECKER_RELEASE_CONCURRENCY_R1.md`.

## Concurrent WSGI read verification — 2026-10-12 evening
- Task ID: `referdue/release-concurrency/r1`; producer: scheduled EO-compatible continuation; status: SUBMITTED / AWAITING_CHECKER at commit time.
- Added a synthetic concurrency test that registers and verifies an account, creates a workspace, then performs 32 authenticated workspace reads across eight threads through the HTTPS WSGI application.
- Self-test result: every request returned 200 and the exact authorized workspace; the complete suite reached 43 passing Python tests. Both JavaScript syntax checks passed.
- This is a bounded concurrency smoke check, not a capacity benchmark, denial-of-service assessment or production-host load test. Browser acceptance remains open.

## Backup and recovery update — 2026-10-12
- Added `backend/backup.py`, a standard-library operator tool for online SQLite backups, read-only integrity checks and restore into a new path. It never overwrites an existing backup or live database, verifies the copy before publishing it and restricts new database files to owner read/write permissions on supported systems.
- Verified a synthetic backup and recovery round trip, preserved committed data, rejected overwrite attempts and rejected a corrupt source without creating a destination. This closes the missing built-in recovery-tool gap, but an operator should still rehearse recovery on the real deployment host after deployment is approved.
- Private-path usage: `python backup.py backup /private/live.sqlite /private/backups/referdue-YYYY-MM-DD.sqlite`; `python backup.py check /private/backups/referdue-YYYY-MM-DD.sqlite`; `python backup.py restore /private/backups/referdue-YYYY-MM-DD.sqlite /private/recovery-test.sqlite`.
- Stop the application and notification worker before replacing a live database. Restore intentionally refuses replacement; promoting a verified recovery file remains a manual deployment operation.
- Actual verification: 42 Python tests pass and both JavaScript syntax checks pass. Browser acceptance remains open because the Playwright Chromium executable is still absent.

## Account and security update — 2026-10-11
This section supersedes the older account-security and legacy-record gaps below.
- Email verification is required before workspace access. Verification and reset links expire after 30 minutes and are single-use; reissue invalidates old links. Reset revokes all sessions. Account responses never return a token.
- Login/account-request rate limits persist in SQLite across restarts. HTTP request limits are also persisted. These are baseline abuse controls, not proof of capacity under attack.
- Account email delivery uses the existing dry-run-first notification adapter. Pending email bodies contain private capability links in the private database; sent bodies are cleared. Keep databases and backups private. No live email was sent.
- Older backend introductions can have missing details completed without replacing the referral ID, partner, prospect or ledger. This does not import the separate browser-local prototype.
- Added an HTTPS-only WSGI application boundary: secure cookies, exact Host/Origin checks, restricted static assets and security headers. Configure REFERDUE_DATABASE outside the source folder and REFERDUE_ORIGIN as the exact HTTPS origin when deploying through a production WSGI server and trusted HTTPS proxy. Entrypoint: backend/wsgi.py, application. Proxy/server installation, TLS and real deployment were not performed. Do not expose the development HTTPServer.
- Actual verification: 39 Python tests pass, including reset expiry/replay, session revocation, throttling after restart, verification enforcement, fake account-mail delivery, WSGI secure-cookie/HTTPS checks and legacy preservation. Both JavaScript syntax checks pass.
- Browser script now requires REFERDUE_TEST_DB pointing to the same fresh disposable synthetic database used by the test server. It uses test-only mailbox access to verify the sample account. Never point it at real data.
- Browser acceptance remains unexecuted. Both ordinary Chromium and the supported headless-shell installation failed with invalid downloaded archives. No visual/responsive acceptance or live-production readiness is claimed.
- Remaining gates: browser end-to-end and visual/accessibility review; independent security/load/backup recovery verification; live mail and deployment checks only after Vishwa authorizes/configures those services. Phase 3 stays open; do not select another project.

# ReferDue local application — current handoff
Updated 2026-10-10. This is the current status; earlier prototype notes are historical.

## Start
From projects/referdue/backend run:
`python server.py --database /private/path/outside/project/referdue.sqlite`
On Windows use `py` instead of `python`, and provide a full writable database path outside the downloaded project.
Open http://127.0.0.1:4174. Use synthetic accounts and sample-only passwords. No paid dependency or live service is required.

## Connected workflow
1. Create a sample account and workspace. Add a partner, contact email and optional sample payment reference.
2. Submit prospect/company/contact/service/date/source/notes/estimated value. Review duplicate warnings.
3. Select the referral and record fixed or percentage terms once.
4. Owner generates an acceptance link. Open it in a separate browser context, review terms and explicitly accept. Links expire after 24 hours and cannot be reused; generating a new link revokes the previous one.
5. Move Accepted → Contacted → Won (Accepted → Won is allowed). Submitted/Accepted/Contacted may become Lost. Lost and Won are terminal manual stages. Revenue requires Won.
6. Record customer revenue. Owner approves earned commission with a due date. Record external commission payments; overpayments and repeated request IDs are rejected/deduplicated. No money moves.
7. Owner generates a private referrer link for a selected partner. It expires in seven days; reissuing revokes the previous link. It exposes only that partner's referrals and ledger. Possession grants read access, so links must stay private.
8. Upload PDF/PNG/JPEG/text evidence (up to 1 MB). Files are stored in the private database and downloaded as attachments, not rendered as active HTML.
9. Download a selected partner's monthly CSV statement. Months and event timestamps use UTC. Opening due, monthly revenue/accrual/payments and closing due are separated by referral/currency. Spreadsheet formula prefixes in prospect names are escaped.
10. View the owner-only notification outbox. Acceptance, stage, approval and payment events are queued; payment and its notification commit together.

## Notifications: disabled unless explicitly operated
`python notifications.py --database /private/path/referdue.sqlite` is a dry-run count only.
The worker supports a TLS SMTP adapter; live sending requires Vishwa's explicit operation with `--send` and his locally configured REFERDUE_SMTP_HOST, REFERDUE_SMTP_PORT, REFERDUE_SMTP_USER, REFERDUE_SMTP_PASSWORD and REFERDUE_FROM. Never paste or commit these values. No live SMTP connection or email sending was performed here.
Use exactly one worker. Delivery is at-least-once if the process crashes after SMTP acceptance but before recording sent status; stable Message-ID is provided but recipients may receive a duplicate. Tests use an in-memory fake transport. Link sharing remains manual; this build does not email private acceptance/portal tokens.

## Verified
28 Python tests passed using `python -m unittest discover -s backend -p 'test_*.py'` from the project folder. Includes real HTTP auth boundary tests, workspace isolation, expiry/logout, ledger accuracy/retries, two-connection overpayment prevention, acceptance expiry/replay/first claim, portal isolation, stages, approval/due/overdue dates, evidence validation, statement totals/CSV safety, notification dry-run/failure/retry and atomic payment/outbox rollback.
JavaScript syntax checks passed for workspace.js and browser_check.cjs.

## Browser gate still open
Chromium is absent. Playwright installation was attempted, but the downloaded archive was invalid and installation failed. No visual/browser acceptance is claimed.
A repeatable script is provided: run the server with a fresh disposable database, install Playwright/Chromium in a browser-capable development environment, then run `node backend/browser_check.cjs` from the project folder. The script is syntax-checked only, not executed here. It covers signup through acceptance, revenue, approval, payout and reload. Responsive visual/accessibility review and file-download UX still need checking.

## Remaining engineering/release limitations
- Loopback HTTPServer is a development server, not a production host. HTTPS, production web serving, load/abuse controls and deployment configuration require further engineering verification.
- Account email ownership verification, password recovery and production-grade persistent authentication throttling remain unbuilt. These are engineering gaps, not merely credentials Vishwa must supply.
- Legacy introductions created before full referral fields have no acceptance metadata. They remain preserved but cannot use the new Won/revenue flow; no automatic migration was fabricated.
- The minimal connected screen is separate from the original styled prototype. No visual redesign was approved.
- Attribution conservatively reserves normalized company, email and phone identifiers on first acceptance within a workspace. Different prospects sharing a company can conflict; no override/split attribution is implemented.
- Terms are insert-only. Approvals use one due date for the referral's commission; recurring commissions, refunds, corrections and negotiated term changes need a future explicit policy.
- Evidence signatures/extensions are checked but malware scanning is not implemented. Use synthetic files only.
- Append-only triggers protect application writes, not a database administrator who can drop triggers. Private backups and file access controls are essential.
- Notification delivery has been fake-tested only. Sender/provider setup, real deliverability and private link delivery are not verified.
- Acceptance links are bearer capabilities, not independent proof of the recipient's legal identity.

## Preservation and ownership
Keep the project code in GitHub. Keep database/backups outside the source tree, private and never committed. Stop the local server before copying the SQLite file, or use SQLite's online backup API. Existing prototype localStorage records are not migrated.
Vishwa-only actions remain live accounts/credentials, spending, real-data approval, real payments, external contact/commitments and publication/deployment. The engineering gaps above remain the assistant's work. Phase 3 must stay open; do not start another project yet.
