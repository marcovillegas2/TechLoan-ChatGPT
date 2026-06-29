const API_BASE_URL = window.TECHLOAN_API_URL || "http://127.0.0.1:8000";
const equipmentForm = document.getElementById("equipmentForm");
const equipmentIdInput = document.getElementById("equipmentId");
const codeInput = document.getElementById("code");
const nameInput = document.getElementById("name");
const categoryInput = document.getElementById("category");
const descriptionInput = document.getElementById("description");
const statusInput = document.getElementById("status");
const registerBtn = document.getElementById("registerBtn");
const updateBtn = document.getElementById("updateBtn");
const cancelBtn = document.getElementById("cancelBtn");
const messageBox = document.getElementById("messageBox");
const tableBody = document.getElementById("equipmentTableBody");
const emptyState = document.getElementById("emptyState");
const formTitle = document.getElementById("formTitle");

let equipments = [];
let editingId = null;

function setMessage(text, type = "") {
  messageBox.textContent = text || "";
  messageBox.className = `message ${type ? `message--${type}` : ""}`.trim();
}

function clearValidation() {
  [codeInput, nameInput, categoryInput, descriptionInput, statusInput].forEach((el) => {
    el.classList.remove("is-invalid");
  });
}

function markInvalid(elements = []) {
  clearValidation();
  elements.forEach((el) => el.classList.add("is-invalid"));
}

function normalizeStatus(status) {
  if (status === "AVAILABLE") return "DISPONIBLE";
  if (status === "LOANED") return "PRESTADO";
  return status || "";
}

function statusBadgeClass(status) {
  const normalized = normalizeStatus(status);
  if (normalized === "DISPONIBLE") return "badge badge--success";
  if (normalized === "PRESTADO") return "badge badge--danger";
  return "badge";
}

function statusLabel(status) {
  const normalized = normalizeStatus(status);
  return normalized === "DISPONIBLE" ? "Disponible" : "Prestado";
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

function resetForm() {
  equipmentForm.reset();
  equipmentIdInput.value = "";
  editingId = null;
  formTitle.textContent = "Registrar equipo";
  registerBtn.classList.remove("btn--hidden");
  updateBtn.classList.add("btn--hidden");
  clearValidation();
  setMessage("");
  statusInput.value = "DISPONIBLE";
}

function fillForm(equipment) {
  editingId = equipment.id;
  equipmentIdInput.value = equipment.id;
  codeInput.value = equipment.code || "";
  nameInput.value = equipment.name || "";
  categoryInput.value = equipment.category || "";
  descriptionInput.value = equipment.description || "";
  statusInput.value = normalizeStatus(equipment.status) || "DISPONIBLE";
  formTitle.textContent = "Editar equipo";
  registerBtn.classList.add("btn--hidden");
  updateBtn.classList.remove("btn--hidden");
  setMessage("Edición cargada. Actualice los datos y confirme el cambio.", "success");
}

function renderTable(data) {
  tableBody.innerHTML = "";
  emptyState.classList.toggle("empty-state--visible", data.length === 0);

  if (data.length === 0) {
    emptyState.textContent = "No hay equipos registrados";
    return;
  }

  data.forEach((equipment) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${equipment.code ?? ""}</td>
      <td>${equipment.name ?? ""}</td>
      <td>${equipment.category ?? ""}</td>
      <td><span class="${statusBadgeClass(equipment.status)}">${statusLabel(equipment.status)}</span></td>
      <td>
        <div class="actions">
          <button class="btn btn--ghost btn--small" data-action="edit" data-id="${equipment.id}">Editar</button>
          <button class="btn btn--danger btn--small" data-action="delete" data-id="${equipment.id}">Eliminar</button>
        </div>
      </td>
    `;

    tableBody.appendChild(tr);
  });
}

async function loadEquipments() {
  try {
    emptyState.classList.remove("empty-state--visible");
    emptyState.textContent = "Cargando equipos...";
    const data = await apiRequest("/equipment");
    equipments = Array.isArray(data) ? data : [];
    renderTable(equipments);
  } catch (error) {
    equipments = [];
    renderTable([]);
    setMessage(error.message, "error");
  }
}

async function createEquipment(payload) {
  try {
    return await apiRequest("/equipment", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error.status === 422 && payload.status === "DISPONIBLE") {
      return await apiRequest("/equipment", {
        method: "POST",
        body: JSON.stringify({ ...payload, status: "AVAILABLE" }),
      });
    }
    if (error.status === 422 && payload.status === "PRESTADO") {
      return await apiRequest("/equipment", {
        method: "POST",
        body: JSON.stringify({ ...payload, status: "LOANED" }),
      });
    }
    throw error;
  }
}

async function updateEquipment(payload) {
  try {
    return await apiRequest(`/equipment/${editingId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error.status === 422 && payload.status === "DISPONIBLE") {
      return await apiRequest(`/equipment/${editingId}`, {
        method: "PUT",
        body: JSON.stringify({ ...payload, status: "AVAILABLE" }),
      });
    }
    if (error.status === 422 && payload.status === "PRESTADO") {
      return await apiRequest(`/equipment/${editingId}`, {
        method: "PUT",
        body: JSON.stringify({ ...payload, status: "LOANED" }),
      });
    }
    throw error;
  }
}

equipmentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearValidation();

  const payload = {
    code: codeInput.value.trim(),
    name: nameInput.value.trim(),
    category: categoryInput.value.trim(),
    description: descriptionInput.value.trim() || null,
    status: statusInput.value,
  };

  const invalidFields = [];
  if (!payload.code) invalidFields.push(codeInput);
  if (!payload.name) invalidFields.push(nameInput);
  if (!payload.category) invalidFields.push(categoryInput);
  if (!payload.status) invalidFields.push(statusInput);

  if (invalidFields.length > 0) {
    markInvalid(invalidFields);
    setMessage("Complete los campos obligatorios.", "error");
    return;
  }

  try {
    if (editingId) {
      await updateEquipment(payload);
      setMessage("Equipo actualizado correctamente.", "success");
    } else {
      await createEquipment(payload);
      setMessage("Equipo registrado correctamente.", "success");
    }
    resetForm();
    await loadEquipments();
  } catch (error) {
    setMessage(error.message, "error");
    if (error.status === 409) {
      codeInput.classList.add("is-invalid");
    }
  }
});

cancelBtn.addEventListener("click", () => {
  resetForm();
});

tableBody.addEventListener("click", async (event) => {
  const actionButton = event.target.closest("button[data-action]");
  if (!actionButton) return;

  const { action, id } = actionButton.dataset;
  const equipment = equipments.find((item) => String(item.id) === String(id));

  if (action === "edit" && equipment) {
    fillForm(equipment);
    return;
  }

  if (action === "delete" && equipment) {
    const confirmed = window.confirm(`¿Desea eliminar el equipo ${equipment.code}?`);
    if (!confirmed) return;

    try {
      await apiRequest(`/equipment/${equipment.id}`, { method: "DELETE" });
      setMessage("Equipo eliminado correctamente.", "success");
      if (String(editingId) === String(equipment.id)) {
        resetForm();
      }
      await loadEquipments();
    } catch (error) {
      setMessage(error.message, "error");
    }
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  statusInput.value = "DISPONIBLE";
  await loadEquipments();
});