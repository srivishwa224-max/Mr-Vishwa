import test from "node:test";
import assert from "node:assert/strict";
import {
  commitReferrals, calculateCommission, createReferral, findPotentialDuplicates, getCommissionLedger,
  getDisplayStatus, loadReferrals, recordCommissionPayment, recordCustomerRevenue,
  saveReferrals, STORAGE_KEY, validateReferral,
} from "../core.mjs";

const example = (extra = {}) => ({
  referrer: "Maya",
  company: "Northstar Studio",
  prospect: "A. Person",
  email: "person.name@example.com",
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
  assert.equal(referral.email, "person.name@example.com");
  assert.equal(referral.status, "Submitted");
  assert.deepEqual(referral.ledger, []);
});

test("duplicate detection normalizes email, phone, and company name", () => {
  const first = createReferral(example());
  const matches = findPotentialDuplicates({
    email: " PERSON.NAME@example.com ",
    phone: "+91 98765 43210",
    company: "northstar-studio",
  }, [first]);
  assert.equal(matches.length, 1);
  assert.deepEqual(matches[0].reasons.sort(), ["company name", "email", "phone"]);
  assert.equal(findPotentialDuplicates({ company: "Different Ltd" }, [first]).length, 0);
  assert.equal(findPotentialDuplicates({ email: "personname@example.com", company: "Different Ltd" }, [first]).length, 0);
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

test("local storage preserves invalid data and migrates valid older records", () => {
  const values = new Map([[STORAGE_KEY, "broken"]]);
  const storage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
  assert.throws(() => loadReferrals(storage), /Writes are blocked/);
  assert.equal(values.get(STORAGE_KEY), "broken");
  const old = createReferral(example());
  delete old.status; delete old.actualRevenue; delete old.commissionPaid; delete old.ledger;
  saveReferrals([{ ...old, id: "one" }], storage);
  const [loaded] = loadReferrals(storage);
  assert.equal(loaded.id, "one");
  assert.equal(loaded.status, "Submitted");
  assert.equal(loaded.actualRevenue, 0);
  assert.deepEqual(loaded.ledger, []);
});


test("fixed commission is earned once, only after customer revenue", () => {
  let record = createReferral(example({ commissionType: "fixed", commissionValue: 50 }));
  assert.equal(getCommissionLedger(record).due, 0);
  assert.throws(() => recordCommissionPayment(record, 1), /greater than the commission due/);
  record = recordCustomerRevenue(record, 100);
  record = recordCustomerRevenue(record, 200);
  assert.equal(getCommissionLedger(record).earned, 50);
  record = recordCommissionPayment(record, 50);
  assert.equal(getDisplayStatus(record), "Commission Paid");
});

test("failed persistence leaves caller state unchanged", () => {
  const previous = [createReferral(example())];
  let state = previous;
  assert.throws(() => { state = commitReferrals([], { setItem() { throw new Error("Quota exceeded"); } }); }, /Quota/);
  assert.equal(state, previous);
});

test("fractional cents, nonfinite and excessive amounts are rejected", () => {
  const record = createReferral(example());
  for (const amount of [0.001, 1.111, Infinity, -1, 1000000001]) {
    assert.throws(() => recordCustomerRevenue(record, amount));
    assert.throws(() => recordCommissionPayment(record, amount));
    assert.ok(validateReferral(example({ dealValue: amount })));
  }
  assert.equal(recordCustomerRevenue(record, 0.01).actualRevenue, 0.01);
});

test("malformed saved records never silently become an empty workspace", () => {
  const record = createReferral(example());
  for (const data of [{}, [null], [{ id: "one" }], [{ ...record, createdAt: "bad" }],
    [{ ...record, ledger: [{ type: "customer-revenue", amount: 2, recordedAt: "bad" }] }], [record, record]]) {
    const raw = JSON.stringify(data);
    assert.throws(() => loadReferrals({ getItem: () => raw }), /Writes are blocked/);
  }
});

test("page includes all literal ID selectors required by app startup", async () => {
  const { readFile } = await import("node:fs/promises");
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const app = await readFile(new URL("../app.mjs", import.meta.url), "utf8");
  for (const [, id] of app.matchAll(/querySelector\("#([a-z-]+)"\)/g)) {
    assert.ok(html.includes('id="' + id + '"'), "Missing DOM element: " + id);
  }
});
