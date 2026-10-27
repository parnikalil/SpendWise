/**
 * SpendWise: Centralized Store & Reactive UI Engine
 * Solves serverless drift by using a unified, client-synced single source of truth.
 */

// Category Definitions & Student Icons
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

const CATEGORY_ICON_MAP = {};
CATEGORIES.Expense.forEach(c => CATEGORY_ICON_MAP[c.name] = c.icon);
CATEGORIES.Income.forEach(c => CATEGORY_ICON_MAP[c.name] = c.icon);

/**
 * SpendWiseStore: Unified Local + Remote Storage
 */
const SpendWiseStore = {
  user: null,
  storageKey: null,
  data: {
    transactions: [],
    budgets: {}
  },

  init() {
    const initData = window.__INITIAL_DATA__ || {};
    this.user = initData.user || null;

    if (!this.user || !this.user.email) {
      return; // Guest on login page
    }

    this.storageKey = 'spendwise_user_data_' + this.user.email.toLowerCase().trim();

    // Check localStorage
    const saved = localStorage.getItem(this.storageKey);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && Array.isArray(parsed.transactions)) {
          this.data = parsed;
        }
      } catch (e) {
        console.warn('Could not parse local store:', e);
      }
    }

    // If local store is empty or has fewer records than server preseed, initialize from server
    if (!this.data.transactions || this.data.transactions.length === 0) {
      if (initData.transactions && initData.transactions.length > 0) {
        this.data.transactions = initData.transactions;
      }
      if (initData.budgets && Object.keys(initData.budgets).length > 0) {
        this.data.budgets = initData.budgets;
      }
      this.persist();
    }

    // Asynchronous background sync with server
    this.syncWithServer();
  },

  persist() {
    if (!this.storageKey) return;
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.data));
    } catch (e) {
      console.warn('Storage quota exceeded:', e);
    }
  },

  notify() {
    this.persist();
    window.dispatchEvent(new CustomEvent('spendwise:updated'));
  },

  getTransactions() {
    return (this.data.transactions || []).slice().sort((a, b) => {
      if (a.date !== b.date) return b.date.localeCompare(a.date);
      return (b.id || 0) - (a.id || 0);
    });
  },

  getTransaction(id) {
    return (this.data.transactions || []).find(t => String(t.id) === String(id));
  },

  getBudgets() {
    return Object.assign({}, this.data.budgets || {});
  },

  setBudget(category, limit) {
    if (!this.data.budgets) this.data.budgets = {};
    this.data.budgets[category] = parseFloat(limit);
    this.notify();

    // Background sync
    fetch('/api/budgets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, limit: parseFloat(limit) })
    }).catch(() => {});
  },

  async addTransaction(tx) {
    const newTx = {
      id: tx.id || Date.now(),
      type: tx.type,
      amount: parseFloat(tx.amount),
      category: tx.category,
      date: tx.date,
      note: tx.note || ''
    };

    if (!this.data.transactions) this.data.transactions = [];
    this.data.transactions.unshift(newTx);
    this.notify();

    // Background sync to server API
    try {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTx)
      });
      const resData = await res.json();
      if (resData.success && resData.transaction && resData.transaction.id) {
        newTx.id = resData.transaction.id;
        this.persist();
      }
    } catch (e) {
      console.warn('Offline / background sync pending:', e);
    }

    return newTx;
  },

  async updateTransaction(id, updated) {
    const idx = (this.data.transactions || []).findIndex(t => String(t.id) === String(id));
    if (idx !== -1) {
      this.data.transactions[idx] = Object.assign({}, this.data.transactions[idx], {
        type: updated.type,
        amount: parseFloat(updated.amount),
        category: updated.category,
        date: updated.date,
        note: updated.note || ''
      });
      this.notify();

      fetch(`/api/transactions/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.data.transactions[idx])
      }).catch(() => {});
    }
  },

  async deleteTransaction(id) {
    this.data.transactions = (this.data.transactions || []).filter(t => String(t.id) !== String(id));
    this.notify();

    fetch(`/api/transactions/${id}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(() => {});
  },

  syncWithServer() {
    if (!this.user) return;
    fetch('/api/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transactions: this.data.transactions,
        budgets: this.data.budgets
      })
    }).then(r => r.json()).then(res => {
      if (res && res.success) {
        // Merge any server-side entries if local was empty
        if ((!this.data.transactions || this.data.transactions.length === 0) && res.transactions) {
          this.data.transactions = res.transactions;
          this.notify();
        }
      }
    }).catch(() => {});
  }
};

/**
 * Currency and Date Formatters
 */
function formatCurrency(val) {
  const num = parseFloat(val) || 0;
  return '₹' + num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const parts = String(dateStr).split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0]);
      const monthIdx = parseInt(parts[1]) - 1;
      const day = parseInt(parts[2]);
      const d = new Date(year, monthIdx, day);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${String(day).padStart(2, '0')} ${months[monthIdx]} ${year}`;
    }
  } catch (e) {}
  return dateStr;
}

function getCurrentMonthKey() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Reactive Page Renderers
 */
function renderDashboard() {
  const incEl = document.getElementById('summaryIncome');
  const expEl = document.getElementById('summaryExpense');
  const balEl = document.getElementById('summaryBalance');
  if (!incEl || !expEl || !balEl) return;

  const currentMonth = getCurrentMonthKey();
  const txs = SpendWiseStore.getTransactions();

  // Filter current month
  let totalIncome = 0;
  let totalExpense = 0;

  txs.forEach(t => {
    if (String(t.date).startsWith(currentMonth)) {
      if (t.type === 'Income') totalIncome += parseFloat(t.amount || 0);
      if (t.type === 'Expense') totalExpense += parseFloat(t.amount || 0);
    }
  });

  const netBalance = totalIncome - totalExpense;

  incEl.textContent = formatCurrency(totalIncome);
  expEl.textContent = formatCurrency(totalExpense);
  balEl.textContent = formatCurrency(netBalance);
  balEl.style.color = netBalance >= 0 ? '#38BDF8' : 'var(--color-red)';

  const balSub = document.getElementById('summaryBalanceSubtext');
  if (balSub) {
    if (netBalance >= 0) {
      const pct = totalIncome > 0 ? ((netBalance / totalIncome) * 100).toFixed(1) : 0;
      balSub.textContent = `Savings rate: ${pct}%`;
    } else {
      balSub.textContent = 'Deficit: Spent more than income';
    }
  }

  // Update Recent Transactions Table
  const tbody = document.getElementById('recentTxTableBody');
  const wrapper = document.getElementById('recentTableWrapper');
  const empty = document.getElementById('recentEmptyState');

  if (tbody) {
    const recent = txs.slice(0, 5);
    if (recent.length > 0) {
      if (wrapper) wrapper.style.display = 'block';
      if (empty) empty.style.display = 'none';

      tbody.innerHTML = recent.map(t => `
        <tr id="tx-row-${t.id}">
          <td style="white-space: nowrap; font-size: 0.88rem; color: var(--text-muted);">${formatDate(t.date)}</td>
          <td>
            <span class="badge-category">
              <span>${CATEGORY_ICON_MAP[t.category] || '📦'}</span>
              <span>${t.category}</span>
            </span>
          </td>
          <td style="color: var(--text-secondary); max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${t.note || '-'}
          </td>
          <td style="text-align: right;">
            <span class="${t.type === 'Income' ? 'amount-income' : 'amount-expense'}">
              ${t.type === 'Income' ? '+' : '-'}${formatCurrency(t.amount)}
            </span>
          </td>
          <td style="text-align: center;">
            <div class="action-buttons" style="justify-content: center;">
              <button class="btn-icon" data-edit-tx="${t.id}" title="Edit transaction" aria-label="Edit"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg></button>
              <button class="btn-icon delete" data-delete-tx="${t.id}" title="Delete transaction" aria-label="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
            </div>
          </td>
        </tr>
      `).join('');
    } else {
      if (wrapper) wrapper.style.display = 'none';
      if (empty) empty.style.display = 'block';
      tbody.innerHTML = '';
    }
  }

  // Update Charts via global charts renderer
  if (window.renderDashboardChartsFromStore) {
    window.renderDashboardChartsFromStore(txs, currentMonth);
  }
}

function renderTransactionsPage() {
  const tbody = document.getElementById('transactionsTableBody');
  const wrapper = document.getElementById('transactionsTableWrapper');
  const empty = document.getElementById('transactionsEmptyState');
  if (!tbody) return;

  const monthFilter = document.getElementById('filterMonth')?.value || '';
  const catFilter = document.getElementById('filterCategory')?.value || '';
  const typeFilter = document.getElementById('filterType')?.value || '';

  let txs = SpendWiseStore.getTransactions();

  if (monthFilter) txs = txs.filter(t => String(t.date).startsWith(monthFilter));
  if (catFilter) txs = txs.filter(t => t.category === catFilter);
  if (typeFilter) txs = txs.filter(t => t.type === typeFilter);

  if (txs.length > 0) {
    if (wrapper) wrapper.style.display = 'block';
    if (empty) empty.style.display = 'none';

    tbody.innerHTML = txs.map(t => `
      <tr id="tx-row-${t.id}">
        <td style="white-space: nowrap; font-size: 0.88rem; color: var(--text-muted);">${formatDate(t.date)}</td>
        <td>
          <span class="badge-category">
            <span>${CATEGORY_ICON_MAP[t.category] || '📦'}</span>
            <span>${t.category}</span>
          </span>
        </td>
        <td style="color: var(--text-secondary); max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          ${t.note || '-'}
        </td>
        <td style="text-align: right;">
          <span class="${t.type === 'Income' ? 'amount-income' : 'amount-expense'}">
            ${t.type === 'Income' ? '+' : '-'}${formatCurrency(t.amount)}
          </span>
        </td>
        <td style="text-align: center;">
          <div class="action-buttons" style="justify-content: center;">
            <button class="btn-icon" data-edit-tx="${t.id}" title="Edit transaction" aria-label="Edit"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg></button>
            <button class="btn-icon delete" data-delete-tx="${t.id}" title="Delete transaction" aria-label="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
          </div>
        </td>
      </tr>
    `).join('');
  } else {
    if (wrapper) wrapper.style.display = 'none';
    if (empty) empty.style.display = 'block';
    tbody.innerHTML = '';
  }
}

function renderBudgetsPage() {
  const monthSelector = document.getElementById('budgetMonthSelector');
  if (!monthSelector) return;

  const selectedMonth = monthSelector.value || getCurrentMonthKey();
  const txs = SpendWiseStore.getTransactions();
  const budgets = SpendWiseStore.getBudgets();

  // Compute spent per category for selected month
  const spentMap = {};
  let totalLimit = 0;
  let totalSpent = 0;

  txs.forEach(t => {
    if (t.type === 'Expense' && String(t.date).startsWith(selectedMonth)) {
      spentMap[t.category] = (spentMap[t.category] || 0) + parseFloat(t.amount || 0);
    }
  });

  const cards = document.querySelectorAll('.budget-card[data-category]');
  cards.forEach(card => {
    const cat = card.dataset.category;
    const limit = budgets[cat] || 0;
    const spent = spentMap[cat] || 0;
    totalLimit += limit;
    totalSpent += spent;

    const remaining = limit - spent;
    const pct = limit > 0 ? Math.round((spent / limit) * 1000) / 10 : 0;
    const isExceeded85 = pct > 85.0;

    const limitLabel = card.querySelector('.budget-limit-label');
    if (limitLabel) limitLabel.textContent = limit > 0 ? `Limit: ${formatCurrency(limit)}` : 'No limit set yet';

    const spentVal = card.querySelector('.budget-spent-val');
    if (spentVal) {
      spentVal.textContent = formatCurrency(spent);
      spentVal.style.color = isExceeded85 ? 'var(--color-red)' : 'var(--text-primary)';
    }

    const remVal = card.querySelector('.budget-remaining-val');
    if (remVal) {
      remVal.textContent = limit > 0 ? formatCurrency(remaining) : '-';
      remVal.style.color = remaining >= 0 ? 'var(--color-green)' : 'var(--color-red)';
    }

    const barFill = card.querySelector('.progress-bar-fill');
    if (barFill) {
      barFill.style.width = Math.min(pct, 100) + '%';
      barFill.className = 'progress-bar-fill ' + (isExceeded85 ? 'progress-red' : 'progress-orange');
    }

    const pctLabel = card.querySelector('.budget-pct-label');
    if (pctLabel) {
      pctLabel.textContent = pct + '%';
      pctLabel.style.color = isExceeded85 ? 'var(--color-red)' : 'var(--accent-orange)';
    }

    const statusLabel = card.querySelector('.budget-status-label');
    if (statusLabel) {
      statusLabel.textContent = isExceeded85 ? 'Over 85% limit' : 'Under limit';
      statusLabel.style.color = isExceeded85 ? 'var(--color-red)' : 'var(--text-muted)';
    }
  });

  const totalLimitEl = document.getElementById('totalBudgetLimitDisplay');
  const totalSpentEl = document.getElementById('totalBudgetSpentDisplay');
  const totalPctEl = document.getElementById('totalBudgetPctDisplay');
  const totalStatusEl = document.getElementById('totalBudgetStatusText');

  if (totalLimitEl) totalLimitEl.textContent = formatCurrency(totalLimit);
  if (totalSpentEl) totalSpentEl.textContent = formatCurrency(totalSpent);
  if (totalPctEl) {
    const overallPct = totalLimit > 0 ? ((totalSpent / totalLimit) * 100).toFixed(1) : 0;
    totalPctEl.textContent = overallPct + '%';
    totalPctEl.style.color = overallPct > 85 ? 'var(--color-red)' : 'var(--accent-orange)';
    if (totalStatusEl) {
      totalStatusEl.textContent = overallPct > 85 ? 'Warning: High budget utilization' : 'Spending remains within limits';
    }
  }
}

function renderHistoryPage() {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  const txs = SpendWiseStore.getTransactions();
  const now = new Date();
  const curY = now.getFullYear();
  const curM = now.getMonth() + 1;

  const monthsKeys = [];
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  for (let i = 0; i < 6; i++) {
    let m = curM - i;
    let y = curY;
    while (m <= 0) {
      m += 12;
      y -= 1;
    }
    monthsKeys.push({
      key: `${y}-${String(m).padStart(2, '0')}`,
      label: `${monthNames[m - 1]} ${y}`
    });
  }

  let totalIncAll = 0;
  let totalExpAll = 0;

  const rowsHtml = monthsKeys.map(item => {
    let inc = 0;
    let exp = 0;
    txs.forEach(t => {
      if (String(t.date).startsWith(item.key)) {
        if (t.type === 'Income') inc += parseFloat(t.amount || 0);
        if (t.type === 'Expense') exp += parseFloat(t.amount || 0);
      }
    });

    const savings = inc - exp;
    totalIncAll += inc;
    totalExpAll += exp;
    const isPositive = savings >= 0;

    return `
      <tr>
        <td style="font-weight: 600; color: var(--text-primary);">${item.label}</td>
        <td style="text-align: right; color: var(--color-green); font-weight: 600;">${formatCurrency(inc)}</td>
        <td style="text-align: right; color: var(--text-secondary); font-weight: 500;">${formatCurrency(exp)}</td>
        <td style="text-align: right; font-weight: 700; font-size: 1rem;">
          <span class="${isPositive ? 'amount-income' : 'amount-expense'}">
            ${isPositive ? '+' : '-'}${formatCurrency(Math.abs(savings))}
          </span>
        </td>
        <td style="text-align: center;">
          <span style="display: inline-flex; align-items: center; gap: 0.35rem; background-color: ${isPositive ? 'var(--color-green-bg)' : 'var(--color-red-bg)'}; color: ${isPositive ? 'var(--color-green)' : 'var(--color-red)'}; padding: 0.25rem 0.65rem; border-radius: var(--radius-sm); font-size: 0.78rem; font-weight: 600; border: 1px solid ${isPositive ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'};">
            <span>●</span> ${isPositive ? 'Surplus' : 'Deficit'}
          </span>
        </td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = rowsHtml;

  const incAllEl = document.getElementById('histIncomeAll');
  const expAllEl = document.getElementById('histExpenseAll');
  const savAllEl = document.getElementById('histSavingsAll');
  const savSubEl = document.getElementById('histSavingsSubtext');

  if (incAllEl) incAllEl.textContent = formatCurrency(totalIncAll);
  if (expAllEl) expAllEl.textContent = formatCurrency(totalExpAll);
  if (savAllEl) {
    const totalSavings = totalIncAll - totalExpAll;
    savAllEl.textContent = (totalSavings >= 0 ? '+' : '') + formatCurrency(totalSavings);
    savAllEl.style.color = totalSavings >= 0 ? 'var(--color-green)' : 'var(--color-red)';
    if (savSubEl) {
      savSubEl.textContent = totalSavings >= 0 ? 'Positive net wealth accumulation' : 'Net cash outflow deficit';
    }
  }
}

function refreshCurrentView() {
  renderDashboard();
  renderTransactionsPage();
  renderBudgetsPage();
  renderHistoryPage();
}

/**
 * Global App Initialization
 */
document.addEventListener('DOMContentLoaded', () => {
  SpendWiseStore.init();

  initMobileNav();
  initModal();
  initTypeToggle();
  initDeleteHandlers();
  initBudgetInlineEditing();
  initFilterListeners();
  initAlertDismissal();

  // Initial render
  refreshCurrentView();

  // React to store updates
  window.addEventListener('spendwise:updated', refreshCurrentView);
});

function initFilterListeners() {
  const m = document.getElementById('filterMonth');
  const c = document.getElementById('filterCategory');
  const t = document.getElementById('filterType');
  const clear = document.getElementById('clearFiltersBtn');
  const bMonth = document.getElementById('budgetMonthSelector');

  if (m) m.addEventListener('change', renderTransactionsPage);
  if (c) c.addEventListener('change', renderTransactionsPage);
  if (t) t.addEventListener('change', renderTransactionsPage);

  if (clear) {
    clear.addEventListener('click', () => {
      if (m) m.value = '';
      if (c) c.value = '';
      if (t) t.value = '';
      renderTransactionsPage();
    });
  }

  if (bMonth) {
    bMonth.addEventListener('change', renderBudgetsPage);
  }
}

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
 * Add / Edit Modal Manager
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
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-open-add-modal]');
    if (!btn) return;
    e.preventDefault();
    resetForm();
    modalTitle.textContent = 'Add Expense / Income';
    setType('Expense');
    backdrop.classList.add('active');
    setTimeout(() => txAmountInput.focus(), 50);
  });

  // Open modal for Editing
  document.addEventListener('click', (e) => {
    const editBtn = e.target.closest('[data-edit-tx]');
    if (!editBtn) return;
    e.preventDefault();
    const txId = editBtn.dataset.editTx;
    if (!txId) return;

    const tx = SpendWiseStore.getTransaction(txId);
    if (tx) {
      resetForm();
      modalTitle.textContent = 'Edit Transaction';
      txIdInput.value = tx.id;
      setType(tx.type);
      txAmountInput.value = tx.amount;
      populateCategoryOptions(tx.type, tx.category);
      txDateInput.value = tx.date;
      txNoteInput.value = tx.note || '';
      backdrop.classList.add('active');
      setTimeout(() => txAmountInput.focus(), 50);
    }
  });

  // Close modal
  closeBtns.forEach(btn => btn.addEventListener('click', closeModal));
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && backdrop.classList.contains('active')) closeModal();
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
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    txDateInput.value = `${yyyy}-${mm}-${dd}`;
  }

  // Handle Form Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    modalError.style.display = 'none';

    const txId = txIdInput.value.trim();
    const type = txTypeInput.value;
    const amount = parseFloat(txAmountInput.value);
    const category = txCategorySelect.value;
    let rawDate = txDateInput.value.trim();
    const note = txNoteInput.value.trim();

    if (!amount || amount <= 0) {
      showModalError('Please enter a valid amount greater than ₹0.');
      return;
    }
    if (!category) {
      showModalError('Please select a category.');
      return;
    }
    if (!rawDate) {
      showModalError('Please select a date.');
      return;
    }

    // Normalize date format if user entered DD-MM-YYYY
    if (/^\d{2}-\d{2}-\d{4}$/.test(rawDate)) {
      const p = rawDate.split('-');
      rawDate = `${p[2]}-${p[1]}-${p[0]}`;
    }

    const payload = {
      type,
      amount,
      category,
      date: rawDate,
      note
    };

    if (txId) {
      await SpendWiseStore.updateTransaction(txId, payload);
      showToast('Transaction updated successfully!', 'success');
    } else {
      await SpendWiseStore.addTransaction(payload);
      showToast(`${type} added successfully!`, 'success');
    }

    closeModal();
    refreshCurrentView();
  });

  function showModalError(msg) {
    modalError.textContent = msg;
    modalError.style.display = 'block';
  }
}

/**
 * Type Switcher: Income / Expense
 */
function initTypeToggle() {
  const expenseBtn = document.getElementById('typeExpenseBtn');
  const incomeBtn = document.getElementById('typeIncomeBtn');
  if (!expenseBtn || !incomeBtn) return;

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
 * Delete Handlers
 */
function initDeleteHandlers() {
  document.addEventListener('click', async (e) => {
    const delBtn = e.target.closest('[data-delete-tx]');
    if (!delBtn) return;
    e.preventDefault();
    const txId = delBtn.dataset.deleteTx;
    if (!txId) return;

    if (!confirm('Are you sure you want to delete this transaction?')) return;

    await SpendWiseStore.deleteTransaction(txId);
    showToast('Transaction deleted successfully.', 'info');
    refreshCurrentView();
  });
}

/**
 * Inline Budget Limit Editing
 */
function initBudgetInlineEditing() {
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

  document.addEventListener('click', (e) => {
    const cancelBtn = e.target.closest('[data-cancel-limit]');
    if (!cancelBtn) return;
    const cat = cancelBtn.dataset.cancelLimit;
    const form = document.getElementById(`limit-form-${cat}`);
    if (form) form.style.display = 'none';
  });

  const forms = document.querySelectorAll('.budget-inline-form');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const cat = form.dataset.category;
      const limitInput = form.querySelector('input[name="limit"]');
      const limitVal = parseFloat(limitInput.value);

      if (isNaN(limitVal) || limitVal < 0) {
        showToast('Please enter a valid positive budget limit.', 'error');
        return;
      }

      SpendWiseStore.setBudget(cat, limitVal);
      form.style.display = 'none';
      showToast(`Budget for ${cat} updated to ${formatCurrency(limitVal)}`, 'success');
      renderBudgetsPage();
    });
  });
}

function initAlertDismissal() {
  document.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('.alert-close');
    if (closeBtn) {
      const alert = closeBtn.closest('.alert');
      if (alert) alert.remove();
    }
  });
}

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
  }, 3500);
}
