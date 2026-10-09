# ReferDue review and handoff

## Status — 2026-10-09
Phase 3 is in progress. This is a local single-browser prototype, not a production-ready SaaS. Do not start the next project yet.

## Run and preserve
Use Node.js 22 or later for `npm test`. From this folder run `python3 -m http.server 4173 --bind 127.0.0.1`, then open http://127.0.0.1:4173. No application dependencies, credentials or paid services are required. Keep this entire project folder and its GitHub history. Stop the local server with Ctrl+C.

Records live under browser localStorage key `referdue.phase1.referrals.v1`, tied to the exact browser profile and origin (including port). Copy the raw value from browser developer tools to a private backup before changing browsers, origins, or stored data. Never commit this backup. Browser clearing deletes records; GitHub preserves source, not browser records. There is no in-app backup/restore workflow.

If the storage alert appears, writes are disabled. Preserve the raw value before repair. Do not clear storage to silence the warning. Inspect a copy for malformed records and test recovery in a separate browser profile before replacing the original value. Syntactically valid but altered local data is not trustworthy accounting evidence.

## Changes and actual verification
- Restored the missing record counter element referenced by rendering.
- Fixed commissions now accrue once after the first positive customer revenue entry, never before revenue. This is an explicit prototype assumption; other contract rules remain unsupported.
- Save operations now persist before replacing in-memory records.
- Malformed saved records now block writes with a recovery notice instead of silently appearing empty. Valid older records receive missing defaults.
- Reject fractional cents, nonfinite values and amounts above 1 billion; revenue totals also have this bound. Supported currencies: INR, USD, GBP, EUR.
- Validate before duplicate confirmation; editing form inputs resets duplicate approval.
- Clarified that agreement status is manually recorded, not verified by another party.

`npm test`: 13 tests passed, zero failed. Coverage includes commission math, duplicates, partial payments, overpayments, old-record migration, corruption, fixed commission timing, failed-save state preservation, amount bounds and required DOM IDs. `node --check app.mjs` and `node --check core.mjs` passed.

Browser launch was attempted with Playwright but failed because the Chromium executable is missing from the environment. No browser interaction, visual, responsive or accessibility acceptance is claimed. Static selector tests are not a substitute. No CI workflow was added outside the allowed project folder.

## Remaining Phase 3 acceptance
In a browser-capable environment, use synthetic information only:
1. Load an empty workspace and confirm no console errors at desktop and mobile widths.
2. Create percentage and fixed referrals. Reload and verify persistence, currency totals and terms count.
3. Trigger each duplicate match; review, edit and save anyway. Verify keyboard access and focus.
4. Change manual status; record revenue, partial commission and remaining commission. Verify status, history and referrer filtering after reload. Reject overpayment and payment before revenue.
5. Simulate storage write failure and confirm no phantom record/status/payment remains. Restore storage and retry.
6. Put malformed data in an isolated test profile; confirm the alert and write block preserve the original raw value.
7. Record actual results and any fixes before marking Phase 3 complete.

## Full SaaS gaps
Implemented locally: referral capture, manual agreement flag, estimates, simple duplicate warnings, manual stages, payment entry/history and a referrer filter.

Still unbuilt: backend persistence, workspaces/team roles, authentication and authorization, secure referrer portal, independent acceptance links, first-accepted attribution, evidence attachments, statements/exports, notifications, due dates/overdue logic, tamper-resistant audit, reconciliation/refunds, backup/restore and multiuser concurrency. Referrer filtering is not access control. Local payment history can be edited in developer tools. No production completion claim is appropriate even after prototype acceptance passes.

## Vishwa-only actions, reserved for later
Choose and configure live accounts/credentials, approve costs, review commission rules and legal/privacy requirements, authorize real-data use, connect services, contact partners, perform real payments, and approve publication/deployment. None was performed. Ordinary missing product features above remain engineering work, not tasks disguised as a credential handoff.
