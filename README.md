# 💸 SpendWise — B.Tech. Student Edition (Parnika Lilani)

SpendWise is a sleek, dark-themed personal finance tracker specifically adapted for **Parnika Lilani**, a B.Tech. engineering student. Built with **Flask**, **SQLite**, and **vanilla HTML/CSS/JavaScript** (no React, no npm, no frontend frameworks).

---

## 🎓 Tailored for B.Tech. College Life

SpendWise includes spending and income streams designed for an engineering student:

### 📉 Student Expense Categories:
1. **🏠 Hostel Fees**: Semester accommodation, room installment, mess fees, laundry deposits.
2. **🍔 Food**: College mess card recharge, campus canteen cutting chai & samosas, midnight Maggi during exams.
3. **⛽ Fuel**: Two-wheeler scooty petrol for college, coaching, and lab commute.
4. **🚆 Travel**: Metro card recharge, auto rides, holiday trains & buses back home for semester breaks.
5. **📚 Stationery**: Engineering graphics drawing sheets, Casio fx-991CW scientific calculator, lab journals, assignment Xerox and printouts.
6. **📱 Phone Recharge**: 5G student data plans (Airtel / Jio 3-month unlimited pack), hostel room shared WiFi contribution.
7. **💻 Tech & Books**: Udemy/Coursera coding courses, core engineering textbooks (DSA, OS, DBMS), cloud credits for group projects.
8. **🎬 Entertainment**: College tech fest & hackathon passes, batch movie nights, outings with friends.
9. **📦 Others**: Semester exam admit card fees, campus pharmacy, personal care.

### 📈 Student Income Streams:
- **💵 Allowance**: Monthly pocket money and college support from parents.
- **💼 Internship Stipend**: Remote / summer frontend software development internship earnings.
- **💻 Freelance**: Python automation scripts, web design, and coding tasks for seniors/clients.
- **🎓 Scholarship**: University merit-cum-means scholarship awards.

---

## 🚀 Quick Start

### 1. Run the Application
```bash
python app.py
```

The database (`spendwise.db`) is automatically initialized and seeded on the very first run.
Open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 👤 Test Student Account

| Field | Value |
|---|---|
| **Name** | **Parnika Lilani** |
| **Email** | `parnika@spendwise.com` (or `test@spendwise.com`) |
| **Password** | `test123` |
| **Quick Access** | Click **"⚡ Login as Parnika Lilani"** on the login page for 1-click demo entry! |

---

## 🎨 Visual Design System

- **Dark Mode Background:** `#0F0F0F`
- **Cards & Surfaces:** `#1A1A1A` with subtle border `#2A2A2A`
- **Primary Accent:** Orange `#F97316`
- **Typography:** `Inter` from Google Fonts
- **Currency:** Indian Rupee `₹`
- **Intelligent Dual-Color Progress Bars**:
  - **Orange (`#F97316`)** when spending $\le 85\%$ of the category budget limit.
  - **Red (`#EF4444`)** when category spending crosses $> 85\%$ (e.g. `Stationery` at $94.7\%$ and `Phone Recharge` at $89.9\%$).
- **6-Month Financial Ledger**:
  - Highlights surplus months in **Green** (`+₹`).
  - Highlights deficit months in **Red** (`-₹`) (e.g. August semester commencement with hostel fee payments).

---

## 📁 Project Architecture
```
spendwise/
├── app.py                     # Flask server with student categories & JSON APIs
├── database.py                # SQLite schema and connection manager
├── seed.py                    # 6-Month realistic student dummy data generator
├── test_spendwise.py          # Complete student test suite
├── requirements.txt           # Dependencies (Flask, Werkzeug)
├── README.md                  # Student edition documentation
├── static/
│   ├── css/
│   │   └── style.css          # Dark theme styles, inputs, cards, tables, modal
│   └── js/
│       ├── main.js            # Student categories switcher, modal, AJAX CRUD
│       ├── charts.js          # Chart.js Doughnut & Bar visualizations
│       └── chart.min.js       # Bundled Chart.js fallback script
└── templates/
    ├── base.html              # Base layout with navbar, modal & FAB button
    ├── auth.html              # Student login & registration
    ├── dashboard.html         # Campus & semester financial overview
    ├── transactions.html      # Filterable transaction ledger
    ├── budgets.html           # Category spending limits & dual-color progress bars
    └── history.html           # 6-Month surplus / deficit ledger
```
