# 💸 SpendWise — Personal Finance Tracker

SpendWise is a sleek, modern, full-stack personal finance tracker built with Flask, SQLite, and vanilla HTML/CSS/JavaScript with a dark fintech UI and orange accents.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- Flask & Werkzeug (`pip install -r requirements.txt`)

### 2. Run the Application
```bash
python app.py
```

The database (`spendwise.db`) is automatically created and seeded on the very first run.
Open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 👤 Demo Credentials
You can log in directly with the pre-seeded account:
- **Email:** `test@spendwise.com`
- **Password:** `test123`
*(There is also an instant "Use Demo Credentials" button on the login screen for 1-click convenience!)*

---

## 🎨 Design System
- **Dark Background:** `#0F0F0F`
- **Card Background:** `#1A1A1A`
- **Surface & Hover:** `#222222` / `#2A2A2A`
- **Primary Accent:** Orange `#F97316`
- **Text:** Crisp White `#FFFFFF` & Light Grey `#E5E5E5`
- **Typography:** `Inter` from Google Fonts
- **Currency:** Indian Rupee symbol `₹` with formatted numbers
- **Dynamic Progress Bars:** Orange below 85% usage; changes to Red `#EF4444` when exceeding 85% threshold.

---

## 🛠️ Features & Pages

1. **Authentication (`/login`)**
   - Clean dark-mode card with SpendWise orange branding.
   - Toggle seamlessly between Login and Register on the same page.
   - Secure password hashing using `werkzeug.security`.

2. **Dashboard (`/dashboard`)**
   - 3 Summary Cards: Total Income (this month), Total Expense (this month), Net Balance.
   - **Expense Breakdown Chart:** Doughnut chart rendered with Chart.js using warm orange shades (`#F97316`, `#FB923C`, `#FDBA74`, `#FED7AA`).
   - **Income vs Expense Bar Chart:** 6-month side-by-side comparison.
   - **Recent Transactions:** Last 5 entries with quick Edit / Delete actions.
   - **Floating Action Button (`+`):** Bottom-right quick entry launcher.

3. **Transactions Page (`/transactions`)**
   - Full chronological ledger with newest entries first.
   - Filter bar: Filter by Month, Category, or Type (All / Income / Expense).
   - Incomes highlighted in Green (`+₹`), Expenses in Red (`-₹`).
   - Edit (✏️) and Delete (🗑️) on every row.

4. **Add / Edit Transaction Modal**
   - Universal popup modal overlay accessible across pages.
   - Segmented toggle between Income and Expense.
   - Dynamic Category selector based on type:
     - Expense: `Food`, `Rent`, `Transport`, `Entertainment`, `Shopping`, `Health`, `Others`.
     - Income: `Salary`, `Freelance`, `Gift`, `Others`.
     - Real-time validation for positive amount, date, and category.

5. **Budgets Page (`/budgets`)**
   - Category cards for all 7 expense categories.
   - Shows monthly limit, spent amount, remaining balance, and usage percentage.
   - Intelligent progress bar: Orange under 85%, Red when spending crosses 85%.
   - Inline "Set Limit" button to adjust monthly budgets directly on each card without page reloads.

6. **History Page (`/history`)**
   - 6-month summary table: Month, Total Income, Total Expenses, Net Savings.
   - Net Savings displayed in Green for surplus months and Red for deficit months.
   - Pre-seeded with 6 months of realistic data, including months with expenses exceeding income.

---

## 📁 Project Architecture
```
spendwise/
├── app.py              # Flask server, routing, Jinja2 filters, API endpoints
├── database.py         # SQLite schema initialization and connection management
├── seed.py             # Automatic dummy data generator (6 months of transactions & budgets)
├── requirements.txt    # Project dependencies
├── README.md           # Documentation
├── static/
│   ├── css/
│   │   └── style.css   # Custom dark mode styles, buttons, cards, modals, transitions
│   └── js/
│       ├── main.js     # Modal management, category toggle, inline budget edits, AJAX calls
│       ├── charts.js   # Chart.js initialization for Doughnut and Bar charts
│       └── chart.min.js# Bundled Chart.js fallback
└── templates/
    ├── base.html       # Base layout with navbar, modal container, FAB button
    ├── auth.html       # Login and registration view
    ├── dashboard.html  # Dashboard with summary metrics, charts, recent transactions
    ├── transactions.html # Full transaction log with filters and actions
    ├── budgets.html    # Budget limit cards with dual-color progress bars
    └── history.html    # 6-Month financial ledger
```
