import os
import sqlite3
import datetime
import calendar
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import DB_PATH, init_db, get_db_connection
from seed import seed_data

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'spendwise-secure-session-key-2026')

EXPENSE_CATEGORIES = ['Food', 'Rent', 'Transport', 'Entertainment', 'Shopping', 'Health', 'Others']
INCOME_CATEGORIES = ['Salary', 'Freelance', 'Gift', 'Others']

CATEGORY_ICONS = {
    'Food': '🍔',
    'Rent': '🏠',
    'Transport': '🚗',
    'Entertainment': '🎬',
    'Shopping': '🛍️',
    'Health': '💊',
    'Others': '📦',
    'Salary': '💼',
    'Freelance': '💻',
    'Gift': '🎁'
}

def get_db():
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    return {
        'current_user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email')
        } if 'user_id' in session else None,
        'expense_categories': EXPENSE_CATEGORIES,
        'income_categories': INCOME_CATEGORIES,
        'category_icons': CATEGORY_ICONS,
        'today_str': datetime.date.today().strftime('%Y-%m-%d'),
        'current_month_str': datetime.date.today().strftime('%Y-%m'),
    }

@app.template_filter('currency')
def currency_filter(value):
    try:
        val = float(value)
        if val.is_integer():
            return f"₹{int(val):,}"
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return "₹0"

@app.template_filter('format_date')
def format_date(value):
    try:
        dt = datetime.datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%d %b %Y')
    except Exception:
        return str(value)

@app.template_filter('month_name')
def month_name_filter(value):
    try:
        dt = datetime.datetime.strptime(str(value), '%Y-%m')
        return dt.strftime('%B %Y')
    except Exception:
        return str(value)

# ----------------- AUTH ROUTES ----------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth.html', active_tab='login', email=email)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(f"Welcome back, {user['name']}!", 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return render_template('auth.html', active_tab='login', email=email)

    return render_template('auth.html', active_tab='login')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash('All fields are required for registration.', 'error')
        return render_template('auth.html', active_tab='register', name=name, email=email)

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return render_template('auth.html', active_tab='register', name=name, email=email)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        flash('An account with this email already exists. Please log in.', 'error')
        return render_template('auth.html', active_tab='login', email=email)

    password_hash = generate_password_hash(password)
    cursor.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, (name, email, password_hash))
    db.commit()
    user_id = cursor.lastrowid

    # Seed default budgets for new user for current month
    today = datetime.date.today()
    default_limits = {
        'Food': 12000.0,
        'Rent': 25000.0,
        'Transport': 5000.0,
        'Entertainment': 6000.0,
        'Shopping': 8000.0,
        'Health': 6000.0,
        'Others': 4000.0
    }
    for cat, lim in default_limits.items():
        cursor.execute("""
            INSERT OR IGNORE INTO budgets (user_id, category, limit_amount, month, year)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, cat, lim, today.month, today.year))
    db.commit()

    session.clear()
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email

    flash(f"Account created successfully! Welcome to SpendWise, {name}.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ----------------- PAGE ROUTES ----------------- #

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user_id = session['user_id']
    today = datetime.date.today()
    current_month_str = today.strftime('%Y-%m')

    # Current month summary
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) as expense
        FROM transactions
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, (user_id, current_month_str))
    month_summary = cursor.fetchone()
    total_income = month_summary['income']
    total_expense = month_summary['expense']
    current_balance = total_income - total_expense

    # Recent 5 transactions
    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 5
    """, (user_id,))
    recent_transactions = cursor.fetchall()

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expense=total_expense,
        current_balance=current_balance,
        recent_transactions=recent_transactions,
        month_label=today.strftime('%B %Y')
    )

@app.route('/transactions')
@login_required
def transactions():
    db = get_db()
    user_id = session['user_id']

    # Filter query parameters
    selected_month = request.args.get('month', '').strip()
    selected_category = request.args.get('category', '').strip()
    selected_type = request.args.get('type', '').strip()

    # Get all distinct months available for this user
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT strftime('%Y-%m', date) as mth
        FROM transactions
        WHERE user_id = ?
        ORDER BY mth DESC
    """, (user_id,))
    available_months = [row['mth'] for row in cursor.fetchall()]

    query = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if selected_month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(selected_month)
    if selected_category:
        query += " AND category = ?"
        params.append(selected_category)
    if selected_type in ['Income', 'Expense']:
        query += " AND type = ?"
        params.append(selected_type)

    query += " ORDER BY date DESC, id DESC"
    cursor.execute(query, params)
    transaction_list = cursor.fetchall()

    return render_template(
        'transactions.html',
        transactions=transaction_list,
        available_months=available_months,
        selected_month=selected_month,
        selected_category=selected_category,
        selected_type=selected_type
    )

@app.route('/budgets')
@login_required
def budgets():
    db = get_db()
    user_id = session['user_id']
    today = datetime.date.today()

    selected_month_param = request.args.get('month', '').strip()
    if selected_month_param:
        try:
            year_val, month_val = map(int, selected_month_param.split('-'))
        except ValueError:
            year_val, month_val = today.year, today.month
    else:
        year_val, month_val = today.year, today.month

    selected_month_str = f"{year_val:04d}-{month_val:02d}"

    # Get expenses by category for selected month
    cursor = db.cursor()
    cursor.execute("""
        SELECT category, SUM(amount) as total_spent
        FROM transactions
        WHERE user_id = ? AND type = 'Expense' AND strftime('%Y-%m', date) = ?
        GROUP BY category
    """, (user_id, selected_month_str))
    spent_map = {row['category']: row['total_spent'] for row in cursor.fetchall()}

    # Get limits set in budgets table for this month/year
    cursor.execute("""
        SELECT category, limit_amount
        FROM budgets
        WHERE user_id = ? AND month = ? AND year = ?
    """, (user_id, month_val, year_val))
    limit_map = {row['category']: row['limit_amount'] for row in cursor.fetchall()}

    # Distinct months list for selector
    cursor.execute("""
        SELECT DISTINCT strftime('%Y-%m', date) as mth
        FROM transactions
        WHERE user_id = ?
        ORDER BY mth DESC
    """, (user_id,))
    available_months = [row['mth'] for row in cursor.fetchall()]
    if selected_month_str not in available_months:
        available_months.insert(0, selected_month_str)

    # Build category card items
    categories_data = []
    total_budget_limit = 0
    total_budget_spent = 0

    for cat in EXPENSE_CATEGORIES:
        limit = limit_map.get(cat, 0.0)
        spent = spent_map.get(cat, 0.0)
        total_budget_limit += limit
        total_budget_spent += spent

        percentage = 0.0
        if limit > 0:
            percentage = round((spent / limit) * 100, 1)

        is_exceeded_85 = percentage > 85.0
        remaining = limit - spent

        categories_data.append({
            'category': cat,
            'icon': CATEGORY_ICONS.get(cat, '📦'),
            'limit': limit,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage,
            'is_exceeded_85': is_exceeded_85
        })

    month_display = datetime.datetime(year_val, month_val, 1).strftime('%B %Y')

    return render_template(
        'budgets.html',
        categories=categories_data,
        selected_month=selected_month_str,
        month_display=month_display,
        year=year_val,
        month=month_val,
        available_months=available_months,
        total_budget_limit=total_budget_limit,
        total_budget_spent=total_budget_spent
    )

@app.route('/history')
@login_required
def history():
    db = get_db()
    user_id = session['user_id']
    today = datetime.date.today()

    # Generate list of last 6 months relative to today
    months_keys = []
    cur_y = today.year
    cur_m = today.month
    for i in range(6):
        m = cur_m - i
        y = cur_y
        while m <= 0:
            m += 12
            y -= 1
        months_keys.append(f"{y:04d}-{m:02d}")

    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', date) as mth,
            SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as total_expense
        FROM transactions
        WHERE user_id = ?
        GROUP BY mth
    """, (user_id,))
    month_data_map = {row['mth']: row for row in cursor.fetchall()}

    history_rows = []
    total_savings_all = 0
    total_income_all = 0
    total_expense_all = 0

    for m_key in months_keys:
        row = month_data_map.get(m_key)
        inc = row['total_income'] if row else 0.0
        exp = row['total_expense'] if row else 0.0
        savings = inc - exp
        total_savings_all += savings
        total_income_all += inc
        total_expense_all += exp

        dt = datetime.datetime.strptime(m_key, '%Y-%m')
        m_label = dt.strftime('%B %Y')

        history_rows.append({
            'month_key': m_key,
            'month_label': m_label,
            'income': inc,
            'expense': exp,
            'savings': savings,
            'is_positive': savings >= 0
        })

    return render_template(
        'history.html',
        history_rows=history_rows,
        total_income_all=total_income_all,
        total_expense_all=total_expense_all,
        total_savings_all=total_savings_all
    )

# ----------------- JSON API ROUTES ----------------- #

@app.route('/api/dashboard')
@login_required
def api_dashboard():
    db = get_db()
    user_id = session['user_id']
    today = datetime.date.today()
    current_month_str = today.strftime('%Y-%m')

    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) as expense
        FROM transactions
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    """, (user_id, current_month_str))
    res = cursor.fetchone()
    inc = res['income']
    exp = res['expense']

    cursor.execute("""
        SELECT id, type, amount, category, date, note
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 5
    """, (user_id,))
    recent = [dict(r) for r in cursor.fetchall()]

    return jsonify({
        'success': True,
        'summary': {
            'income': inc,
            'expense': exp,
            'balance': inc - exp,
            'month': today.strftime('%B %Y')
        },
        'recent_transactions': recent
    })

@app.route('/api/charts')
@login_required
def api_charts():
    db = get_db()
    user_id = session['user_id']
    today = datetime.date.today()
    current_month_str = today.strftime('%Y-%m')

    cursor = db.cursor()

    # 1. Expense Breakdown by Category for this month
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'Expense' AND strftime('%Y-%m', date) = ?
        GROUP BY category
        ORDER BY total DESC
    """, (user_id, current_month_str))
    cat_rows = cursor.fetchall()

    expense_labels = [r['category'] for r in cat_rows]
    expense_data = [float(r['total']) for r in cat_rows]

    # Warm orange palette as required
    orange_palette = [
        '#F97316', # Primary orange
        '#FB923C', # Light orange
        '#FDBA74', # Soft peach orange
        '#FED7AA', # Very soft orange
        '#EA580C', # Deep burnt orange
        '#C2410C', # Dark amber orange
        '#9A3412', # Deep rust orange
    ]

    # 2. Income vs Expense for last 6 months (chronological order)
    months_keys = []
    cur_y = today.year
    cur_m = today.month
    for i in range(5, -1, -1): # Chronological: 5 months ago to current month
        m = cur_m - i
        y = cur_y
        while m <= 0:
            m += 12
            y -= 1
        months_keys.append(f"{y:04d}-{m:02d}")

    cursor.execute("""
        SELECT 
            strftime('%Y-%m', date) as mth,
            SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as inc,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as exp
        FROM transactions
        WHERE user_id = ?
        GROUP BY mth
    """, (user_id,))
    monthly_map = {r['mth']: r for r in cursor.fetchall()}

    history_labels = []
    history_income = []
    history_expense = []

    for m_key in months_keys:
        dt = datetime.datetime.strptime(m_key, '%Y-%m')
        history_labels.append(dt.strftime('%b %Y'))
        m_data = monthly_map.get(m_key)
        history_income.append(float(m_data['inc']) if m_data else 0.0)
        history_expense.append(float(m_data['exp']) if m_data else 0.0)

    return jsonify({
        'success': True,
        'expense_chart': {
            'labels': expense_labels,
            'data': expense_data,
            'colors': orange_palette[:len(expense_labels)]
        },
        'history_chart': {
            'labels': history_labels,
            'income': history_income,
            'expense': history_expense
        }
    })

@app.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json(silent=True) or request.form
    user_id = session['user_id']

    tx_type = data.get('type', '').strip()
    amount_str = data.get('amount', '')
    category = data.get('category', '').strip()
    date_str = data.get('date', '').strip()
    note = data.get('note', '').strip()

    # Validation
    if tx_type not in ['Income', 'Expense']:
        return jsonify({'success': False, 'error': 'Type must be Income or Expense.'}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be a positive number.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Please enter a valid numeric amount.'}), 400

    if not date_str:
        return jsonify({'success': False, 'error': 'Date is required.'}), 400

    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format (must be YYYY-MM-DD).'}), 400

    valid_categories = EXPENSE_CATEGORIES if tx_type == 'Expense' else INCOME_CATEGORIES
    if not category or category not in valid_categories:
        return jsonify({'success': False, 'error': f"Category '{category}' is invalid for {tx_type}."}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, type, amount, category, date, note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, tx_type, amount, category, date_str, note))
    db.commit()
    new_id = cursor.lastrowid

    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'success': True,
            'message': 'Transaction added successfully!',
            'transaction': {
                'id': new_id,
                'type': tx_type,
                'amount': amount,
                'category': category,
                'date': date_str,
                'note': note
            }
        })
    flash('Transaction added successfully!', 'success')
    return redirect(request.referrer or url_for('transactions'))

@app.route('/api/transactions/<int:tx_id>', methods=['GET'])
@login_required
def get_transaction(tx_id):
    db = get_db()
    user_id = session['user_id']
    cursor = db.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    tx = cursor.fetchone()
    if not tx:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    return jsonify({'success': True, 'transaction': dict(tx)})

@app.route('/api/transactions/<int:tx_id>', methods=['PUT', 'POST'])
@login_required
def update_transaction(tx_id):
    db = get_db()
    user_id = session['user_id']
    cursor = db.cursor()

    cursor.execute("SELECT id FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    if not cursor.fetchone():
        return jsonify({'success': False, 'error': 'Transaction not found.'}), 404

    data = request.get_json(silent=True) or request.form

    tx_type = data.get('type', '').strip()
    amount_str = data.get('amount', '')
    category = data.get('category', '').strip()
    date_str = data.get('date', '').strip()
    note = data.get('note', '').strip()

    if tx_type not in ['Income', 'Expense']:
        return jsonify({'success': False, 'error': 'Type must be Income or Expense.'}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be a positive number.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount.'}), 400

    if not date_str:
        return jsonify({'success': False, 'error': 'Date is required.'}), 400

    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format.'}), 400

    valid_categories = EXPENSE_CATEGORIES if tx_type == 'Expense' else INCOME_CATEGORIES
    if not category or category not in valid_categories:
        return jsonify({'success': False, 'error': f"Category '{category}' is invalid for {tx_type}."}), 400

    cursor.execute("""
        UPDATE transactions
        SET type = ?, amount = ?, category = ?, date = ?, note = ?
        WHERE id = ? AND user_id = ?
    """, (tx_type, amount, category, date_str, note, tx_id, user_id))
    db.commit()

    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'success': True, 'message': 'Transaction updated successfully!'})
    flash('Transaction updated successfully!', 'success')
    return redirect(request.referrer or url_for('transactions'))

@app.route('/api/transactions/<int:tx_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_transaction(tx_id):
    db = get_db()
    user_id = session['user_id']
    cursor = db.cursor()

    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({'success': False, 'error': 'Transaction not found.'}), 404

    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'success': True, 'message': 'Transaction deleted successfully.'})
    flash('Transaction deleted successfully.', 'info')
    return redirect(request.referrer or url_for('transactions'))

@app.route('/api/budgets', methods=['POST'])
@login_required
def update_budget():
    data = request.get_json(silent=True) or request.form
    user_id = session['user_id']
    today = datetime.date.today()

    category = data.get('category', '').strip()
    limit_str = data.get('limit', data.get('limit_amount', ''))
    month = int(data.get('month', today.month))
    year = int(data.get('year', today.year))

    if category not in EXPENSE_CATEGORIES:
        return jsonify({'success': False, 'error': 'Invalid expense category.'}), 400

    try:
        limit_amount = float(limit_str)
        if limit_amount < 0:
            return jsonify({'success': False, 'error': 'Budget limit cannot be negative.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Limit must be a valid number.'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO budgets (user_id, category, limit_amount, month, year)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, category, month, year)
        DO UPDATE SET limit_amount = excluded.limit_amount
    """, (user_id, category, limit_amount, month, year))
    db.commit()

    return jsonify({
        'success': True,
        'message': f"Budget limit for {category} updated to ₹{limit_amount:,.2f}",
        'category': category,
        'limit_amount': limit_amount
    })

# ----------------- MAIN APP RUNNER ----------------- #

if __name__ == '__main__':
    # Initialize DB and Seed Data
    init_db()
    seed_data()

    port = int(os.environ.get('PORT', 5000))
    print("\n" + "=" * 65)
    print("  🚀 SpendWise - Personal Finance Tracker")
    print(f"  🌐 Application URL: http://127.0.0.1:{port}")
    print("  👤 Demo Account:    test@spendwise.com")
    print("  🔑 Demo Password:   test123")
    print("=" * 65 + "\n")

    app.run(host='127.0.0.1', port=port, debug=True)
