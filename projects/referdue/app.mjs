import {
  MANUAL_STATUSES, commitReferrals, validateReferral, calculateCommission, createReferral, findPotentialDuplicates,
  formatMoney, getCommissionLedger, getDisplayStatus, loadReferrals,
  recordCommissionPayment, recordCustomerRevenue, saveReferrals, setReferralStatus,
} from "./core.mjs";

const form = document.querySelector("#referral-form");
const errorBox = document.querySelector("#form-error");
const duplicateBox = document.querySelector("#duplicate-warning");
const rows = document.querySelector("#referral-rows");
const emptyState = document.querySelector("#empty-state");
const currencyInput = form.elements.currency;
const dealInput = form.elements.dealValue;
const typeInput = form.elements.commissionType;
const rateInput = form.elements.commissionValue;
const typeLabel = document.querySelector("#commission-value-label");
const filterInput = document.querySelector("#referrer-filter");
const toast = document.querySelector("#toast");
let referrals = [];
let storageBlocked = false;
try { referrals = loadReferrals(); } catch (error) {
  storageBlocked = true;
  const alert = document.querySelector("#storage-error");
  alert.hidden = false;
  alert.textContent = error.message;
  for (const control of form.elements) control.disabled = true;
}
function commit(next) {
  if (storageBlocked) throw new Error("Writes are blocked until saved records are recovered.");
  referrals = commitReferrals(next);
}
let toastTimer;
let allowDuplicate = false;

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

function statusClass(status) {
  return status.toLowerCase().replaceAll(" ", "-");
}

function makeStatusCell(referral, status) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = "status-pill " + statusClass(status);
  badge.textContent = status;
  cell.append(badge);
  if (getCommissionLedger(referral).revenueReceived === 0) {
    const select = document.createElement("select");
    select.className = "status-select";
    select.setAttribute("aria-label", "Update status for " + referral.company);
    select.dataset.statusFor = referral.id;
    for (const statusOption of MANUAL_STATUSES) {
      const option = document.createElement("option");
      option.value = statusOption;
      option.textContent = statusOption;
      option.selected = referral.status === statusOption;
      select.append(option);
    }
    cell.append(select);
  }
  return cell;
}

function makeLedgerCell(referral) {
  const cell = document.createElement("td");
  cell.className = "ledger-cell";
  const ledger = getCommissionLedger(referral);
  const lines = [
    ["Customer received", ledger.revenueReceived],
    ["Commission earned", ledger.earned],
    ["Commission paid", ledger.paid],
    ["Commission due", ledger.due],
  ];
  for (const lineData of lines) {
    const line = document.createElement("div");
    const caption = document.createElement("span");
    caption.textContent = lineData[0] + ": ";
    const value = document.createElement("strong");
    value.textContent = formatMoney(lineData[1], referral.currency);
    line.append(caption, value);
    cell.append(line);
  }
  if (referral.ledger.length) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "History (" + referral.ledger.length + ")";
    const list = document.createElement("ul");
    for (const entry of [...referral.ledger].reverse()) {
      const item = document.createElement("li");
      const label = entry.type === "customer-revenue" ? "Customer revenue received" : "Commission paid";
      const date = new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(entry.recordedAt));
      item.textContent = label + ": " + formatMoney(entry.amount, referral.currency) + " · " + date;
      list.append(item);
    }
    details.append(summary, list);
    cell.append(details);
  }
  return cell;
}

function makeActionsCell(referral) {
  const cell = document.createElement("td");
  const details = document.createElement("details");
  details.className = "ledger-actions";
  const summary = document.createElement("summary");
  summary.textContent = "Record payment";
  details.append(summary);
  const forms = [
    ["revenue", "Customer revenue received", "Add revenue"],
    ["commission", "Commission paid externally", "Add commission payment"],
  ];
  for (const formInfo of forms) {
    const paymentForm = document.createElement("form");
    paymentForm.className = "mini-ledger-form";
    paymentForm.dataset.ledgerType = formInfo[0];
    paymentForm.dataset.referralId = referral.id;
    const inputLabel = document.createElement("label");
    inputLabel.textContent = formInfo[1];
    const input = document.createElement("input");
    input.name = "amount";
    input.type = "number";
    input.min = "0.01";
    input.step = "0.01";
    input.required = true;
    input.setAttribute("aria-label", formInfo[1] + " for " + referral.company);
    inputLabel.append(input);
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "button button-quiet mini-button";
    submit.textContent = formInfo[2];
    paymentForm.append(inputLabel, submit);
    details.append(paymentForm);
  }
  cell.append(details);
  return cell;
}

function makeSubline(text) {
  const detail = document.createElement("span");
  detail.className = "referral-sub";
  detail.textContent = text;
  return detail;
}

function renderReferrerFilter() {
  const selected = filterInput.value;
  const referrers = [...new Set(referrals.map(item => item.referrer).filter(Boolean))].sort((a, b) => a.localeCompare(b));
  filterInput.replaceChildren(new Option("All referrers", ""));
  for (const referrer of referrers) filterInput.append(new Option(referrer, referrer));
  if (referrers.includes(selected)) filterInput.value = selected;
}

function render() {
  renderReferrerFilter();
  rows.replaceChildren();
  const selectedReferrer = filterInput.value;
  const visible = referrals
    .filter(item => !selectedReferrer || item.referrer === selectedReferrer)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  for (const referral of visible) {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const name = document.createElement("span");
    name.className = "referral-name";
    name.textContent = referral.company;
    const detail = document.createElement("span");
    detail.className = "referral-sub";
    detail.textContent = referral.prospect + " · " + referral.service;
    nameCell.append(name, detail);
    if (referral.email) nameCell.append(makeSubline(referral.email));
    if (referral.phone) nameCell.append(makeSubline(referral.phone));
    row.append(nameCell);
    row.append(makeCell(referral.referrer));
    row.append(makeCell(formatMoney(referral.dealValue, referral.currency)));
    row.append(makeCell(formatMoney(referral.commissionEstimate, referral.currency), "money-cell"));
    row.append(makeStatusCell(referral, getDisplayStatus(referral)));
    row.append(makeLedgerCell(referral));
    const date = new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(referral.createdAt));
    row.append(makeCell(date));
    row.append(makeActionsCell(referral));
    rows.append(row);
  }

  document.querySelector("#stat-total").textContent = String(visible.length);
  const currencyTotals = new Map();
  for (const item of visible) currencyTotals.set(item.currency, (currencyTotals.get(item.currency) || 0) + item.commissionEstimate);
  const commissionText = currencyTotals.size === 0
    ? formatMoney(0, currencyInput.value)
    : [...currencyTotals].map(entry => formatMoney(entry[1], entry[0])).join(" · ");
  document.querySelector("#stat-commission").textContent = commissionText;
  document.querySelector("#stat-agreed").textContent = String(visible.filter(item => item.termsAgreed).length);
  document.querySelector("#record-count").textContent = visible.length + (visible.length === 1 ? " record" : " records");
  emptyState.classList.toggle("visible", visible.length === 0);
  document.querySelector(".table-wrap table").style.display = visible.length === 0 ? "none" : "table";
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function showDuplicateWarning(matches) {
  duplicateBox.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = "Possible duplicate found";
  const copy = document.createElement("p");
  copy.textContent = "Check these existing records before saving. This is a warning; it does not merge or delete records.";
  const list = document.createElement("ul");
  for (const match of matches) {
    const item = document.createElement("li");
    item.textContent = match.referral.company + " — " + match.reasons.join(", ") + " match";
    list.append(item);
  }
  const confirm = document.createElement("button");
  confirm.type = "button";
  confirm.className = "button button-primary";
  confirm.textContent = "Save anyway";
  confirm.addEventListener("click", () => {
    allowDuplicate = true;
    form.requestSubmit();
  }, { once: true });
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "button button-quiet";
  cancel.textContent = "Review form";
  cancel.addEventListener("click", () => { duplicateBox.hidden = true; allowDuplicate = false; });
  const actions = document.createElement("div");
  actions.className = "duplicate-actions";
  actions.append(confirm, cancel);
  duplicateBox.append(title, copy, list, actions);
  duplicateBox.hidden = false;
}

form.addEventListener("input", () => { allowDuplicate = false; duplicateBox.hidden = true; });
typeInput.addEventListener("change", setTypeLabel);
for (const input of [currencyInput, dealInput, rateInput]) input.addEventListener("input", updateEstimate);
currencyInput.addEventListener("change", updateEstimate);
filterInput.addEventListener("change", render);
form.addEventListener("reset", () => setTimeout(() => {
  errorBox.textContent = "";
  duplicateBox.hidden = true;
  allowDuplicate = false;
  setTypeLabel();
}, 0));

form.addEventListener("submit", event => {
  event.preventDefault();
  errorBox.textContent = "";
  const data = Object.fromEntries(new FormData(form).entries());
  data.termsAgreed = form.elements.termsAgreed.checked;
  try {
    const validationError = validateReferral(data);
    if (validationError) throw new Error(validationError);
    const matches = findPotentialDuplicates(data, referrals);
    if (matches.length && !allowDuplicate) {
      showDuplicateWarning(matches);
      return;
    }
    allowDuplicate = false;
    duplicateBox.hidden = true;
    commit([createReferral(data), ...referrals]);
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

rows.addEventListener("change", event => {
  const select = event.target.closest("[data-status-for]");
  if (!select) return;
  try {
    const id = select.dataset.statusFor;
    commit(referrals.map(item => item.id === id ? setReferralStatus(item, select.value) : item));
    render();
    showToast("Referral status updated.");
  } catch (error) {
    showToast(error.message);
    render();
  }
});

rows.addEventListener("submit", event => {
  const paymentForm = event.target.closest("[data-ledger-type]");
  if (!paymentForm) return;
  event.preventDefault();
  const id = paymentForm.dataset.referralId;
  const amount = new FormData(paymentForm).get("amount");
  try {
    commit(referrals.map(item => {
      if (item.id !== id) return item;
      return paymentForm.dataset.ledgerType === "revenue"
        ? recordCustomerRevenue(item, amount)
        : recordCommissionPayment(item, amount);
    }));
    render();
    showToast("Ledger updated. This records an external payment; it does not move money.");
  } catch (error) {
    showToast(error.message);
  }
});

setTypeLabel();
render();
