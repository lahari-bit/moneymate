/**
 * MoneyMate - Chart.js Initializers & Theme Adapters
 */

window.MoneyMateCharts = {};

function getChartColors() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    textColor: isDark ? '#94a3b8' : '#64748b',
    gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
    cardBg: isDark ? '#131b2e' : '#ffffff',
  };
}

// 1. Category Expenses Doughnut Chart
function initCategoryChart(canvasId, labels, data, colors, currency = '₹') {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  if (window.MoneyMateCharts[canvasId]) {
    window.MoneyMateCharts[canvasId].destroy();
  }

  const { textColor } = getChartColors();

  if (!labels || labels.length === 0) {
    // Show empty state inside canvas
    ctx.parentElement.innerHTML = `
      <div class="empty-state" style="padding: 2.5rem 1rem;">
        <i class="fa-solid fa-chart-pie empty-icon" style="font-size: 1.8rem; width: 50px; height: 50px;"></i>
        <p class="empty-desc" style="margin: 0;">No expense records found for this period.</p>
      </div>
    `;
    return null;
  }

  window.MoneyMateCharts[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.length ? colors : ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
        borderWidth: 2,
        borderColor: document.documentElement.getAttribute('data-theme') === 'dark' ? '#131b2e' : '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: textColor,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
            padding: 16,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${context.label}: ${currency}${val.toLocaleString()} (${pct}%)`;
            }
          }
        }
      }
    }
  });

  return window.MoneyMateCharts[canvasId];
}

// 2. Monthly Income vs Expenses Bar Chart
function initMonthlyComparisonChart(canvasId, labels, incomeData, expenseData, currency = '₹') {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  if (window.MoneyMateCharts[canvasId]) {
    window.MoneyMateCharts[canvasId].destroy();
  }

  const { textColor, gridColor } = getChartColors();

  window.MoneyMateCharts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Income',
          data: incomeData,
          backgroundColor: '#10b981',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.7
        },
        {
          label: 'Expenses',
          data: expenseData,
          backgroundColor: '#ef4444',
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.7
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textColor, font: { family: "'Plus Jakarta Sans', sans-serif" } }
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            font: { family: "'Plus Jakarta Sans', sans-serif" },
            callback: function(value) {
              return currency + (value >= 1000 ? (value / 1000) + 'k' : value);
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            color: textColor,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ${currency}${context.raw.toLocaleString()}`;
            }
          }
        }
      }
    }
  });

  return window.MoneyMateCharts[canvasId];
}

// 3. Weekly Spending Line Chart
function initWeeklySpendingChart(canvasId, labels, data, currency = '₹') {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  if (window.MoneyMateCharts[canvasId]) {
    window.MoneyMateCharts[canvasId].destroy();
  }

  const { textColor, gridColor } = getChartColors();

  window.MoneyMateCharts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Daily Spending',
        data: data,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#10b981',
        pointHoverRadius: 6,
        borderWidth: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textColor, font: { family: "'Plus Jakarta Sans', sans-serif" } }
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            callback: function(value) {
              return currency + (value >= 1000 ? (value / 1000) + 'k' : value);
            }
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` Spending: ${currency}${context.raw.toLocaleString()}`;
            }
          }
        }
      }
    }
  });

  return window.MoneyMateCharts[canvasId];
}

// Hook to update charts when user switches light/dark theme
window.updateChartsTheme = function(theme) {
  const { textColor, gridColor } = getChartColors();
  for (const chartId in window.MoneyMateCharts) {
    const chart = window.MoneyMateCharts[chartId];
    if (chart) {
      if (chart.options.scales) {
        if (chart.options.scales.x) {
          chart.options.scales.x.ticks.color = textColor;
        }
        if (chart.options.scales.y) {
          chart.options.scales.y.ticks.color = textColor;
          chart.options.scales.y.grid.color = gridColor;
        }
      }
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = textColor;
      }
      chart.update();
    }
  }
};
