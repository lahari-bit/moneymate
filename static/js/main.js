/**
 * MoneyMate - Main Application Scripts
 * Handles Dark/Light Mode, Mobile Navigation, Modals, Dynamic Form Behaviors
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme Management (Light / Dark)
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeToggleIcon');
  const htmlElement = document.documentElement;

  // Retrieve saved theme or system preference
  const savedTheme = localStorage.getItem('moneymate_theme') || htmlElement.getAttribute('data-theme') || 'light';
  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = htmlElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('moneymate_theme', newTheme);
      
      // Notify Chart.js to update colors if chart is active
      if (window.updateChartsTheme) {
        window.updateChartsTheme(newTheme);
      }
    });
  }

  function applyTheme(theme) {
    htmlElement.setAttribute('data-theme', theme);
    if (themeIcon) {
      if (theme === 'dark') {
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
      } else {
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
      }
    }
  }

  // 2. Mobile Sidebar Toggle
  const menuToggleBtn = document.getElementById('menuToggleBtn');
  const sidebar = document.querySelector('.app-sidebar');
  let sidebarOverlay = document.getElementById('sidebarOverlay');

  if (menuToggleBtn && sidebar) {
    menuToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
      if (sidebar.classList.contains('mobile-open')) {
        createSidebarOverlay();
      } else {
        removeSidebarOverlay();
      }
    });
  }

  function createSidebarOverlay() {
    if (!sidebarOverlay) {
      sidebarOverlay = document.createElement('div');
      sidebarOverlay.id = 'sidebarOverlay';
      sidebarOverlay.style.cssText = `
        position: fixed; inset: 0; background: rgba(0,0,0,0.5);
        z-index: 45; backdrop-filter: blur(2px);
      `;
      sidebarOverlay.addEventListener('click', () => {
        sidebar.classList.remove('mobile-open');
        removeSidebarOverlay();
      });
      document.body.appendChild(sidebarOverlay);
    }
  }

  function removeSidebarOverlay() {
    if (sidebarOverlay) {
      sidebarOverlay.remove();
      sidebarOverlay = null;
    }
  }

  // 3. Dynamic Category Filtering based on Transaction Type (Income vs Expense)
  const txTypeSelect = document.getElementById('id_transaction_type');
  const categorySelect = document.getElementById('id_category');

  if (txTypeSelect && categorySelect) {
    // Store original options
    const originalOptions = Array.from(categorySelect.options).map(opt => ({
      value: opt.value,
      text: opt.text,
      selected: opt.selected
    }));

    function filterCategories() {
      const selectedType = txTypeSelect.value;
      const currentValue = categorySelect.value;
      categorySelect.innerHTML = '';

      originalOptions.forEach(opt => {
        if (!opt.value) {
          categorySelect.appendChild(new Option(opt.text, opt.value));
          return;
        }
        const textLower = opt.text.toLowerCase();
        let matches = true;

        if (selectedType === 'income') {
          // Check if category represents income
          if (textLower.includes('salary') || textLower.includes('freelance') || 
              textLower.includes('allowance') || textLower.includes('income') || 
              textLower.includes('scholarship') || textLower.includes('investment') ||
              textLower.includes('(income)')) {
            matches = true;
          } else {
            matches = false;
          }
        } else if (selectedType === 'expense') {
          if (textLower.includes('(income)') || textLower.includes('salary') || textLower.includes('scholarship')) {
            matches = false;
          } else {
            matches = true;
          }
        }

        if (matches) {
          const optionEl = new Option(opt.text, opt.value);
          if (opt.value === currentValue) {
            optionEl.selected = true;
          }
          categorySelect.appendChild(optionEl);
        }
      });
    }

    txTypeSelect.addEventListener('change', filterCategories);
  }

  // 4. Auto-dismiss Alert Messages
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 6000);
  });
});

// 5. Global Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modals when clicking outside container
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
    document.body.style.overflow = '';
  }
});
