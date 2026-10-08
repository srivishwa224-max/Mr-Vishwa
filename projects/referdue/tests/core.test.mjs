import test from "node:test";
import assert from "node:assert/strict";
import {
  calculateCommission, createReferral, findPotentialDuplicates, getCommissionLedger,
  getDisplayStatus, loadReferrals, recordCommissionPayment, recordCustomerRevenue,
  saveReferrals, STORAGE_KEY, validateReferral,
} from "../core.mjs";

const example = (extra = {}) => ({
  referrer: "Maya",
  company: "Northstar Studio",
  prospect: "A. Person",
  email: "person@example.com",
  phone: "+91 98765 43210",
  service: "Design",
  dealValue: "1200.00",
  commissionType: "percent",
  commissionValue: "8",
  currency: "INR",
  termsAgreed: true,
  ...extra,
});

test("percentage commission is rounded to two decimals", () => {
  assert.equal(calculateCommission(1250, "percent", 7.5), 93.75);
  assert.equal(calculateCommission(199.99, "percent", 7.5), 15);
});

test("fixed commission remains fixed and invalid values return zero", () => {
  assert.equal(calculateCommission(5000, "fixed", 125), 125);
  assert.equal(calculateCommission(-1, "percent", 10), 0);
});

test("referral validation rejects percentages above 100 and malformed email", () => {
  assert.match(validateReferral(example({ commissionValue: 101 })), /100%/);
  assert.match(validateReferral(example({ email: "bad-email" })), /valid email/);
});

test("a valid referral stores terms, normalized contact fields and starting status", () => {
  const referral = createReferral(example(), new Date("2026-10-07T10:00:00.000Z"));
  assert.equal(referral.referrer, "Maya");
  assert.equal(referral.commissionEstimate, 96);
  assert.equal(referral.termsAgreed, true);
  assert.equal(referral.email, "person@example.com");
  assert.equal(referral.status, "Submitted");
  assert.deepEqual(referral.ledger, []);
});

test("duplicate detection normalizes email, phone, and company name", () => {
  const first = createReferral(example());
  const matches = findPotentialDuplicates({
    email: " PERSON@example.com ",
    phone: "+91 98765 43210",
    company: "northstar-studio",
  }, [first]);
  assert.equal(matches.length, 1);
  assert.deepEqual(matches[0].reasons.sort(), ["company name", "email", "phone"]);
  assert.equal(findPotentialDuplicates({ company: "Different Ltd" }, [first]).length, 0);
});

test("revenue and partial commission payments update an auditable ledger", () => {
  let referral = createReferral(example());
  referral = recordCustomerRevenue(referral, "1000", new Date("2026-10-08T01:00:00.000Z"));
  assert.equal(getCommissionLedger(referral).earned, 80);
  assert.equal(getCommissionLedger(referral).due, 80);
  assert.equal(getDisplayStatus(referral), "Commission Due");
  referral = recordCommissionPayment(referral, "30", new Date("2026-10-08T02:00:00.000Z"));
  assert.equal(getCommissionLedger(referral).paid, 30);
  assert.equal(getCommissionLedger(referral).due, 50);
  assert.equal(getDisplayStatus(referral), "Commission Due");
  referral = recordCommissionPayment(referral, "50");
  assert.equal(getCommissionLedger(referral).due, 0);
  assert.equal(getDisplayStatus(referral), "Commission Paid");
  assert.equal(referral.ledger.length, 3);
});

test("ledger rejects overpayments and invalid amounts", () => {
  const referral = recordCustomerRevenue(createReferral(example()), 100);
  assert.throws(() => recordCommissionPayment(referral, 9), /greater than the commission due/);
  assert.throws(() => recordCustomerRevenue(referral, 0), /greater than zero/);
});

test("local storage recovers invalid data and migrates older records", () => {
  const values = new Map([[STORAGE_KEY, "broken"]]);
  const storage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
  assert.deepEqual(loadReferrals(storage), []);
  saveReferrals([{ id: "one", company: "Northstar" }], storage);
  const [loaded] = loadReferrals(storage);
  assert.equal(loaded.id, "one");
  assert.equal(loaded.status, "Submitted");
  assert.equal(loaded.actualRevenue, 0);
  assert.deepEqual(loaded.ledger, []);
});
