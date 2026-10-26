/**
 * SpendWise - Chart.js Visualizations for Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {
  initDashboardCharts();
});

async function initDashboardCharts() {
  const pieCanvas = document.getElementById('expensePieChart');
  const barCanvas = document.getElementById('incomeExpenseBarChart');

  if (!pieCanvas || !barCanvas) return;

  try {
    const response = await fetch('/api/charts');
    const data = await response.json();

    if (!data.success) {
      console.error('Failed to load chart data');
      return;
    }

    renderExpensePieChart(pieCanvas, data.expense_chart);
    renderIncomeExpenseBarChart(barCanvas, data.history_chart);
  } catch (error) {
    console.error('Error fetching chart data:', error);
  }
}

/**
 * Render Expense Breakdown by Category (Doughnut / Pie Chart)
 */
function renderExpensePieChart(canvas, chartData) {
  const ctx = canvas.getContext('2d');

  if (!chartData.data || chartData.data.length === 0) {
    const parent = canvas.parentElement;
    parent.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:#9CA3AF; gap:0.5rem;">
        <span style="font-size:2rem;">📊</span>
        <p style="font-size:0.9rem;">No expenses recorded for this month yet.</p>
      </div>
    `;
    return;
  }

  const orangeShades = [
    '#F97316', // Primary vibrant orange
    '#FB923C', // Amber orange
    '#FDBA74', // Peach orange
    '#FED7AA', // Soft pale orange
    '#EA580C', // Deep burnt orange
    '#C2410C', // Dark rust orange
    '#9A3412', // Deep earthy orange
    '#FF7A00', // Electric orange
    '#D97706', // Warm amber
    '#F59E0B'  // Golden yellow-orange
  ];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: chartData.labels,
      datasets: [{
        data: chartData.data,
        backgroundColor: orangeShades.slice(0, chartData.data.length),
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
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ₹${val.toLocaleString('en-IN')} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

/**
 * Render 6-Month Income vs Expense Bar Chart
 */
function renderIncomeExpenseBarChart(canvas, chartData) {
  const ctx = canvas.getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Income',
          data: chartData.income,
          backgroundColor: '#F97316', // Primary Orange
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.65
        },
        {
          label: 'Expense',
          data: chartData.expense,
          backgroundColor: '#FED7AA', // Soft Light Orange
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
          grid: {
            display: false
          },
          ticks: {
            color: '#9CA3AF',
            font: { family: 'Inter', size: 11, weight: 500 }
          }
        },
        y: {
          grid: {
            color: '#262626'
          },
          ticks: {
            color: '#9CA3AF',
            font: { family: 'Inter', size: 11 },
            callback: function(value) {
              if (value >= 1000) {
                return '₹' + (value / 1000) + 'k';
              }
              return '₹' + value;
            }
          }
        }
      }
    }
  });
}
