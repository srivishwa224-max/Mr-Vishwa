export const STORAGE_KEY = "referdue.phase1.referrals.v1";

export const MANUAL_STATUSES = ["Submitted", "Accepted", "Contacted", "Won", "Lost"];
export const PAYMENT_STATUSES = ["Commission Due", "Commission Paid"];

export function calculateCommission(dealValue, commissionType, commissionValue) {
  const deal = Number(dealValue);
  const rule = Number(commissionValue);
  if (!Number.isFinite(deal) || !Number.isFinite(rule) || deal < 0 || rule < 0) return 0;
  const amount = commissionType === "percent" ? deal * rule / 100 : rule;
  return Math.round((amount + Number.EPSILON) * 100) / 100;
}

export function validateReferral(data) {
  const required = ["referrer", "company", "prospect", "service"];
  for (const field of required) {
    if (!String(data[field] ?? "").trim()) return `${field} is required.`;
  }
  const dealValue = Number(data.dealValue);
  const commissionValue = Number(data.commissionValue);
  if (!Number.isFinite(dealValue) || dealValue <= 0) return "Enter an estimated deal value greater than zero.";
  if (!Number.isFinite(commissionValue) || commissionValue <= 0) return "Enter a commission amount greater than zero.";
  if (data.commissionType === "percent" && commissionValue > 100) return "A percentage commission cannot be greater than 100%.";
  if (!["percent", "fixed"].includes(data.commissionType)) return "Choose a valid commission type.";
  if (!/^[A-Z]{3}$/.test(String(data.currency ?? ""))) return "Choose a valid currency.";
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(data.email).trim())) return "Enter a valid email address or leave it blank.";
  return "";
}

export function formatMoney(amount, currency = "INR") {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(amount) || 0);
}

export function createReferral(data, now = new Date()) {
  const error = validateReferral(data);
  if (error) throw new Error(error);
  const id = globalThis.crypto?.randomUUID?.() ?? `rd-${now.getTime()}-${Math.random().toString(16).slice(2)}`;
  return {
    id,
    createdAt: now.toISOString(),
    updatedAt: now.toISOString(),
    referrer: String(data.referrer).trim(),
    company: String(data.company).trim(),
    prospect: String(data.prospect).trim(),
    email: String(data.email ?? "").trim().toLowerCase(),
    phone: String(data.phone ?? "").trim(),
    service: String(data.service).trim(),
    dealValue: roundMoney(data.dealValue),
    currency: data.currency,
    commissionType: data.commissionType,
    commissionValue: roundMoney(data.commissionValue),
    commissionEstimate: calculateCommission(data.dealValue, data.commissionType, data.commissionValue),
    termsAgreed: Boolean(data.termsAgreed),
    notes: String(data.notes ?? "").trim(),
    status: "Submitted",
    actualRevenue: 0,
    commissionPaid: 0,
    ledger: [],
  };
}

function roundMoney(value) {
  return Math.round((Number(value) + Number.EPSILON) * 100) / 100;
}

export function normalizeIdentity(value) {
  return String(value ?? "").normalize("NFKC").trim().toLocaleLowerCase("en").replace(/[\s\p{P}\p{S}]+/gu, "");
}

export function normalizePhone(value) {
  return String(value ?? "").replace(/\D/g, "");
}

export function findPotentialDuplicates(data, referrals) {
  const email = String(data.email ?? "").trim().toLocaleLowerCase("en");
  const phone = normalizePhone(data.phone);
  const company = normalizeIdentity(data.company);
  const matches = [];
  for (const referral of referrals) {
    const reasons = [];
    if (email && String(referral.email ?? "").trim().toLocaleLowerCase("en") === email) reasons.push("email");
    if (phone.length >= 7 && normalizePhone(referral.phone) === phone) reasons.push("phone");
    if (company && normalizeIdentity(referral.company) === company) reasons.push("company name");
    if (reasons.length) matches.push({ referral, reasons });
  }
  return matches;
}

export function loadReferrals(storage = globalThis.localStorage) {
  try {
    const parsed = JSON.parse(storage.getItem(STORAGE_KEY) ?? "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(item => item && typeof item.id === "string").map(item => ({
      ...item,
      status: [...MANUAL_STATUSES, ...PAYMENT_STATUSES].includes(item.status) ? item.status : "Submitted",
      email: String(item.email ?? ""),
      phone: String(item.phone ?? ""),
      actualRevenue: Number(item.actualRevenue) || 0,
      commissionPaid: Number(item.commissionPaid) || 0,
      ledger: Array.isArray(item.ledger) ? item.ledger : [],
    }));
  } catch {
    return [];
  }
}

export function saveReferrals(referrals, storage = globalThis.localStorage) {
  storage.setItem(STORAGE_KEY, JSON.stringify(referrals));
}

export function getCommissionLedger(referral) {
  const earned = calculateCommission(referral.actualRevenue, referral.commissionType, referral.commissionValue);
  const paid = roundMoney(referral.commissionPaid ?? 0);
  return { revenueReceived: roundMoney(referral.actualRevenue ?? 0), earned, paid, due: Math.max(0, roundMoney(earned - paid)) };
}

export function getDisplayStatus(referral) {
  const { revenueReceived, due } = getCommissionLedger(referral);
  if (revenueReceived > 0) return due > 0 ? "Commission Due" : "Commission Paid";
  return MANUAL_STATUSES.includes(referral.status) ? referral.status : "Submitted";
}

export function setReferralStatus(referral, nextStatus, now = new Date()) {
  if (!MANUAL_STATUSES.includes(nextStatus)) throw new Error("Choose a valid deal status.");
  if (getCommissionLedger(referral).revenueReceived > 0) throw new Error("Payment has been recorded; deal status now comes from the ledger.");
  return { ...referral, status: nextStatus, updatedAt: now.toISOString() };
}

export function recordCustomerRevenue(referral, amount, now = new Date()) {
  const value = Number(amount);
  if (!Number.isFinite(value) || value <= 0) throw new Error("Enter revenue received greater than zero.");
  const rounded = roundMoney(value);
  const updated = {
    ...referral,
    actualRevenue: roundMoney((Number(referral.actualRevenue) || 0) + rounded),
    status: "Commission Due",
    updatedAt: now.toISOString(),
    ledger: [...(Array.isArray(referral.ledger) ? referral.ledger : []), { type: "customer-revenue", amount: rounded, recordedAt: now.toISOString() }],
  };
  if (getCommissionLedger(updated).due === 0) updated.status = "Commission Paid";
  return updated;
}

export function recordCommissionPayment(referral, amount, now = new Date()) {
  const value = Number(amount);
  if (!Number.isFinite(value) || value <= 0) throw new Error("Enter a commission payment greater than zero.");
  const rounded = roundMoney(value);
  const ledger = getCommissionLedger(referral);
  if (rounded > ledger.due) throw new Error(`Payment is greater than the commission due (${ledger.due.toFixed(2)}).`);
  const updated = {
    ...referral,
    commissionPaid: roundMoney(ledger.paid + rounded),
    updatedAt: now.toISOString(),
    ledger: [...(Array.isArray(referral.ledger) ? referral.ledger : []), { type: "commission-payment", amount: rounded, recordedAt: now.toISOString() }],
  };
  updated.status = getCommissionLedger(updated).due > 0 ? "Commission Due" : "Commission Paid";
  return updated;
}
