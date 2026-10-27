# SpendWise: B.Tech. Student Edition (Parnika Lilani)

SpendWise is a dark-themed personal finance tracker adapted for Parnika Lilani, an engineering student. It is built with Flask, SQLite, and standard HTML, CSS, and JavaScript.

---

## Tailored for College Life

SpendWise tracks expense and income categories for campus life:

### Student Expense Categories
1. **Hostel Fees**: Semester accommodation, room installment, mess fees, and laundry deposits.
2. **Food**: Campus canteen lunches, cutting chai, snacks, and exam week food.
3. **Fuel**: Two-wheeler scooty fuel for college and lab commute.
4. **Travel**: Metro card recharge, auto rides, and holiday trains back home for semester breaks.
5. **Stationery**: Engineering drawing sheets, Casio scientific calculator, lab journals, and assignment printouts.
6. **Phone Recharge**: 5G student data plans and hostel shared Wi-Fi contributions.
7. **Tech & Books**: Online course certifications, core engineering textbooks, and cloud credits for projects.
8. **Entertainment**: College fest tickets, movie outings, and team celebrations.
9. **Others**: University exam fees, pharmacy, and personal care.

### Student Income Streams
- **Allowance**: Monthly pocket money and college support from parents.
- **Internship Stipend**: Software development internship earnings.
- **Freelance**: Python automation scripts, web design, and technical assignments.
- **Scholarship**: University academic merit awards.

---

## Quick Start

### 1. Run the Application
```bash
python app.py
```

The database (`spendwise.db`) is automatically initialized and seeded on first run.
Open your browser at:
**http://127.0.0.1:5000**

---

## Demo Student Account

| Field | Value |
|---|---|
| **Name** | Parnika Lilani |
| **Email** | `parnika@spendwise.com` (or `test@spendwise.com`) |
| **Password** | `test123` |
| **Quick Access** | Click "Fill Parnika Lilani Credentials" on the login page for quick entry. |

---

## Visual Design System

- **Background:** `#0F0F0F`
- **Cards & Surfaces:** `#1A1A1A` with border `#2A2A2A`
- **Primary Accent:** Orange `#F97316`
- **Typography:** `Plus Jakarta Sans` for headings, `Inter` for interface elements
- **Currency:** Indian Rupee (`₹`)
- **Dual-Color Progress Bars**:
  - Orange (`#F97316`) when category spending is under 85% of limit.
  - Red (`#EF4444`) when spending crosses 85%.
- **6-Month Financial Ledger**:
  - Highlights surplus months in Green.
  - Highlights deficit months in Red (such as August semester commencement hostel payments).

---

## Project Structure
```
spendwise/
├── app.py                     # Entry point importing backend application
├── requirements.txt           # Dependencies (Flask, Werkzeug)
├── vercel.json                # Vercel deployment configuration
├── README.md                  # Project documentation
├── test_spendwise.py          # Complete student test suite
├── api/
│   └── index.py               # Vercel serverless WSGI entry point
├── backend/
│   ├── app.py                 # Flask server, authentication, APIs, and routes
│   ├── database.py            # SQLite schema and connection manager
│   ├── seed.py                # 6-Month student seed data generator
│   └── spendwise.db           # SQLite database file
└── frontend/
    ├── static/
    │   ├── css/
    │   │   └── style.css      # Dark theme styling, inputs, tables, modal
    │   └── js/
    │       ├── main.js        # Reactive store, client persistence, modal CRUD
    │       ├── charts.js      # Chart.js Doughnut and Bar visualizations
    │       └── chart.min.js   # Local Chart.js fallback script
    └── templates/
        ├── base.html          # Base layout with navbar, modal, and action button
        ├── auth.html          # Student login and registration
        ├── dashboard.html     # Campus and semester financial overview
        ├── transactions.html  # Filterable transaction ledger
        ├── budgets.html       # Category spending limits and progress bars
        └── history.html       # 6-Month surplus and deficit ledger
```
