const API_BASE_URL = window.TECHLOAN_API_URL || "http://127.0.0.1:8000";

const loanForm = document.getElementById("loanForm");
const dniInput = document.getElementById("dni");
const fullNameInput = document.getElementById("fullName");
const emailInput = document.getElementById("email");
const phoneInput = document.getElementById("phone");
const departmentInput = document.getElementById("department");
const equipmentSelect = document.getElementById("equipmentId");
const loanDateInput = document.getElementById("loanDate");
const dueDateInput = document.getElementById("dueDate");
const clearBtn = document.getElementById("clearBtn");
const cancelBtn = document.getElementById("cancelBtn");
const messageBox = document.getElementById("messageBox");
const tableBody = document.getElementById("loanTableBody");
const emptyState = document.getElementById("emptyState");

let loans = [];
let borrowers = [];
let availableEquipment = [];

function setMessage(text, type = "") {
  messageBox.textContent = text || "";
  messageBox.className = `message ${type ? `message--${type}` : ""}`.trim();
}

function clearValidation() {
  [dniInput, fullNameInput, emailInput, phoneInput, departmentInput, equipmentSelect, loanDateInput, dueDateInput].forEach((el) => {
    el.classList.remove("is-invalid");
  });
}

function markInvalid(elements = []) {
  clearValidation();
  elements.forEach((el) => el.classList.add("is-invalid"));
}

function normalizeEquipmentStatus(status) {
  if (status === "AVAILABLE") return "DISPONIBLE";
  if (status === "LOANED") return "PRESTADO";
  return status || "";
}

function normalizeLoanStatus(status) {
  if (status === "ACTIVE") return "ACTIVO";
  if (status === "RETURNED") return "DEVUELTO";
  if (status === "OVERDUE") return "VENCIDO";
  return status || "";
}

function loanStatusClass(status, overdue = false) {
  const normalized = normalizeLoanStatus(status);
  if (overdue || normalized === "VENCIDO") return "badge badge--overdue";
  if (normalized === "ACTIVO") return "badge badge--active";
  if (normalized === "DEVUELTO") return "badge badge--returned";
  return "badge";
}

function loanStatusLabel(status, overdue = false) {
  if (overdue) return "VENCIDO";
  return normalizeLoanStatus(status);
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("es-PE");
}

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function daysBetweenDates(later, earlier) {
  const a = new Date(later);
  const b = new Date(earlier);
  const diff = a.getTime() - b.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
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

function borrowerByDni(dni) {
  return borrowers.find((item) => String(item.dni) === String(dni));
}

function equipmentById(id) {
  return availableEquipment.find((item) => String(item.id) === String(id));
}

function loanLabelForEquipment(loan) {
  const equipment = availableEquipment.find((item) => String(item.id) === String(loan.equipment_id));
  return equipment ? `${equipment.code} - ${equipment.name}` : `Equipo #${loan.equipment_id}`;
}

function borrowerLabelForLoan(loan) {
  const borrower = borrowers.find((item) => String(item.id) === String(loan.borrower_id));
  return borrower ? borrower.full_name : `Solicitante #${loan.borrower_id}`;
}

function isOverdueLoan(loan) {
  if (loan.return_date) return false;
  if (normalizeLoanStatus(loan.status) === "DEVUELTO") return false;
  const dueDate = new Date(loan.due_date);
  if (Number.isNaN(dueDate.getTime())) return false;
  return dueDate < new Date(todayISO());
}

function renderEquipmentOptions() {
  equipmentSelect.innerHTML = "";

  if (availableEquipment.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No hay equipos disponibles";
    equipmentSelect.appendChild(option);
    equipmentSelect.disabled = true;
    return;
  }

  equipmentSelect.disabled = false;
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "Seleccione un equipo";
  equipmentSelect.appendChild(defaultOption);

  availableEquipment.forEach((equipment) => {
    const option = document.createElement("option");
    option.value = equipment.id;
    option.textContent = `${equipment.code} - ${equipment.name}`;
    equipmentSelect.appendChild(option);
  });
}

function renderTable(data) {
  tableBody.innerHTML = "";
  emptyState.classList.toggle("empty-state--visible", data.length === 0);

  if (data.length === 0) {
    emptyState.textContent = "No hay préstamos registrados";
    return;
  }

  data.forEach((loan) => {
    const overdue = isOverdueLoan(loan);
    const tr = document.createElement("tr");
    if (overdue) tr.classList.add("row--overdue");

    tr.innerHTML = `
      <td>${loanLabelForEquipment(loan)}</td>
      <td>${borrowerLabelForLoan(loan)}</td>
      <td>${(borrowers.find((item) => String(item.id) === String(loan.borrower_id)) || {}).dni || "-"}</td>
      <td>${formatDate(loan.loan_date)}</td>
      <td>${formatDate(loan.due_date)}</td>
      <td><span class="${loanStatusClass(loan.status, overdue)}">${loanStatusLabel(loan.status, overdue)}</span></td>
      <td>
        <div class="actions">
          <button class="btn btn--ghost btn--small" data-action="detail" data-id="${loan.id}">Ver detalle</button>
          <button class="btn btn--danger btn--small" data-action="return" data-id="${loan.id}" ${loan.return_date ? "disabled" : ""}>Registrar devolución</button>
        </div>
      </td>
    `;

    tableBody.appendChild(tr);
  });
}

async function loadBorrowers() {
  const data = await apiRequest("/borrowers");
  borrowers = Array.isArray(data) ? data : [];
}

async function loadLoans() {
  const data = await apiRequest("/loans");
  loans = Array.isArray(data) ? data : [];
}

async function loadAvailableEquipment() {
  const data = await apiRequest("/loans/available-equipment");
  availableEquipment = Array.isArray(data) ? data : [];
  renderEquipmentOptions();
}

async function refreshAll() {
  try {
    emptyState.classList.remove("empty-state--visible");
    emptyState.textContent = "Cargando préstamos...";
    await Promise.all([loadBorrowers(), loadLoans(), loadAvailableEquipment()]);
    renderTable(loans);
  } catch (error) {
    loans = [];
    borrowers = [];
    availableEquipment = [];
    renderEquipmentOptions();
    renderTable([]);
    setMessage(error.message, "error");
  }
}

function clearForm() {
  loanForm.reset();
  loanDateInput.value = todayISO();
  dueDateInput.value = todayISO();
  clearValidation();
  setMessage("");
}

async function createBorrowerIfNeeded() {
  const dni = dniInput.value.trim();
  const existing = borrowerByDni(dni);
  if (existing) return existing;

  const payload = {
    dni,
    full_name: fullNameInput.value.trim(),
    email: emailInput.value.trim(),
    phone: phoneInput.value.trim(),
    department: departmentInput.value.trim(),
  };

  const created = await apiRequest("/borrowers", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  borrowers.push(created);
  return created;
}

async function submitLoan(event) {
  event.preventDefault();
  clearValidation();

  const payload = {
    dni: dniInput.value.trim(),
    fullName: fullNameInput.value.trim(),
    email: emailInput.value.trim(),
    phone: phoneInput.value.trim(),
    department: departmentInput.value.trim(),
    equipmentId: equipmentSelect.value,
    loanDate: loanDateInput.value,
    dueDate: dueDateInput.value,
  };

  const invalidFields = [];
  if (!payload.dni) invalidFields.push(dniInput);
  if (!payload.fullName) invalidFields.push(fullNameInput);
  if (!payload.email) invalidFields.push(emailInput);
  if (!payload.phone) invalidFields.push(phoneInput);
  if (!payload.department) invalidFields.push(departmentInput);
  if (!payload.equipmentId) invalidFields.push(equipmentSelect);
  if (!payload.loanDate) invalidFields.push(loanDateInput);
  if (!payload.dueDate) invalidFields.push(dueDateInput);

  if (invalidFields.length > 0) {
    markInvalid(invalidFields);
    setMessage("Complete los campos obligatorios.", "error");
    return;
  }

  if (payload.dueDate <= payload.loanDate) {
    markInvalid([loanDateInput, dueDateInput]);
    setMessage("La fecha límite debe ser posterior a la fecha de préstamo.", "error");
    return;
  }

  try {
    const borrower = await createBorrowerIfNeeded();

    await apiRequest("/loans", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: Number(payload.equipmentId),
        borrower_id: borrower.id,
        loan_date: payload.loanDate,
        due_date: payload.dueDate,
        return_date: null,
        status: "ACTIVO",
      }),
    });

    setMessage("Préstamo registrado correctamente.", "success");
    clearForm();
    await refreshAll();
  } catch (error) {
    setMessage(error.message, "error");
    if (error.status === 409) {
      equipmentSelect.classList.add("is-invalid");
    }
    if (error.status === 422) {
      markInvalid([equipmentSelect]);
    }
  }
}

tableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const { action, id } = button.dataset;
  const loan = loans.find((item) => String(item.id) === String(id));
  if (!loan) return;

  if (action === "detail") {
    const borrower = borrowers.find((item) => String(item.id) === String(loan.borrower_id));
    const equipment = availableEquipment.find((item) => String(item.id) === String(loan.equipment_id));
    window.alert(
      [
        `Préstamo #${loan.id}`,
        `Equipo: ${equipment ? `${equipment.code} - ${equipment.name}` : loan.equipment_id}`,
        `Solicitante: ${borrower ? borrower.full_name : loan.borrower_id}`,
        `DNI: ${borrower ? borrower.dni : "-"}`,
        `Préstamo: ${formatDate(loan.loan_date)}`,
        `Vencimiento: ${formatDate(loan.due_date)}`,
        `Estado: ${normalizeLoanStatus(loan.status)}`,
      ].join("\n")
    );
    return;
  }

  if (action === "return") {
    const confirmed = window.confirm("¿Registrar devolución de este préstamo?");
    if (!confirmed) return;

    try {
      await apiRequest(`/loans/${loan.id}/return`, { method: "POST" });
      setMessage("Devolución registrada correctamente.", "success");
      await refreshAll();
    } catch (error) {
      setMessage(error.message, "error");
    }
  }
});

clearBtn.addEventListener("click", () => {
  clearForm();
});

cancelBtn.addEventListener("click", () => {
  clearForm();
});

loanForm.addEventListener("submit", submitLoan);

document.addEventListener("DOMContentLoaded", async () => {
  loanDateInput.value = todayISO();
  dueDateInput.value = todayISO();
  await refreshAll();
});