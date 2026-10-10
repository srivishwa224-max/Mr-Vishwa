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
