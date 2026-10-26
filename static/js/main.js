/**
 * SpendWise - Main Application JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initModal();
  initTypeToggle();
  initDeleteHandlers();
  initBudgetInlineEditing();
  initAlertDismissal();
});

// B.Tech Student Category Definitions
const CATEGORIES = {
  Expense: [
    { name: 'Hostel Fees', icon: '🏠' },
    { name: 'Food', icon: '🍔' },
    { name: 'Fuel', icon: '⛽' },
    { name: 'Travel', icon: '🚆' },
    { name: 'Stationery', icon: '📚' },
    { name: 'Phone Recharge', icon: '📱' },
    { name: 'Tech & Books', icon: '💻' },
    { name: 'Entertainment', icon: '🎬' },
    { name: 'Others', icon: '📦' }
  ],
  Income: [
    { name: 'Allowance', icon: '💵' },
    { name: 'Internship Stipend', icon: '💼' },
    { name: 'Freelance', icon: '💻' },
    { name: 'Scholarship', icon: '🎓' },
    { name: 'Others', icon: '🎁' }
  ]
};

/**
 * Mobile Navigation Menu Toggle
 */
function initMobileNav() {
  const menuBtn = document.getElementById('mobileMenuBtn');
  const navLinks = document.getElementById('navLinks');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }
}

/**
 * Global Transaction Modal Handler (Add & Edit)
 */
function initModal() {
  const backdrop = document.getElementById('transactionModal');
  if (!backdrop) return;

  const closeBtns = backdrop.querySelectorAll('[data-close-modal]');
  const form = document.getElementById('transactionForm');
  const modalTitle = document.getElementById('modalTitle');
  const txIdInput = document.getElementById('txId');
  const txTypeInput = document.getElementById('txType');
  const txAmountInput = document.getElementById('txAmount');
  const txCategorySelect = document.getElementById('txCategory');
  const txDateInput = document.getElementById('txDate');
  const txNoteInput = document.getElementById('txNote');
  const modalError = document.getElementById('modalError');

  // Open modal for Adding
  const openAddBtns = document.querySelectorAll('[data-open-add-modal]');
  openAddBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      resetForm();
      modalTitle.textContent = 'Add Transaction';
      setType('Expense');
      backdrop.classList.add('active');
      txAmountInput.focus();
    });
  });

  // Open modal for Editing
  document.addEventListener('click', async (e) => {
    const editBtn = e.target.closest('[data-edit-tx]');
    if (!editBtn) return;

    e.preventDefault();
    const txId = editBtn.dataset.editTx;
    if (!txId) return;

    try {
      const res = await fetch(`/api/transactions/${txId}`);
      const data = await res.json();
      if (data.success && data.transaction) {
        const tx = data.transaction;
        resetForm();
        modalTitle.textContent = 'Edit Transaction';
        txIdInput.value = tx.id;
        setType(tx.type);
        txAmountInput.value = tx.amount;
        populateCategoryOptions(tx.type, tx.category);
        txDateInput.value = tx.date;
        txNoteInput.value = tx.note || '';
        backdrop.classList.add('active');
        txAmountInput.focus();
      } else {
        showToast(data.error || 'Could not load transaction.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Error loading transaction data.', 'error');
    }
  });

  // Close modal
  closeBtns.forEach(btn => {
    btn.addEventListener('click', closeModal);
  });

  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closeModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && backdrop.classList.contains('active')) {
      closeModal();
    }
  });

  function closeModal() {
    backdrop.classList.remove('active');
    resetForm();
  }

  function resetForm() {
    form.reset();
    txIdInput.value = '';
    modalError.textContent = '';
    modalError.style.display = 'none';
    const today = new Date().toISOString().split('T')[0];
    txDateInput.value = today;
  }

  // Handle Form Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    modalError.style.display = 'none';

    const txId = txIdInput.value.trim();
    const type = txTypeInput.value;
    const amount = parseFloat(txAmountInput.value);
    const category = txCategorySelect.value;
    const date = txDateInput.value;
    const note = txNoteInput.value.trim();

    if (!amount || amount <= 0) {
      showModalError('Please enter a valid amount greater than ₹0.');
      return;
    }
    if (!category) {
      showModalError('Please select a category.');
      return;
    }
    if (!date) {
      showModalError('Please select a date.');
      return;
    }

    const payload = { type, amount, category, date, note };
    const url = txId ? `/api/transactions/${txId}` : '/api/transactions';
    const method = 'POST';

    try {
      const res = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });

      let data = null;
      try {
        data = await res.json();
      } catch (jsonErr) {
        // If server returned non-JSON HTML error
        showModalError(`Server returned status ${res.status}. Please try again.`);
        return;
      }

      if (res.ok && data && data.success) {
        closeModal();
        showToast(data.message || 'Saved successfully!', 'success');
        // Reload page to refresh metrics, charts, and tables
        setTimeout(() => {
          window.location.reload();
        }, 300);
      } else {
        showModalError((data && data.error) || `Error (${res.status}): Failed to save transaction.`);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      showModalError('Connection issue: Could not reach the server. Please try again.');
    }
  });

  function showModalError(msg) {
    modalError.textContent = msg;
    modalError.style.display = 'block';
  }
}

/**
 * Handle Type Switcher (Income / Expense) in Modal
 */
function initTypeToggle() {
  const expenseBtn = document.getElementById('typeExpenseBtn');
  const incomeBtn = document.getElementById('typeIncomeBtn');
  const txTypeInput = document.getElementById('txType');

  if (!expenseBtn || !incomeBtn || !txTypeInput) return;

  expenseBtn.addEventListener('click', () => setType('Expense'));
  incomeBtn.addEventListener('click', () => setType('Income'));
}

function setType(type) {
  const expenseBtn = document.getElementById('typeExpenseBtn');
  const incomeBtn = document.getElementById('typeIncomeBtn');
  const txTypeInput = document.getElementById('txType');

  if (!expenseBtn || !incomeBtn || !txTypeInput) return;

  txTypeInput.value = type;

  if (type === 'Expense') {
    expenseBtn.classList.add('active', 'expense');
    incomeBtn.classList.remove('active', 'income');
  } else {
    incomeBtn.classList.add('active', 'income');
    expenseBtn.classList.remove('active', 'expense');
  }

  populateCategoryOptions(type);
}

function populateCategoryOptions(type, selectedCategory = '') {
  const select = document.getElementById('txCategory');
  if (!select) return;

  const categories = CATEGORIES[type] || [];
  select.innerHTML = '<option value="">Select Category</option>';

  categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat.name;
    opt.textContent = `${cat.icon} ${cat.name}`;
    if (selectedCategory && selectedCategory === cat.name) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });

  if (!selectedCategory && categories.length > 0) {
    select.selectedIndex = 1;
  }
}

/**
 * Transaction Deletion Handlers
 */
function initDeleteHandlers() {
  document.addEventListener('click', async (e) => {
    const delBtn = e.target.closest('[data-delete-tx]');
    if (!delBtn) return;

    e.preventDefault();
    const txId = delBtn.dataset.deleteTx;
    if (!txId) return;

    if (!confirm('Are you sure you want to delete this transaction?')) {
      return;
    }

    try {
      const res = await fetch(`/api/transactions/${txId}/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();

      if (data.success) {
        showToast(data.message || 'Transaction deleted.', 'info');
        const row = document.getElementById(`tx-row-${txId}`);
        if (row) {
          row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          row.style.opacity = '0';
          row.style.transform = 'translateX(20px)';
          setTimeout(() => {
            row.remove();
            // If on dashboard, reload to recalculate balance
            if (window.location.pathname === '/dashboard') {
              window.location.reload();
            }
          }, 300);
        } else {
          setTimeout(() => window.location.reload(), 300);
        }
      } else {
        showToast(data.error || 'Failed to delete transaction.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while deleting transaction.', 'error');
    }
  });
}

/**
 * Budget Page Inline Editing
 */
function initBudgetInlineEditing() {
  // Toggle inline edit form
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-toggle-limit-form]');
    if (!btn) return;

    const cat = btn.dataset.toggleLimitForm;
    const form = document.getElementById(`limit-form-${cat}`);
    if (form) {
      const isHidden = form.style.display === 'none' || !form.style.display;
      form.style.display = isHidden ? 'flex' : 'none';
      if (isHidden) {
        const input = form.querySelector('input[name="limit"]');
        if (input) input.focus();
      }
    }
  });

  // Cancel inline form
  document.addEventListener('click', (e) => {
    const cancelBtn = e.target.closest('[data-cancel-limit]');
    if (!cancelBtn) return;

    const cat = cancelBtn.dataset.cancelLimit;
    const form = document.getElementById(`limit-form-${cat}`);
    if (form) form.style.display = 'none';
  });

  // Submit budget form via AJAX
  const forms = document.querySelectorAll('.budget-inline-form');
  forms.forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const cat = form.dataset.category;
      const month = form.dataset.month;
      const year = form.dataset.year;
      const limitInput = form.querySelector('input[name="limit"]');
      const limitVal = parseFloat(limitInput.value);

      if (isNaN(limitVal) || limitVal < 0) {
        showToast('Please enter a valid non-negative budget limit.', 'error');
        return;
      }

      try {
        const res = await fetch('/api/budgets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category: cat, limit: limitVal, month, year })
        });
        const data = await res.json();

        if (data.success) {
          showToast(data.message, 'success');
          // Reload to cleanly update all metrics and overview
          setTimeout(() => window.location.reload(), 350);
        } else {
          showToast(data.error || 'Failed to update budget.', 'error');
        }
      } catch (err) {
        console.error(err);
        showToast('Error saving budget limit.', 'error');
      }
    });
  });
}

/**
 * Flash Alert Auto-dismissal and Close buttons
 */
function initAlertDismissal() {
  document.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('.alert-close');
    if (closeBtn) {
      const alert = closeBtn.closest('.alert');
      if (alert) alert.remove();
    }
  });
}

/**
 * Simple Toast Notification
 */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.position = 'fixed';
    container.style.top = '1.5rem';
    container.style.right = '1.5rem';
    container.style.zIndex = '9999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '0.5rem';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.boxShadow = '0 8px 24px rgba(0,0,0,0.6)';
  toast.style.minWidth = '260px';
  toast.innerHTML = `
    <span>${message}</span>
    <button class="alert-close" style="margin-left:0.75rem;">&times;</button>
  `;

  container.appendChild(toast);

  toast.querySelector('.alert-close').addEventListener('click', () => toast.remove());

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
