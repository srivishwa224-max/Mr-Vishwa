# ReferDue prototype

ReferDue records a referral introduction and the commission terms attached to it. This first phase is a local browser prototype, designed to check the basic workflow before adding status tracking and partner views.

## Start it

From this folder:

```sh
npm run serve
```

Open `http://localhost:4173`. No package install or paid service is required. To run the calculation and storage checks, use `npm test`.

## Project progress

**Phase 1 is complete:** the local browser prototype captures referral details, commission terms, agreement status, estimates, and stores sample records in the browser. The calculation and storage tests pass.

## Three-phase plan

- Capture referrer, prospect, service, and estimated deal value.
- Record percentage or fixed commission terms.
- Mark whether both sides have agreed to the terms.
- Calculate the estimated commission and keep records in this browser's local storage.

## Limits

- Use sample information only. Data stays in this browser and is not shared with another device or person.
- There is no account system, server database, email, file upload, or payment processing.
- Commission estimates are arithmetic estimates. The parties remain responsible for confirming the agreement and recording actual revenue received.
- External market research found established referral and partner software with overlapping features. This prototype does not prove demand or a unique market position.

## Remaining phases

2. Add referral statuses, a commission ledger, duplicate warnings, and a referrer view.
3. Test and refine the end-to-end demo, then prepare a complete setup and preservation package. Keep credentials, live partner data, payment handling, external account connections, and deployment decisions for Vishwa to do or approve manually.

The original ReferDue idea and project context remain in Notion. No source page was edited.
