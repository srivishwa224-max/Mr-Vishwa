export const STORAGE_KEY = "referdue.phase1.referrals.v1";

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
    referrer: String(data.referrer).trim(),
    company: String(data.company).trim(),
    prospect: String(data.prospect).trim(),
    service: String(data.service).trim(),
    dealValue: Math.round((Number(data.dealValue) + Number.EPSILON) * 100) / 100,
    currency: data.currency,
    commissionType: data.commissionType,
    commissionValue: Math.round((Number(data.commissionValue) + Number.EPSILON) * 100) / 100,
    commissionEstimate: calculateCommission(data.dealValue, data.commissionType, data.commissionValue),
    termsAgreed: Boolean(data.termsAgreed),
    notes: String(data.notes ?? "").trim(),
  };
}

export function loadReferrals(storage = globalThis.localStorage) {
  try {
    const parsed = JSON.parse(storage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter(item => item && typeof item.id === "string") : [];
  } catch {
    return [];
  }
}

export function saveReferrals(referrals, storage = globalThis.localStorage) {
  storage.setItem(STORAGE_KEY, JSON.stringify(referrals));
}
