import { calculateCommission, createReferral, formatMoney, loadReferrals, saveReferrals } from "./core.mjs";

const form = document.querySelector("#referral-form");
const errorBox = document.querySelector("#form-error");
const rows = document.querySelector("#referral-rows");
const emptyState = document.querySelector("#empty-state");
const currencyInput = form.elements.currency;
const dealInput = form.elements.dealValue;
const typeInput = form.elements.commissionType;
const rateInput = form.elements.commissionValue;
const typeLabel = document.querySelector("#commission-value-label");
const toast = document.querySelector("#toast");
let referrals = loadReferrals();
let toastTimer;

function setTypeLabel() {
  const fixed = typeInput.value === "fixed";
  typeLabel.firstChild.textContent = fixed ? "Commission amount" : "Commission rate (%)";
  rateInput.max = fixed ? "" : "100";
  rateInput.placeholder = fixed ? "0.00" : "10";
  updateEstimate();
}

function updateEstimate() {
  const value = calculateCommission(dealInput.value, typeInput.value, rateInput.value);
  document.querySelector("#commission-preview").textContent = formatMoney(value, currencyInput.value);
}

function makeCell(text, className) {
  const cell = document.createElement("td");
  if (className) cell.className = className;
  cell.textContent = text;
  return cell;
}

function render() {
  rows.replaceChildren();
  const sorted = [...referrals].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  for (const referral of sorted) {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const name = document.createElement("span");
    name.className = "referral-name";
    name.textContent = referral.company;
    const detail = document.createElement("span");
    detail.className = "referral-sub";
    detail.textContent = `${referral.prospect} · ${referral.service}`;
    nameCell.append(name, detail);
    row.append(nameCell);
    row.append(makeCell(referral.referrer));
    row.append(makeCell(formatMoney(referral.dealValue, referral.currency)));
    row.append(makeCell(formatMoney(referral.commissionEstimate, referral.currency), "money-cell"));
    const termsCell = document.createElement("td");
    const terms = document.createElement("span");
    terms.className = `term-pill ${referral.termsAgreed ? "agreed" : "pending"}`;
    const dot = document.createElement("i");
    terms.append(dot, document.createTextNode(referral.termsAgreed ? "Agreed" : "Needs confirmation"));
    termsCell.append(terms);
    row.append(termsCell);
    const date = new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(referral.createdAt));
    row.append(makeCell(date));
    rows.append(row);
  }

  const total = referrals.length;
  document.querySelector("#stat-total").textContent = String(total);
  const currencyTotals = new Map();
  for (const item of referrals) currencyTotals.set(item.currency, (currencyTotals.get(item.currency) ?? 0) + item.commissionEstimate);
  const commissionText = currencyTotals.size === 0
    ? formatMoney(0, currencyInput.value)
    : [...currencyTotals].map(([currency, amount]) => formatMoney(amount, currency)).join(" · ");
  document.querySelector("#stat-commission").textContent = commissionText;
  document.querySelector("#stat-agreed").textContent = String(referrals.filter(item => item.termsAgreed).length);
  document.querySelector("#record-count").textContent = `${total} ${total === 1 ? "record" : "records"}`;
  emptyState.classList.toggle("visible", total === 0);
  document.querySelector(".table-wrap table").style.display = total === 0 ? "none" : "table";
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

typeInput.addEventListener("change", setTypeLabel);
for (const input of [currencyInput, dealInput, rateInput]) input.addEventListener("input", updateEstimate);
currencyInput.addEventListener("change", updateEstimate);
form.addEventListener("reset", () => setTimeout(() => { errorBox.textContent = ""; setTypeLabel(); }, 0));
form.addEventListener("submit", event => {
  event.preventDefault();
  errorBox.textContent = "";
  const data = Object.fromEntries(new FormData(form).entries());
  data.termsAgreed = form.elements.termsAgreed.checked;
  try {
    const referral = createReferral(data);
    referrals = [referral, ...referrals];
    saveReferrals(referrals);
    render();
    form.reset();
    currencyInput.value = "INR";
    setTypeLabel();
    showToast("Referral saved in this browser.");
    document.querySelector("#referrals").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    errorBox.textContent = error.message;
  }
});

setTypeLabel();
render();
