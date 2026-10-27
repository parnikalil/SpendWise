import os
import sys
import datetime
from werkzeug.security import generate_password_hash

# Handle imports whether run standalone or imported
try:
    from backend.database import get_db_connection
except ImportError:
    from database import get_db_connection

def get_relative_month(base_date, month_offset):
    """
    Returns (year, month) for base_date minus month_offset months.
    offset = 0 is base_date's month.
    """
    y = base_date.year
    m = base_date.month - month_offset
    while m <= 0:
        m += 12
        y -= 1
    return y, m

def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if student account already exists
    cursor.execute("SELECT id FROM users WHERE email = ? OR email = ?", ("parnika@spendwise.com", "test@spendwise.com"))
    existing_user = cursor.fetchone()

    password_hash = generate_password_hash("test123")

    if existing_user:
        user_id = existing_user["id"]
        cursor.execute("UPDATE users SET name = 'Parnika Lilani', email = 'parnika@spendwise.com' WHERE id = ?", (user_id,))
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE user_id = ?", (user_id,))
        if cursor.fetchone()["count"] > 0:
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
            conn.commit()
    else:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, ("Parnika Lilani", "parnika@spendwise.com", password_hash))
        user_id = cursor.lastrowid
        print(f"Created student account: Parnika Lilani (parnika@spendwise.com)")

    # Also ensure test@spendwise.com exists as an alias for compatibility
    cursor.execute("SELECT id FROM users WHERE email = 'test@spendwise.com'")
    if not cursor.fetchone() and existing_user is None:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, ("Parnika Lilani", "test@spendwise.com", password_hash))

    today = datetime.date.today()

    months_data = [
        # offset 0: Current Month (e.g. October 2026) — Active Semester
        (
            0,
            [
                ("Allowance", 18000.0, 1, "Monthly allowance from parents"),
                ("Internship Stipend", 15000.0, 12, "Frontend developer intern stipend (Remote)"),
                ("Freelance", 6500.0, 20, "Python automation script for college senior")
            ],
            [
                ("Hostel Fees", 8500.0, 2, "Monthly hostel accommodation & mess fee"),
                ("Food", 1250.0, 4, "Hostel canteen lunch & evening chai-samosa"),
                ("Fuel", 650.0, 6, "Activa scooty petrol for college & lab commute"),
                ("Stationery", 780.0, 8, "Engineering drawing sheets & lab manual journals"),
                ("Phone Recharge", 899.0, 10, "Airtel 5G 3-month unlimited data plan"),
                ("Food", 450.0, 13, "Midnight Maggi & cold coffee during quiz prep"),
                ("Travel", 600.0, 15, "Metro card recharge for city project commute"),
                ("Stationery", 640.0, 18, "Final project printouts, spiral binding & chart papers"),
                ("Tech & Books", 1290.0, 21, "Data Structures & Algorithms reference handbook"),
                ("Entertainment", 1200.0, 22, "College Tech Fest Hackathon entry fee & team snacks"),
                ("Food", 850.0, 23, "Weekend dinner with wingmates after exam submission"),
                ("Fuel", 550.0, 24, "Petrol top-up for weekend library commute"),
                ("Food", 680.0, 25, "Campus bakery sandwich & juices"),
                ("Others", 450.0, 26, "Hostel laundry & ironing charges")
            ],
            {
                "Hostel Fees": 12000.0,
                "Food": 5500.0,
                "Fuel": 2000.0,
                "Travel": 2500.0,
                "Stationery": 1500.0,
                "Phone Recharge": 1000.0,
                "Tech & Books": 3000.0,
                "Entertainment": 2000.0,
                "Others": 1500.0
            }
        ),
        # offset 1: 1 Month Ago (e.g. September 2026) — Mid-Term Exams
        (
            1,
            [
                ("Allowance", 18000.0, 1, "Monthly allowance from parents"),
                ("Internship Stipend", 15000.0, 10, "Frontend developer intern stipend")
            ],
            [
                ("Hostel Fees", 8500.0, 2, "Hostel room & mess monthly installment"),
                ("Food", 2400.0, 5, "Canteen meals & cafeteria snacks"),
                ("Fuel", 1100.0, 8, "Scooty fuel for mid-term exam commute"),
                ("Stationery", 820.0, 11, "Scientific calculator Casio fx-991CW battery & notebooks"),
                ("Phone Recharge", 350.0, 14, "Hostel room shared high-speed WiFi contribution"),
                ("Travel", 850.0, 17, "Metro pass recharge for coaching & college"),
                ("Tech & Books", 649.0, 20, "Coursera Machine Learning certification course"),
                ("Entertainment", 950.0, 24, "Post mid-term movie with hostel friends"),
                ("Others", 580.0, 27, "Campus medical store pharmacy & headache balm")
            ],
            {
                "Hostel Fees": 12000.0,
                "Food": 5500.0,
                "Fuel": 2000.0,
                "Travel": 2500.0,
                "Stationery": 1500.0,
                "Phone Recharge": 1000.0,
                "Tech & Books": 3000.0,
                "Entertainment": 2000.0,
                "Others": 1500.0
            }
        ),
        # offset 2: 2 Months Ago (e.g. August 2026) — SEMESTER COMMENCEMENT (Expenses > Income)
        (
            2,
            [
                ("Allowance", 20000.0, 1, "Semester start allowance from parents"),
                ("Internship Stipend", 15000.0, 15, "Frontend developer intern stipend")
            ],
            [
                ("Hostel Fees", 28000.0, 2, "Odd semester hostel room & mess fee payment"),
                ("Stationery", 3450.0, 5, "Casio fx-991CW calculator, mini drafter & B.Tech books"),
                ("Tech & Books", 5800.0, 8, "Core Engineering textbooks & Cloud lab subscription"),
                ("Travel", 2200.0, 11, "Semester return train tickets & luggage transit"),
                ("Food", 4800.0, 14, "Mess advance & orientation week dining"),
                ("Fuel", 1400.0, 18, "Scooty petrol for semester onboarding"),
                ("Phone Recharge", 899.0, 21, "Jio 5G semester unlimited data pack"),
                ("Entertainment", 3200.0, 24, "Freshers welcome fest ticket & college society t-shirt"),
                ("Others", 2490.0, 27, "Hostel room mattress, bucket, study lamp & locks")
            ],
            {
                "Hostel Fees": 30000.0,
                "Food": 6000.0,
                "Fuel": 2000.0,
                "Travel": 3000.0,
                "Stationery": 4000.0,
                "Phone Recharge": 1000.0,
                "Tech & Books": 6000.0,
                "Entertainment": 3500.0,
                "Others": 3000.0
            }
        ),
        # offset 3: 3 Months Ago (e.g. July 2026) — Summer Internship & Scholarship
        (
            3,
            [
                ("Scholarship", 25000.0, 5, "University Academic Merit Scholarship award"),
                ("Internship Stipend", 18000.0, 10, "Summer Software Intern stipend"),
                ("Allowance", 12000.0, 12, "Allowance from parents")
            ],
            [
                ("Hostel Fees", 8500.0, 2, "Summer hostel accommodation charges"),
                ("Food", 4200.0, 6, "Internship office canteen lunches & tea"),
                ("Travel", 2800.0, 12, "Metro daily pass for tech park commute"),
                ("Fuel", 1250.0, 16, "Scooty petrol for tech campus"),
                ("Tech & Books", 2400.0, 19, "LeetCode Premium 1-year student subscription"),
                ("Stationery", 650.0, 22, "Coding notebook, sticky notes & pens"),
                ("Phone Recharge", 350.0, 24, "Monthly data booster add-on"),
                ("Entertainment", 2100.0, 26, "Internship team lunch & bowling outing"),
                ("Others", 1200.0, 28, "Professional formal clothes for intern presentation")
            ],
            {
                "Hostel Fees": 12000.0,
                "Food": 5500.0,
                "Fuel": 2000.0,
                "Travel": 3000.0,
                "Stationery": 1500.0,
                "Phone Recharge": 1000.0,
                "Tech & Books": 3000.0,
                "Entertainment": 2500.0,
                "Others": 1500.0
            }
        ),
        # offset 4: 4 Months Ago (e.g. June 2026) — Semester End Travel & Gear
        (
            4,
            [
                ("Allowance", 16000.0, 1, "Allowance from parents"),
                ("Freelance", 8000.0, 20, "Web design for college society website")
            ],
            [
                ("Hostel Fees", 8500.0, 2, "Hostel mess & room clearance"),
                ("Travel", 6500.0, 6, "Flight / AC Train ticket back home for summer vacation"),
                ("Tech & Books", 12500.0, 10, "Laptop SSD & RAM upgrade for Engineering CAD & coding"),
                ("Food", 3400.0, 14, "Travel meals and semester end farewell party"),
                ("Stationery", 1850.0, 17, "Semester project hardbound thesis printing & binding"),
                ("Fuel", 950.0, 21, "Commute to railway station and courier service"),
                ("Phone Recharge", 899.0, 24, "3-month vacation roaming mobile plan"),
                ("Entertainment", 2400.0, 26, "Farewell celebration with B.Tech classmates"),
                ("Others", 1150.0, 28, "Hostel room luggage packing cartons & courier home")
            ],
            {
                "Hostel Fees": 12000.0,
                "Food": 5500.0,
                "Fuel": 2000.0,
                "Travel": 7000.0,
                "Stationery": 2000.0,
                "Phone Recharge": 1000.0,
                "Tech & Books": 13000.0,
                "Entertainment": 2500.0,
                "Others": 1500.0
            }
        ),
        # offset 5: 5 Months Ago (e.g. May 2026) — Even Semester Exams
        (
            5,
            [
                ("Allowance", 18000.0, 1, "Monthly allowance from parents"),
                ("Freelance", 12000.0, 14, "Python Django backend API task for start-up")
            ],
            [
                ("Hostel Fees", 8500.0, 2, "Monthly hostel accommodation & mess fee"),
                ("Food", 3100.0, 6, "Hostel mess & night canteen coffee/bun-maska"),
                ("Fuel", 950.0, 10, "Scooty fuel for university exam center"),
                ("Stationery", 1200.0, 15, "Semester exam answer sheets, graph pads & geometry box"),
                ("Phone Recharge", 350.0, 18, "Hostel WiFi top-up"),
                ("Travel", 1150.0, 21, "Auto & metro rides during practical exam week"),
                ("Tech & Books", 1800.0, 24, "Database Systems & Operating Systems guidebooks"),
                ("Entertainment", 1400.0, 27, "Post-exam celebration dinner with project partners"),
                ("Others", 1000.0, 28, "Semester examination admit card & university fees")
            ],
            {
                "Hostel Fees": 12000.0,
                "Food": 5500.0,
                "Fuel": 2000.0,
                "Travel": 2500.0,
                "Stationery": 1500.0,
                "Phone Recharge": 1000.0,
                "Tech & Books": 3000.0,
                "Entertainment": 2000.0,
                "Others": 1500.0
            }
        ),
    ]

    for offset, incomes, expenses, budgets in months_data:
        year, month = get_relative_month(today, offset)

        # Insert Incomes
        for cat, amt, day, note in incomes:
            actual_day = min(day, today.day if offset == 0 else 28)
            date_str = f"{year:04d}-{month:02d}-{actual_day:02d}"
            cursor.execute("""
                INSERT INTO transactions (user_id, type, amount, category, date, note)
                VALUES (?, 'Income', ?, ?, ?, ?)
            """, (user_id, amt, cat, date_str, note))

        # Insert Expenses
        for cat, amt, day, note in expenses:
            actual_day = min(day, today.day if offset == 0 else 28)
            date_str = f"{year:04d}-{month:02d}-{actual_day:02d}"
            cursor.execute("""
                INSERT INTO transactions (user_id, type, amount, category, date, note)
                VALUES (?, 'Expense', ?, ?, ?, ?)
            """, (user_id, amt, cat, date_str, note))

        # Insert Budgets
        for cat, limit in budgets.items():
            cursor.execute("""
                INSERT INTO budgets (user_id, category, limit_amount, month, year)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, category, month, year) 
                DO UPDATE SET limit_amount = excluded.limit_amount
            """, (user_id, cat, limit, month, year))

    conn.commit()
    conn.close()
    print("Seed data successfully inserted for Parnika Lilani (parnika@spendwise.com)!")

if __name__ == '__main__':
    seed_data()
