# ReferDue prototype

ReferDue records referral introductions, agreed commission terms, deal progress, and manually recorded revenue and commission payments. It is a local browser prototype for validating the workflow.

## Start it

From this folder:

```sh
npm run serve
```

Open `http://localhost:4173`. No package install or paid service is required. To run the calculation and storage checks, use `npm test`.

## Project progress

**Phase 1 is complete:** referral capture, terms, estimates, and browser storage.

**Phase 2 is complete:** editable deal stages, duplicate warnings by normalized email/phone/company, a manual commission ledger with partial-payment support, and a referrer filter preview.

**Phase 3 is next:** end-to-end review, refinement, setup and preservation documentation, and a manual user-only handoff.

## Limits

- Use sample information only. Data stays in this browser and is not shared with another device or person.
- There is no account system, server database, email, file upload, or payment processing.
- The referrer filter is a demo view, not an authenticated portal; it does not enforce access separation.
- Duplicate detection only warns. It does not merge records or prevent a user from saving a duplicate.
- Ledger entries record amounts that the user says were received or paid externally. The app does not verify receipts, send money, or provide tamper-proof audit history.
- Commission estimates are arithmetic estimates. The parties remain responsible for confirming the agreement and recording actual revenue received.
- External market research found established referral and partner software with overlapping features. This prototype does not prove demand or a unique market position.

## Remaining phase

3. Test and refine the end-to-end demo, then prepare a complete setup and preservation package. Keep credentials, live partner data, payment handling, external account connections, and deployment decisions for Vishwa to do or approve manually.

## Phase 2 checks

Run the command npm test in this folder. Tests cover commission arithmetic, input validation, normalized duplicate matching, revenue and partial commission events, overpayment rejection, and migration of older browser records.

The original ReferDue idea and project context remain in Notion. No source page was edited.

## Phase 3 review — 2026-10-09
Phase 3 remains in progress: regression fixes and 13 passing tests are recorded in [HANDOFF.md](HANDOFF.md). Browser acceptance is blocked by a missing Chromium executable. The local prototype is not a production-ready SaaS; the handoff lists remaining product gaps and manual actions.
