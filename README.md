# MoneyMate – Smart Expense Tracker 💰📊

A modern, responsive, and full-featured financial management web application built with **Python Django**, **HTML5/CSS3/JavaScript**, and **Chart.js**. MoneyMate helps students and individuals master their daily finances, curtail unnecessary expenses, create category budgets with automated warnings, and achieve target savings goals.

---

## 🌟 Key Features

### 1. Modern Financial Dashboard
- **Live Metric Cards**: Total Balance, Total Income, Total Expenses, Remaining Budget, and Total Savings.
- **Interactive Chart.js Visualizations**:
  - 📊 Monthly Income vs Expenses Comparison (Multi-bar chart)
  - 🍩 Category Spending Distribution (Doughnut chart with percentages)
  - 📈 Weekly Spending Trends (Smooth 7-day line chart)
  - 📉 12-Month Historical Financial Trajectory
- **Active Budget Monitors**: Live visual consumption gauges with 80% warnings and exceeded alerts.
- **Recent Transactions & Quick Add**: Instant modal access to record transactions from anywhere.

### 2. Expense & Income Management
- Add, edit, delete, and view expenses and income separately.
- Categorization across **Food & Dining**, **Transportation**, **Education**, **Shopping**, **Bills & Utilities**, **Healthcare**, **Entertainment**, **Personal Care**, **Salary**, **Freelance**, etc.
- Multi-channel payment tracking: **UPI / GPay / PhonePe**, **Cash**, **Debit Card**, **Credit Card**, **Net Banking**, and **Mobile Wallets**.
- **Search & Advanced Filtering**: Filter by date range, category, transaction type, payment method, and amount thresholds.
- **Sorting & Aggregation**: Sort by newest, oldest, highest, or lowest amount. View live calculated spending totals for filtered results.
- **Pagination**: Clean, fast paginated records.

### 3. Smart Budgets & Automated Alerts
- Set monthly limits globally and on individual categories.
- Visual progress bars showing consumption percentage.
- **⚠️ 80% Warning Threshold**: Automatic alert banner when spending reaches 80% of budget.
- **🚨 Overspent Alert**: Instant danger alert when budget is exceeded (>100%).
- **Roll-over / Reset**: Duplicate or reset budgets into the new month with one click without losing past transaction ledger history.

### 4. Milestone Savings Goals
- Create named goals: *Apple MacBook Pro*, *College Tuition*, *Emergency Fund*, *Vacation Road Trip*.
- Target dates, target amounts, and live progress bars.
- **Add Money**: Deposit savings into goal vaults anytime.
- Days remaining countdown and automatic completion badges.

### 5. Financial Reports & Analytics
- Monthly, Annual, and All-Time financial statements.
- Category-wise expense breakdown with transaction frequency counts and percentages.
- **CSV Spreadsheet Export**: Export filtered or all transactions with one click.
- **Printable Report**: Clean, professional printable statement (`@media print` and dedicated print layout) ready for saving as PDF or physical printout.

### 6. Recurring Expenses & Bills
- Register recurring bills (House Rent, Broadband, Netflix, Gym).
- Manage billing frequency: Daily, Weekly, Monthly, Yearly.
- **Pay Now / Auto-Record**: Record due payments as transactions and update next due dates.

### 7. User Customization & Authentication
- Secure Django user authentication, password validation, and CSRF protection.
- Strict data isolation: each user only ever accesses their own records.
- **Currency Selection**: Default **INR (₹)** with support for USD ($), EUR (€), GBP (£), JPY (¥), AED, etc.
- **Light & Dark Mode**: Persistent toggle with seamless CSS variables and Chart.js theme re-rendering.
- **One-Click Demo Data Loader**: Populate realistic transactions, budgets, goals, and alerts for instant college project demonstrations.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, Django 5+ / 6.0+ |
| **Database** | SQLite3 (Zero configuration, standard in development) |
| **Frontend** | HTML5, Modern CSS3 (CSS Variables, Flexbox, Grid), Vanilla JavaScript |
| **Charts** | Chart.js 4 (via CDN) |
| **Icons** | Font Awesome 6 (via CDN) |
| **Design** | Green (`#10B981`), White (`#FFFFFF`), Dark Navy (`#0F172A`) |

---

## 📂 Project Structure

```text
moneymate/
├── manage.py                          # Django management script
├── requirements.txt                   # Python package dependencies
├── README.md                          # Project documentation
│
├── moneymate_project/                 # Django project configuration
│   ├── settings.py                    # App settings, static, templates, context processors
│   ├── urls.py                        # Project root URL dispatcher
│   ├── asgi.py
│   └── wsgi.py
│
├── tracker/                           # Core MoneyMate application
│   ├── admin.py                       # Django Admin models configuration
│   ├── apps.py                        # App configuration & signal registry
│   ├── context_processors.py          # Global currency, theme, notification processor
│   ├── forms.py                       # Forms for transactions, budgets, goals, profile
│   ├── models.py                      # Database models (Transaction, Budget, SavingsGoal, etc.)
│   ├── signals.py                     # Automatic UserProfile & default category creation
│   ├── tests.py                       # Automated test suite
│   ├── urls.py                        # Tracker URL endpoints
│   ├── utils.py                       # Demo data generator & budget alert triggers
│   ├── views.py                       # View logic for dashboard, reports, budgets, transactions
│   ├── templatetags/
│   │   └── tracker_tags.py            # Custom template tags (currency, percentage math)
│   └── management/
│       └── commands/
│           └── seed_demo.py           # CLI command: python manage.py seed_demo
│
├── static/                            # Static assets
│   ├── css/
│   │   └── style.css                  # Design system, light/dark mode CSS variables
│   └── js/
│       ├── main.js                    # Theme toggle, modals, dynamic filters
│       └── charts.js                  # Chart.js initialization & theme listeners
│
└── templates/                         # HTML templates
    ├── base.html                      # Sidebar, topbar, modals & layout shell
    ├── landing.html                   # Public hero landing page
    ├── registration/
    │   ├── login.html                 # Login page
    │   └── register.html              # Registration page with currency picker
    └── tracker/
        ├── dashboard.html             # Main financial dashboard
        ├── transactions.html          # Transaction list with multi-filters
        ├── transaction_form.html      # Add / Edit transaction
        ├── transaction_confirm_delete.html # Confirm delete dialog
        ├── budgets.html               # Category budgets & roll-over
        ├── savings.html               # Savings goals & deposit vault
        ├── reports.html               # Analytics, trends & CSV export
        ├── report_print.html          # Printable PDF-ready statement
        ├── recurring.html             # Recurring bills manager
        ├── profile.html               # User profile, currency & demo loader
        └── notifications.html         # Alerts & notification center
```

---

## 🚀 How to Run the Website Locally (VS Code / Terminal)

### Step 1: Open the Project in VS Code
Open the project directory in VS Code:
```bash
cd "C:\Users\lahar\.gemini\antigravity\scratch"
```

### Step 2: Ensure Dependencies Are Installed
Verify Python and install dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Run Database Migrations
Create the SQLite database tables:
```bash
python manage.py migrate
```

### Step 4: (Optional) Seed Demo Data
To immediately test the application with realistic transactions, budgets, goals, and alerts, run:
```bash
python manage.py seed_demo
```
> **Demo Credentials Created:**
> - **Username:** `demo`
> - **Password:** `demo12345`

*Alternatively, you can register a new account through the web interface at any time and click **"Populate Sample Dataset"** inside Settings & Profile.*

### Step 5: Start the Development Server
```bash
python manage.py runserver
```

### Step 6: Open in Your Browser
Visit:
- **Landing Page:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Login Page:** [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Register Page:** [http://127.0.0.1:8000/register/](http://127.0.0.1:8000/register/)
- **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Running Automated Tests

Run the test suite to verify database operations, budget alert thresholds, and user privacy isolation:
```bash
python manage.py test
```

---

## 🔒 Security & Privacy Architecture
- **Django Auth & CSRF Protection**: Every form is safeguarded against cross-site request forgery.
- **Strict Query Filtering**: All database operations query `Transaction.objects.filter(user=request.user)`. One user can never see or modify another user's financial records.
- **Secure Password Hashing**: Passwords use PBKDF2 with SHA256; no plain-text credentials are ever stored.
