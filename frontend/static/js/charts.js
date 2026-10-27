/**
 * SpendWise: Reactive Chart Engine for Dashboard
 * Synchronized with the centralized transactions store.
 */

let pieChartInstance = null;
let barChartInstance = null;

const ORANGE_SHADES = [
  '#F97316',
  '#FB923C',
  '#FDBA74',
  '#FED7AA',
  '#EA580C',
  '#C2410C',
  '#9A3412',
  '#FF7A00',
  '#D97706',
  '#F59E0B'
];

window.renderDashboardChartsFromStore = function(transactions, currentMonthKey) {
  if (typeof Chart === 'undefined') {
    setTimeout(function() {
      window.renderDashboardChartsFromStore(transactions, currentMonthKey);
    }, 60);
    return;
  }

  const pieContainer = document.getElementById('pieChartContainer');
  const barContainer = document.getElementById('barChartContainer');
  if (!pieContainer && !barContainer) return;

  if (!transactions && typeof SpendWiseStore !== 'undefined') {
    transactions = SpendWiseStore.getTransactions();
  }
  transactions = transactions || [];

  if (!currentMonthKey) {
    const now = new Date();
    currentMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }

  renderExpenseDoughnut(transactions, currentMonthKey);
  renderIncomeExpenseBars(transactions);
};

function renderExpenseDoughnut(transactions, currentMonthKey) {
  const container = document.getElementById('pieChartContainer');
  if (!container) return;

  const categoryTotals = {};
  let totalExpenseThisMonth = 0;

  transactions.forEach(function(t) {
    if (t.type === 'Expense' && String(t.date).startsWith(currentMonthKey)) {
      const amt = parseFloat(t.amount || 0);
      categoryTotals[t.category] = (categoryTotals[t.category] || 0) + amt;
      totalExpenseThisMonth += amt;
    }
  });

  const categories = Object.keys(categoryTotals).sort(function(a, b) {
    return categoryTotals[b] - categoryTotals[a];
  });
  const amounts = categories.map(function(c) {
    return categoryTotals[c];
  });

  if (amounts.length === 0 || totalExpenseThisMonth === 0) {
    if (pieChartInstance) {
      pieChartInstance.destroy();
      pieChartInstance = null;
    }
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:#9CA3AF; gap:0.5rem;">
        <span style="font-size:2rem;">🍩</span>
        <p style="font-size:0.9rem;">No expenses recorded for this month yet.</p>
      </div>
    `;
    return;
  }

  let currentCanvas = document.getElementById('expensePieChart');
  if (!currentCanvas) {
    container.innerHTML = '<canvas id="expensePieChart"></canvas>';
    currentCanvas = document.getElementById('expensePieChart');
  }

  if (pieChartInstance) {
    pieChartInstance.destroy();
    pieChartInstance = null;
  }

  const ctx = currentCanvas.getContext('2d');
  pieChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: categories,
      datasets: [{
        data: amounts,
        backgroundColor: ORANGE_SHADES.slice(0, categories.length),
        borderColor: '#1A1A1A',
        borderWidth: 2,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#E5E5E5',
            font: { family: 'Inter', size: 12, weight: 500 },
            padding: 14,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: '#222222',
          titleColor: '#FFFFFF',
          bodyColor: '#FED7AA',
          borderColor: '#2A2A2A',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          titleFont: { family: 'Inter', size: 13, weight: 600 },
          bodyFont: { family: 'Inter', size: 12 },
          callbacks: {
            label: function(context) {
              const val = context.parsed || 0;
              const total = context.dataset.data.reduce(function(a, b) { return a + b; }, 0);
              const percentage = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ₹${val.toLocaleString('en-IN')} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

function renderIncomeExpenseBars(transactions) {
  const container = document.getElementById('barChartContainer');
  if (!container) return;

  let currentCanvas = document.getElementById('incomeExpenseBarChart');
  if (!currentCanvas) {
    container.innerHTML = '<canvas id="incomeExpenseBarChart"></canvas>';
    currentCanvas = document.getElementById('incomeExpenseBarChart');
  }

  const now = new Date();
  const curY = now.getFullYear();
  const curM = now.getMonth() + 1;

  const months = [];
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  for (let i = 5; i >= 0; i--) {
    let m = curM - i;
    let y = curY;
    while (m <= 0) {
      m += 12;
      y -= 1;
    }
    months.push({
      key: `${y}-${String(m).padStart(2, '0')}`,
      label: `${monthNames[m - 1]} ${y}`
    });
  }

  const incomeData = [];
  const expenseData = [];
  const labels = [];

  months.forEach(function(m) {
    labels.push(m.label);
    let inc = 0;
    let exp = 0;
    transactions.forEach(function(t) {
      if (String(t.date).startsWith(m.key)) {
        if (t.type === 'Income') inc += parseFloat(t.amount || 0);
        if (t.type === 'Expense') exp += parseFloat(t.amount || 0);
      }
    });
    incomeData.push(inc);
    expenseData.push(exp);
  });

  if (barChartInstance) {
    barChartInstance.destroy();
    barChartInstance = null;
  }

  const ctx = currentCanvas.getContext('2d');
  barChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Income',
          data: incomeData,
          backgroundColor: '#F97316',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.65
        },
        {
          label: 'Expense',
          data: expenseData,
          backgroundColor: '#FED7AA',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.65
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            color: '#E5E5E5',
            font: { family: 'Inter', size: 12, weight: 500 },
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16
          }
        },
        tooltip: {
          backgroundColor: '#222222',
          titleColor: '#FFFFFF',
          bodyColor: '#E5E5E5',
          borderColor: '#2A2A2A',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          titleFont: { family: 'Inter', size: 13, weight: 600 },
          bodyFont: { family: 'Inter', size: 12 },
          callbacks: {
            label: function(context) {
              const val = context.parsed.y || 0;
              return ` ${context.dataset.label}: ₹${val.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: '#9CA3AF',
            font: { family: 'Inter', size: 11, weight: 500 }
          }
        },
        y: {
          grid: { color: '#262626' },
          ticks: {
            color: '#9CA3AF',
            font: { family: 'Inter', size: 11 },
            callback: function(value) {
              if (value >= 1000) return '₹' + (value / 1000) + 'k';
              return '₹' + value;
            }
          }
        }
      }
    }
  });
}

function autoInitCharts() {
  if (document.getElementById('expensePieChart') || document.getElementById('incomeExpenseBarChart')) {
    const txs = (typeof SpendWiseStore !== 'undefined') ? SpendWiseStore.getTransactions() : (window.__INITIAL_DATA__ ? window.__INITIAL_DATA__.transactions : []);
    const curM = (typeof getCurrentMonthKey === 'function') ? getCurrentMonthKey() : new Date().toISOString().slice(0, 7);
    window.renderDashboardChartsFromStore(txs, curM);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', autoInitCharts);
} else {
  autoInitCharts();
}
