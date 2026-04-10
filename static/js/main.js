/* =====================================================
   Clínica Dental Familiar – Main JavaScript
   ===================================================== */

// ─── CSRF TOKEN ──────────────────────────────────────
const CSRF_TOKEN = window.CSRF_TOKEN || '';

// ─── PATIENT SEARCH AUTOCOMPLETE ─────────────────────
function initPatientSearch(inputId, hiddenId, displayId) {
  const input = document.getElementById(inputId);
  const hidden = document.getElementById(hiddenId);
  const display = document.getElementById(displayId);
  if (!input) return;

  let dropdown = null;
  let debounceTimer = null;

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    const q = this.value.trim();
    if (q.length < 2) { closeDropdown(); return; }
    debounceTimer = setTimeout(() => searchPatients(q), 280);
  });

  function searchPatients(q) {
    fetch(`/api/patients/search?q=${encodeURIComponent(q)}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(r => r.json())
      .then(data => renderDropdown(data))
      .catch(() => {});
  }

  function renderDropdown(results) {
    closeDropdown();
    if (!results.length) return;

    dropdown = document.createElement('div');
    dropdown.className = 'search-results-dropdown';

    results.forEach(p => {
      const item = document.createElement('div');
      item.className = 'search-result-item';
      const dob = p.dob ? ` · ${calcAge(p.dob)} años` : '';
      item.innerHTML = `
        <div class="search-result-name">${p.last_name}, ${p.first_name}</div>
        <div class="search-result-info">${p.phone || ''}${dob} · ID #${p.id}</div>
      `;
      item.addEventListener('mousedown', e => {
        e.preventDefault();
        selectPatient(p);
      });
      dropdown.appendChild(item);
    });

    input.parentElement.style.position = 'relative';
    input.parentElement.appendChild(dropdown);
  }

  function selectPatient(p) {
    if (hidden) hidden.value = p.id;
    if (display) display.value = `${p.last_name}, ${p.first_name}`;
    else input.value = `${p.last_name}, ${p.first_name}`;
    closeDropdown();
  }

  function closeDropdown() {
    if (dropdown) { dropdown.remove(); dropdown = null; }
  }

  document.addEventListener('click', e => {
    if (!input.contains(e.target)) closeDropdown();
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeDropdown();
  });
}

// ─── AGE CALCULATOR ──────────────────────────────────
function calcAge(dob) {
  if (!dob) return '';
  const today = new Date();
  const birth = new Date(dob);
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

// ─── APPOINTMENT STATUS QUICK UPDATE (AJAX) ──────────
function updateApptStatus(aid, newStatus) {
  const form = new FormData();
  form.append('status', newStatus);
  form.append('_csrf_token', CSRF_TOKEN);

  fetch(`/appointments/${aid}/status`, {
    method: 'POST',
    body: form,
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        showToast('Estado actualizado.', 'success');
        const badge = document.querySelector(`[data-appt-badge="${aid}"]`);
        if (badge) {
          badge.textContent = newStatus.replace('_', ' ');
          badge.className = `badge badge-${getStatusColor(newStatus)}`;
        }
        const card = document.querySelector(`[data-appt-card="${aid}"]`);
        if (card) {
          card.className = `appt-card status-${newStatus}`;
        }
      }
    })
    .catch(() => showToast('Error al actualizar.', 'error'));
}

// ─── TASK STATUS TOGGLE (AJAX) ────────────────────────
function toggleTask(tid, status) {
  const form = new FormData();
  form.append('status', status);
  form.append('_csrf_token', CSRF_TOKEN);

  fetch(`/tasks/${tid}/status`, {
    method: 'POST',
    body: form,
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        showToast('Tarea actualizada.', 'success');
        const taskEl = document.querySelector(`[data-task="${tid}"]`);
        if (taskEl && status === 'done') {
          taskEl.style.opacity = '0.4';
          taskEl.style.transition = 'opacity .3s';
          setTimeout(() => taskEl.remove(), 500);
        }
      }
    })
    .catch(() => showToast('Error al actualizar.', 'error'));
}

// ─── STATUS COLOR MAP ─────────────────────────────────
function getStatusColor(status) {
  const map = {
    scheduled: 'blue', confirmed: 'teal', checked_in: 'purple',
    completed: 'green', cancelled: 'gray', no_show: 'red',
    active: 'green', inactive: 'gray', open: 'blue', in_progress: 'amber',
    done: 'green', pending: 'amber', contacted: 'blue', overdue: 'red',
    unpaid: 'red', partial: 'amber', paid: 'green'
  };
  return map[status] || 'gray';
}

// ─── MODAL HELPERS ───────────────────────────────────
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    modal.addEventListener('click', function(e) {
      if (e.target === modal) closeModal(id);
    }, { once: true });
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay').forEach(m => {
      if (m.style.display !== 'none') closeModal(m.id);
    });
  }
});

// ─── TOAST NOTIFICATIONS ─────────────────────────────
function showToast(msg, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      display: flex; flex-direction: column; gap: 8px; max-width: 360px;
    `;
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const colorMap = {
    success: '#d1fae5; color: #065f46; border: 1px solid #6ee7b7',
    error:   '#fee2e2; color: #991b1b; border: 1px solid #fca5a5',
    warning: '#fef3c7; color: #92400e; border: 1px solid #fcd34d',
    info:    '#eff6ff; color: #1e40af; border: 1px solid #bfdbfe'
  };

  toast.style.cssText = `
    padding: 12px 16px; border-radius: 8px; font-size: 13.5px; font-weight: 500;
    background: ${colorMap[type] || colorMap.info};
    box-shadow: 0 10px 15px rgba(0,0,0,.1); animation: slideInRight .25s ease;
    max-width: 360px; font-family: 'Inter', sans-serif;
  `;
  toast.textContent = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'fadeOut .3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ─── CONFIRM DIALOGS ─────────────────────────────────
function confirmAction(msg, callback) {
  if (window.confirm(msg)) callback();
}

function confirmDelete(formEl, msg = '¿Estás seguro que deseas eliminar este registro?') {
  if (confirm(msg)) formEl.submit();
}

// ─── FORM VALIDATION ─────────────────────────────────
function validateRequired(formEl) {
  let valid = true;
  formEl.querySelectorAll('[required]').forEach(field => {
    if (!field.value.trim()) {
      field.style.borderColor = '#dc2626';
      valid = false;
      field.addEventListener('input', () => { field.style.borderColor = ''; }, { once: true });
    }
  });
  if (!valid) showToast('Por favor completa todos los campos requeridos.', 'error');
  return valid;
}

// ─── AUTO DISMISS FLASH MESSAGES ────────────────────
function initFlashDismiss() {
  document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
      flash.style.transition = 'opacity .4s, transform .4s';
      flash.style.opacity = '0';
      flash.style.transform = 'translateY(-8px)';
      setTimeout(() => flash.remove(), 400);
    }, 4000);
  });

  document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', function() {
      const flash = this.closest('.flash');
      flash.style.transition = 'opacity .2s';
      flash.style.opacity = '0';
      setTimeout(() => flash.remove(), 200);
    });
  });
}

// ─── ACTIVE NAV HIGHLIGHTING ─────────────────────────
function initActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (href === '/' && path === '/') {
      link.classList.add('active');
    } else if (href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    }
  });
}

// ─── DATE FORMATTING ─────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('es-PR', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateTime(dtStr) {
  if (!dtStr) return '';
  const d = new Date(dtStr.replace(' ', 'T'));
  return d.toLocaleDateString('es-PR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

// ─── TABS ────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab-link').forEach(tab => {
    tab.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('data-tab');
      if (!targetId) return;

      const container = this.closest('.tabs-wrapper');
      if (container) {
        container.querySelectorAll('.tab-link').forEach(t => t.classList.remove('active'));
      }
      this.classList.add('active');

      const tabContents = document.querySelectorAll('.tab-content');
      tabContents.forEach(c => c.classList.remove('active'));

      const target = document.getElementById(targetId);
      if (target) target.classList.add('active');

      window.history.replaceState(null, null, '#' + targetId);
    });
  });

  const hash = window.location.hash.slice(1);
  if (hash) {
    const tab = document.querySelector(`[data-tab="${hash}"]`);
    if (tab) tab.click();
  } else {
    const firstTab = document.querySelector('.tab-link');
    if (firstTab && !document.querySelector('.tab-link.active')) firstTab.click();
  }
}

// ─── EXPAND/COLLAPSE SECTIONS ────────────────────────
function initExpanders() {
  document.querySelectorAll('.expand-toggle').forEach(toggle => {
    toggle.addEventListener('click', function() {
      const targetId = this.getAttribute('data-expand');
      const content = document.getElementById(targetId);
      if (!content) return;
      content.classList.toggle('open');
      const icon = this.querySelector('.expand-icon');
      if (icon) icon.textContent = content.classList.contains('open') ? '▲' : '▼';
    });
  });
}

// ─── CANCELLATION REASON TOGGLE ──────────────────────
function initCancelReasonToggle() {
  const statusSelect = document.getElementById('status-select');
  const cancelRow = document.getElementById('cancel-reason-row');
  if (!statusSelect || !cancelRow) return;

  function toggleCancel() {
    cancelRow.style.display = statusSelect.value === 'cancelled' ? 'block' : 'none';
  }
  statusSelect.addEventListener('change', toggleCancel);
  toggleCancel();
}

// ─── TREATMENT PLAN ITEMS (dynamic) ──────────────────
function addTreatmentItem() {
  const container = document.getElementById('treatment-items-container');
  if (!container) return;
  const row = document.createElement('div');
  row.className = 'treatment-row form-row mb-2';
  row.innerHTML = `
    <div class="form-group mb-0">
      <input type="text" name="item_description" class="form-control" placeholder="Descripción del tratamiento" required>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <input type="text" name="item_tooth" class="form-control" placeholder="Diente (ej: #14)">
      <div style="display:flex;gap:6px;align-items:center;">
        <input type="number" name="item_cost" class="form-control" placeholder="Costo $" min="0" step="0.01">
        <button type="button" onclick="this.closest('.treatment-row').remove()" class="btn btn-ghost btn-icon btn-sm" title="Eliminar" style="flex-shrink:0;">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>
  `;
  container.appendChild(row);
}

// ─── PHONE FORMATTER ─────────────────────────────────
function initPhoneFormat() {
  document.querySelectorAll('input[type="tel"], input[name*="phone"]').forEach(input => {
    input.addEventListener('input', function() {
      let v = this.value.replace(/\D/g, '');
      if (v.length >= 10) {
        v = v.slice(0, 10);
        this.value = `${v.slice(0,3)}-${v.slice(3,6)}-${v.slice(6)}`;
      }
    });
  });
}

// ─── STATUS COLOR BADGES (dynamic) ───────────────────
function applyStatusColors() {
  document.querySelectorAll('[data-status-badge]').forEach(el => {
    const status = el.getAttribute('data-status-badge');
    const color = getStatusColor(status);
    el.className = `badge badge-${color}`;
  });
}

// ─── SEARCH FILTER (client-side table filter) ────────
function initTableFilter(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('input', function() {
    const q = this.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(q) ? '' : 'none';
    });
  });
}

// ─── PRINT ──────────────────────────────────────────
function printSection(id) {
  const content = document.getElementById(id);
  if (!content) return;
  const original = document.body.innerHTML;
  document.body.innerHTML = content.innerHTML;
  window.print();
  document.body.innerHTML = original;
  location.reload();
}

// ─── COPY TO CLIPBOARD ───────────────────────────────
function copyText(text) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('Copiado al portapapeles.', 'success'))
    .catch(() => showToast('No se pudo copiar.', 'error'));
}

// ─── INITIALIZE ALL ──────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  initFlashDismiss();
  initActiveNav();
  initTabs();
  initExpanders();
  initCancelReasonToggle();
  initPhoneFormat();
  applyStatusColors();

  initPatientSearch('patient-search', 'patient_id', 'patient-search');

  document.querySelectorAll('.confirm-delete').forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const msg = this.dataset.confirm || '¿Eliminar este registro?';
      if (confirm(msg)) this.submit();
    });
  });

  document.querySelectorAll('.task-done-check').forEach(cb => {
    cb.addEventListener('change', function() {
      const tid = this.dataset.tid;
      if (this.checked) toggleTask(tid, 'done');
    });
  });
});

// ─── ANIMATIONS ──────────────────────────────────────
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
  }
  @keyframes fadeOut {
    to { opacity: 0; transform: translateY(8px); }
  }
`;
document.head.appendChild(style);
