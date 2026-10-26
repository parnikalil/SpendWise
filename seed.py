import os
import datetime
from werkzeug.security import generate_password_hash
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

    # Check if test user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", ("test@spendwise.com",))
    existing_user = cursor.fetchone()

    if existing_user:
        user_id = existing_user["id"]
        # Check if transactions already exist
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE user_id = ?", (user_id,))
        if cursor.fetchone()["count"] > 0:
            print("Seed data already present. Skipping.")
            conn.close()
            return
    else:
        # Create test user
        password_hash = generate_password_hash("test123")
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, ("Alex Morgan", "test@spendwise.com", password_hash))
        user_id = cursor.lastrowid
        print(f"Created test user: test@spendwise.com with ID: {user_id}")

    today = datetime.date.today()

    # We will generate data for 6 months (current month + 5 previous months)
    # Month 0: current month (positive savings)
    # Month 1: 1 month ago (positive savings)
    # Month 2: 2 months ago (NEGATIVE savings, expenses exceed income)
    # Month 3: 3 months ago (positive savings)
    # Month 4: 4 months ago (NEGATIVE savings, expenses exceed income)
    # Month 5: 5 months ago (positive savings)

    months_data = [
        # (offset, incomes, expenses, budgets)
        # offset 0: Current Month (e.g. Oct 2026)
        (
            0,
            [
                ("Salary", 75000.0, 1, "Monthly tech salary"),
                ("Freelance", 18500.0, 15, "Landing page UI design")
            ],
            [
                ("Rent", 22000.0, 2, "Apartment rent"),
                ("Food", 3200.0, 4, "Whole Foods grocery haul"),
                ("Transport", 1450.0, 7, "Fuel & Metro recharge"),
                ("Entertainment", 2800.0, 10, "Concert tickets & drinks"),
                ("Health", 4500.0, 12, "Dentist checkup & vitamins"),
                ("Shopping", 9200.0, 14, "Mechanical keyboard & monitor arm"),
                ("Food", 2850.0, 18, "Dinner with college friends"),
                ("Others", 1600.0, 21, "Cloud server & domain renewal"),
                ("Transport", 850.0, 24, "Weekend cab rides"),
                ("Food", 1900.0, 25, "Weekly veggies & pantry stock")
            ],
            # Budgets: category -> limit
            # Notice Shopping (9200 / 10000 = 92% -> RED > 85%)
            # Rent (22000 / 25000 = 88% -> RED > 85%)
            # Food (7950 / 12000 = 66% -> ORANGE)
            {
                "Food": 12000.0,
                "Rent": 25000.0,
                "Transport": 5000.0,
                "Entertainment": 6000.0,
                "Shopping": 10000.0,
                "Health": 8000.0,
                "Others": 4000.0
            }
        ),
        # offset 1: 1 month ago (e.g. Sep 2026) - Positive savings
        (
            1,
            [
                ("Salary", 75000.0, 1, "Monthly tech salary"),
                ("Gift", 5000.0, 18, "Birthday gift from family")
            ],
            [
                ("Rent", 22000.0, 2, "Apartment rent"),
                ("Food", 8400.0, 5, "Groceries and meal kit delivery"),
                ("Shopping", 5500.0, 9, "Autumn wardrobe basics"),
                ("Transport", 3100.0, 14, "Commute passes & fuel"),
                ("Entertainment", 3400.0, 20, "Movie night & dining out"),
                ("Health", 1800.0, 23, "Eye exam & lens solution"),
                ("Others", 1200.0, 27, "Software subscriptions")
            ],
            {
                "Food": 12000.0,
                "Rent": 25000.0,
                "Transport": 5000.0,
                "Entertainment": 6000.0,
                "Shopping": 8000.0,
                "Health": 6000.0,
                "Others": 4000.0
            }
        ),
        # offset 2: 2 months ago (e.g. Aug 2026) - NEGATIVE SAVINGS (Expenses > Income)
        (
            2,
            [
                ("Salary", 75000.0, 1, "Monthly tech salary")
            ],
            [
                ("Rent", 22000.0, 2, "Apartment rent"),
                ("Health", 28500.0, 6, "Emergency dental root canal surgery"),
                ("Shopping", 24000.0, 11, "Workstation desk & ergonomic chair"),
                ("Food", 9200.0, 15, "Monthly dining & groceries"),
                ("Transport", 4100.0, 19, "Car servicing & petrol"),
                ("Entertainment", 4500.0, 22, "Weekend club & outing"),
                ("Others", 3200.0, 26, "Annual tax consultant fee")
            ],
            {
                "Food": 12000.0,
                "Rent": 25000.0,
                "Transport": 5000.0,
                "Entertainment": 6000.0,
                "Shopping": 10000.0,
                "Health": 10000.0,
                "Others": 4000.0
            }
        ),
        # offset 3: 3 months ago (e.g. Jul 2026) - Positive savings
        (
            3,
            [
                ("Salary", 75000.0, 1, "Monthly tech salary"),
                ("Freelance", 25000.0, 20, "Full-stack client API integration")
            ],
            [
                ("Rent", 22000.0, 2, "Apartment rent"),
                ("Food", 11300.0, 5, "Summer BBQ supplies & dining"),
                ("Entertainment", 7200.0, 12, "Music festival weekend passes"),
                ("Shopping", 6500.0, 16, "Sneakers and summer apparel"),
                ("Transport", 3800.0, 21, "Fuel and highway tolls"),
                ("Health", 2100.0, 25, "Annual health checkup"),
                ("Others", 2000.0, 28, "Home utilities")
            ],
            {
                "Food": 12000.0,
                "Rent": 25000.0,
                "Transport": 5000.0,
                "Entertainment": 8000.0,
                "Shopping": 8000.0,
                "Health": 6000.0,
                "Others": 4000.0
            }
        ),
        # offset 4: 4 months ago (e.g. Jun 2026) - NEGATIVE SAVINGS (Expenses > Income)
        (
            4,
            [
                ("Salary", 75000.0, 1, "Monthly tech salary")
            ],
            [
                ("Rent", 22000.0, 2, "Apartment rent"),
                ("Shopping", 32000.0, 8, "Smart TV & soundbar for living room"),
                ("Entertainment", 14500.0, 13, "Flight tickets for summer retreat"),
                ("Food", 10200.0, 17, "Restaurants and specialty grocery"),
                ("Transport", 5100.0, 22, "Cab rides during travel"),
                ("Others", 2800.0, 25, "Luggage repair and insurance"),
                ("Health", 1500.0, 27, "Travel vaccinations & first aid")
            ],
            {
                "Food": 12000.0,
                "Rent": 25000.0,
                "Transport": 5000.0,
                "Entertainment": 10000.0,
                "Shopping": 15000.0,
                "Health": 5000.0,
                "Others": 4000.0
            }
        ),
        # offset 5: 5 months ago (e.g. May 2026) - Positive savings
        (
            5,
            [
                ("Salary", 75000.0, 1, "Monthly tech salary"),
                ("Freelance", 12000.0, 14, "Mobile app bug fixes")
            ],
            [
                ("Rent", 22000.0, 2, "Apartment rent"),
                ("Food", 8100.0, 6, "Groceries & organic farmers market"),
                ("Shopping", 4200.0, 10, "Kindle books & kitchen cookware"),
                ("Entertainment", 3600.0, 16, "Escape room & dinner with team"),
                ("Transport", 2900.0, 20, "Fuel & parking permits"),
                ("Health", 1200.0, 24, "Gym membership renewal"),
                ("Others", 1500.0, 27, "Broadband fiber internet")
            ],
            {
                "Food": 12000.0,
                "Rent": 25000.0,
                "Transport": 5000.0,
                "Entertainment": 6000.0,
                "Shopping": 6000.0,
                "Health": 5000.0,
                "Others": 4000.0
            }
        ),
    ]

    for offset, incomes, expenses, budgets in months_data:
        year, month = get_relative_month(today, offset)

        # Insert Incomes
        for cat, amt, day, note in incomes:
            # Ensure day doesn't exceed current day if offset == 0
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
    print("Seed data successfully inserted for user test@spendwise.com!")

if __name__ == '__main__':
    seed_data()
