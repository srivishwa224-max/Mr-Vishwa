import test from "node:test";
import assert from "node:assert/strict";
import { calculateCommission, createReferral, loadReferrals, saveReferrals, STORAGE_KEY, validateReferral } from "../core.mjs";

test("percentage commission is rounded to two decimals", () => {
  assert.equal(calculateCommission(1250, "percent", 7.5), 93.75);
  assert.equal(calculateCommission(199.99, "percent", 7.5), 15);
});

test("fixed commission remains fixed and invalid values return zero", () => {
  assert.equal(calculateCommission(5000, "fixed", 125), 125);
  assert.equal(calculateCommission(-1, "percent", 10), 0);
});

test("referral validation rejects percentages above 100", () => {
  const error = validateReferral({ referrer: "A", company: "B", prospect: "C", service: "D", dealValue: 10, commissionType: "percent", commissionValue: 101, currency: "INR" });
  assert.match(error, /100%/);
});

test("a valid referral stores the exact terms and computed estimate", () => {
  const referral = createReferral({ referrer: " Maya ", company: "Northstar", prospect: "A. Person", service: "Design", dealValue: "1200.00", commissionType: "percent", commissionValue: "8", currency: "INR", termsAgreed: true }, new Date("2026-10-07T10:00:00.000Z"));
  assert.equal(referral.referrer, "Maya");
  assert.equal(referral.commissionEstimate, 96);
  assert.equal(referral.termsAgreed, true);
  assert.equal(referral.createdAt, "2026-10-07T10:00:00.000Z");
});

test("local storage helpers handle invalid data and round-trip records", () => {
  const values = new Map([[STORAGE_KEY, "broken"]]);
  const storage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
  assert.deepEqual(loadReferrals(storage), []);
  saveReferrals([{ id: "one", company: "Northstar" }], storage);
  assert.deepEqual(loadReferrals(storage), [{ id: "one", company: "Northstar" }]);
});
