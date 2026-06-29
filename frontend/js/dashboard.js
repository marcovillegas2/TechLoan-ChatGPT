const API_BASE_URL = window.TECHLOAN_API_URL || "http://127.0.0.1:8000";

const totalEquipmentEl = document.getElementById("totalEquipment");
const availableEquipmentEl = document.getElementById("availableEquipment");
const loanedEquipmentEl = document.getElementById("loanedEquipment");
const overdueLoansEl = document.getElementById("overdueLoans");
const equipmentChartEl = document.getElementById("equipmentChart");
const loanChartEl = document.getElementById("loanChart");
const overdueUsersBody = document.getElementById("overdueUsersBody");
const emptyState = document.getElementById("emptyState");

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function apiRequest(path) {
  const response = await fetch(apiUrl(path), {
    headers: {
      "Content-Type": "application/json",
    },
  });

  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text ? { detail: text } : null;
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || "Error inesperado";
    const error = new Error(detail);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("es-PE");
}

function normalizeEquipmentKey(key) {
  if (key === "AVAILABLE") return "DISPONIBLE";
  if (key === "LOANED") return "PRESTADO";
  return key;
}

function normalizeLoanKey(key) {
  if (key === "ACTIVE") return "ACTIVO";
  if (key === "RETURNED") return "DEVUELTO";
  if (key === "OVERDUE") return "VENCIDO";
  return key;
}

function getDistributionValue(distribution, ...keys) {
  for (const key of keys) {
    if (distribution && Object.prototype.hasOwnProperty.call(distribution, key)) {
      return Number(distribution[key]) || 0;
    }
  }
  return 0;
}

function setSummary(summary = {}) {
  totalEquipmentEl.textContent = summary.total_equipment ?? 0;
  availableEquipmentEl.textContent = summary.available_equipment ?? 0;
  loanedEquipmentEl.textContent = summary.loaned_equipment ?? 0;
  overdueLoansEl.textContent = summary.overdue_loans ?? 0;
}

function buildChartRow(label, value, max, colorClass) {
  const row = document.createElement("div");
  row.className = "chart__row";

  const labelEl = document.createElement("div");
  labelEl.className = "chart__label";
  labelEl.textContent = label;

  const track = document.createElement("div");
  track.className = "chart__track";

  const bar = document.createElement("div");
  bar.className = `chart__bar ${colorClass}`;
  const width = max > 0 ? Math.round((value / max) * 100) : 0;
  bar.style.width = `${width}%`;

  track.appendChild(bar);

  const valueEl = document.createElement("div");
  valueEl.className = "chart__value";
  valueEl.textContent = String(value);

  row.appendChild(labelEl);
  row.appendChild(track);
  row.appendChild(valueEl);

  return row;
}

function renderEquipmentChart(distribution = {}) {
  equipmentChartEl.innerHTML = "";

  const available = getDistributionValue(distribution, "DISPONIBLE", "AVAILABLE");
  const loaned = getDistributionValue(distribution, "PRESTADO", "LOANED");
  const max = Math.max(available, loaned, 1);

  equipmentChartEl.appendChild(buildChartRow("Disponibles", available, max, "chart__bar--blue"));
  equipmentChartEl.appendChild(buildChartRow("Prestados", loaned, max, "chart__bar--red"));
}

function renderLoanChart(distribution = {}) {
  loanChartEl.innerHTML = "";

  const active = getDistributionValue(distribution, "ACTIVO", "ACTIVE");
  const returned = getDistributionValue(distribution, "DEVUELTO", "RETURNED");
  const overdue = getDistributionValue(distribution, "VENCIDO", "OVERDUE");
  const max = Math.max(active, returned, overdue, 1);

  loanChartEl.appendChild(buildChartRow("Activos", active, max, "chart__bar--blue"));
  loanChartEl.appendChild(buildChartRow("Devueltos", returned, max, "chart__bar--green"));
  loanChartEl.appendChild(buildChartRow("Vencidos", overdue, max, "chart__bar--red"));
}

function renderOverdueUsers(users = []) {
  overdueUsersBody.innerHTML = "";
  emptyState.classList.toggle("empty-state--visible", users.length === 0);

  if (users.length === 0) {
    emptyState.textContent = "No existen usuarios con devoluciones vencidas.";
    return;
  }

  users.forEach((item) => {
    const tr = document.createElement("tr");
    tr.classList.add("row--overdue");

    const equipmentText = item.equipment
      ? `${item.equipment.code || ""}${item.equipment.name ? ` - ${item.equipment.name}` : ""}`
      : "-";

    tr.innerHTML = `
      <td>${item.full_name ?? "-"}</td>
      <td>${item.dni ?? "-"}</td>
      <td>${equipmentText}</td>
      <td>${formatDate(item.due_date)}</td>
      <td>${item.days_overdue ?? 0}</td>
      <td><span class="badge badge--danger">${normalizeLoanKey(item.status || "VENCIDO")}</span></td>
    `;

    overdueUsersBody.appendChild(tr);
  });
}

async function loadDashboard() {
  try {
    emptyState.classList.remove("empty-state--visible");
    emptyState.textContent = "Cargando dashboard...";

    const [summary, charts, overdueUsers] = await Promise.all([
      apiRequest("/dashboard/summary"),
      apiRequest("/dashboard/charts"),
      apiRequest("/dashboard/overdue-users"),
    ]);

    setSummary(summary || {});

    const equipmentDistribution =
      summary?.equipment_status_distribution ||
      charts?.equipment_distribution ||
      {};

    const loanDistribution =
      summary?.loan_status_distribution ||
      charts?.loan_distribution ||
      {};

    renderEquipmentChart({
      DISPONIBLE: getDistributionValue(equipmentDistribution, "DISPONIBLE", "AVAILABLE"),
      PRESTADO: getDistributionValue(equipmentDistribution, "PRESTADO", "LOANED"),
    });

    renderLoanChart({
      ACTIVO: getDistributionValue(loanDistribution, "ACTIVO", "ACTIVE"),
      DEVUELTO: getDistributionValue(loanDistribution, "DEVUELTO", "RETURNED"),
      VENCIDO: getDistributionValue(loanDistribution, "VENCIDO", "OVERDUE"),
    });

    renderOverdueUsers(Array.isArray(overdueUsers) ? overdueUsers : []);
  } catch (error) {
    setSummary({});
    renderEquipmentChart({});
    renderLoanChart({});
    renderOverdueUsers([]);
    emptyState.classList.add("empty-state--visible");
    emptyState.textContent = error.message;
  }
}

document.addEventListener("DOMContentLoaded", loadDashboard);