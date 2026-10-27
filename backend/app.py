import os
import sys
import sqlite3
import datetime
import calendar
import json
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

# Handle database imports
try:
    from backend.database import DB_PATH, init_db, get_db_connection
    from backend.seed import seed_data
except ImportError:
    from database import DB_PATH, init_db, get_db_connection
    from seed import seed_data

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, 'templates'),
    static_folder=os.path.join(FRONTEND_DIR, 'static'),
    static_url_path='/static'
)

app.secret_key = os.environ.get('SECRET_KEY', 'spendwise-student-secret-2026')

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=bool(os.environ.get('VERCEL'))
)

# Categories tailored specifically for B.Tech student life
EXPENSE_CATEGORIES = [
    'Hostel Fees',
    'Food',
    'Fuel',
    'Travel',
    'Stationery',
    'Phone Recharge',
    'Tech & Books',
    'Entertainment',
    'Others'
]

INCOME_CATEGORIES = [
    'Allowance',
    'Internship Stipend',
    'Freelance',
    'Scholarship',
    'Others'
]

CATEGORY_ICONS = {
    'Hostel Fees': '🏠',
    'Food': '🍔',
    'Fuel': '⛽',
    'Travel': '🚆',
    'Stationery': '📚',
    'Phone Recharge': '📱',
    'Tech & Books': '💻',
    'Entertainment': '🎬',
    'Others': '📦',
    'Allowance': '💵',
    'Internship Stipend': '💼',
    'Freelance': '💻',
    'Scholarship': '🎓'
}

DEFAULT_BUDGETS = {
    'Hostel Fees': 12000.0,
    'Food': 5500.0,
    'Fuel': 2000.0,
    'Travel': 2500.0,
    'Stationery': 1500.0,
    'Phone Recharge': 1000.0,
    'Tech & Books': 3000.0,
    'Entertainment': 2000.0,
    'Others': 1500.0
}

def normalize_date(date_str):
    """Normalize user input dates (DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY) into ISO YYYY-MM-DD."""
    if not date_str:
        return datetime.date.today().strftime('%Y-%m-%d')
    date_str = str(date_str).strip()
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%m/%d/%Y'):
        try:
            return datetime.datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def get_db():
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.before_request
def ensure_user_in_db():
    """Ensure logged-in user exists in local container DB (prevents container desync)."""
    user_id = session.get('user_id')
    if user_id:
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, name, email, password_hash)
                    VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    session.get('user_name', 'Student User'),
                    session.get('user_email', f'user{user_id}@spendwise.com'),
                    session.get('user_hash', '')
                ))
                db.commit()
        except Exception:
            pass

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            flash('Please log in to access your student dashboard.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_user_transactions(user_id):
    """Retrieve all transactions for a user sorted newest first."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, type, amount, category, date, note
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (user_id,))
    return [dict(r) for r in cursor.fetchall()]

def get_user_budgets(user_id, month=None, year=None):
    """Retrieve budget limits for a user."""
    today = datetime.date.today()
    m = month or today.month
    y = year or today.year
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT category, limit_amount
        FROM budgets
        WHERE user_id = ? AND month = ? AND year = ?
    """, (user_id, m, y))
    rows = cursor.fetchall()
    limit_map = {r['category']: float(r['limit_amount']) for r in rows}
    
    # Fill in defaults if not explicitly set
    for cat, default_lim in DEFAULT_BUDGETS.items():
        if cat not in limit_map:
            limit_map[cat] = default_lim
    return limit_map

@app.context_processor
def inject_globals():
    user_info = None
    initial_transactions = []
    initial_budgets = {}

    if 'user_id' in session:
        user_info = {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email')
        }
        try:
            initial_transactions = get_user_transactions(session['user_id'])
            initial_budgets = get_user_budgets(session['user_id'])
        except Exception:
            initial_transactions = []
            initial_budgets = DEFAULT_BUDGETS

    return {
        'current_user': user_info,
        'expense_categories': EXPENSE_CATEGORIES,
        'income_categories': INCOME_CATEGORIES,
        'category_icons': CATEGORY_ICONS,
        'default_budgets': DEFAULT_BUDGETS,
        'today_str': datetime.date.today().strftime('%Y-%m-%d'),
        'current_month_str': datetime.date.today().strftime('%Y-%m'),
        'initial_data_json': json.dumps({
            'user': user_info,
            'transactions': initial_transactions,
            'budgets': initial_budgets
        })
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
        norm = normalize_date(value)
        if norm:
            dt = datetime.datetime.strptime(norm, '%Y-%m-%d')
            return dt.strftime('%d %b %Y')
        return str(value)
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
            session['user_hash'] = user['password_hash']
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

    # Seed default student budgets for new user for current month
    today = datetime.date.today()
    for cat, lim in DEFAULT_BUDGETS.items():
        cursor.execute("""
            INSERT OR IGNORE INTO budgets (user_id, category, limit_amount, month, year)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, cat, lim, today.month, today.year))
    db.commit()

    session.clear()
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email
    session['user_hash'] = password_hash

    flash(f"Welcome to SpendWise, {name}! Your student finance tracker is ready.", 'success')
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
    today = datetime.date.today()
    user_id = session['user_id']
    transactions = get_user_transactions(user_id)
    current_month_str = today.strftime('%Y-%m')

    # Calculate month summary safely from user's transactions
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'Income' and str(t['date']).startswith(current_month_str))
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'Expense' and str(t['date']).startswith(current_month_str))
    current_balance = total_income - total_expense

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expense=total_expense,
        current_balance=current_balance,
        recent_transactions=transactions[:5],
        month_label=today.strftime('%B %Y')
    )

@app.route('/transactions')
@login_required
def transactions():
    db = get_db()
    user_id = session['user_id']
    all_txs = get_user_transactions(user_id)

    # Distinct months
    available_months = sorted(list(set(str(t['date'])[:7] for t in all_txs if t.get('date'))), reverse=True)
    if not available_months:
        available_months = [datetime.date.today().strftime('%Y-%m')]

    selected_month = request.args.get('month', '').strip()
    selected_category = request.args.get('category', '').strip()
    selected_type = request.args.get('type', '').strip()

    filtered = all_txs
    if selected_month:
        filtered = [t for t in filtered if str(t['date']).startswith(selected_month)]
    if selected_category:
        filtered = [t for t in filtered if t['category'] == selected_category]
    if selected_type in ['Income', 'Expense']:
        filtered = [t for t in filtered if t['type'] == selected_type]

    return render_template(
        'transactions.html',
        transactions=filtered,
        available_months=available_months,
        selected_month=selected_month,
        selected_category=selected_category,
        selected_type=selected_type
    )

@app.route('/budgets')
@login_required
def budgets():
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

    transactions = get_user_transactions(user_id)
    month_expenses = [t for t in transactions if t['type'] == 'Expense' and str(t['date']).startswith(selected_month_str)]

    spent_map = {}
    for t in month_expenses:
        spent_map[t['category']] = spent_map.get(t['category'], 0.0) + float(t['amount'])

    limit_map = get_user_budgets(user_id, month=month_val, year=year_val)

    available_months = sorted(list(set(str(t['date'])[:7] for t in transactions if t.get('date'))), reverse=True)
    if selected_month_str not in available_months:
        available_months.insert(0, selected_month_str)

    categories_data = []
    total_budget_limit = 0.0
    total_budget_spent = 0.0

    for cat in EXPENSE_CATEGORIES:
        limit = limit_map.get(cat, DEFAULT_BUDGETS.get(cat, 0.0))
        spent = spent_map.get(cat, 0.0)
        total_budget_limit += limit
        total_budget_spent += spent

        percentage = round((spent / limit) * 100, 1) if limit > 0 else 0.0
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
    user_id = session['user_id']
    today = datetime.date.today()
    transactions = get_user_transactions(user_id)

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

    history_rows = []
    total_savings_all = 0.0
    total_income_all = 0.0
    total_expense_all = 0.0

    for m_key in months_keys:
        m_inc = sum(t['amount'] for t in transactions if t['type'] == 'Income' and str(t['date']).startswith(m_key))
        m_exp = sum(t['amount'] for t in transactions if t['type'] == 'Expense' and str(t['date']).startswith(m_key))
        savings = m_inc - m_exp

        total_savings_all += savings
        total_income_all += m_inc
        total_expense_all += m_exp

        dt = datetime.datetime.strptime(m_key, '%Y-%m')
        m_label = dt.strftime('%B %Y')

        history_rows.append({
            'month_key': m_key,
            'month_label': m_label,
            'income': m_inc,
            'expense': m_exp,
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

@app.route('/api/sync', methods=['POST'])
@login_required
def api_sync():
    """Two-way sync endpoint: syncs client-side transactions & budgets with server."""
    data = request.get_json(silent=True) or {}
    user_id = session['user_id']
    client_txs = data.get('transactions')
    client_budgets = data.get('budgets')

    db = get_db()
    cursor = db.cursor()

    if client_txs is not None and isinstance(client_txs, list):
        # Update server DB with client transactions
        cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        for tx in client_txs:
            t_type = tx.get('type')
            t_amt = float(tx.get('amount', 0))
            t_cat = tx.get('category')
            t_date = normalize_date(tx.get('date'))
            t_note = tx.get('note', '')
            if t_type in ['Income', 'Expense'] and t_amt > 0 and t_cat and t_date:
                cursor.execute("""
                    INSERT INTO transactions (user_id, type, amount, category, date, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, t_type, t_amt, t_cat, t_date, t_note))
        db.commit()

    if client_budgets is not None and isinstance(client_budgets, dict):
        today = datetime.date.today()
        for cat, lim in client_budgets.items():
            try:
                cursor.execute("""
                    INSERT INTO budgets (user_id, category, limit_amount, month, year)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, category, month, year)
                    DO UPDATE SET limit_amount = excluded.limit_amount
                """, (user_id, cat, float(lim), today.month, today.year))
            except Exception:
                pass
        db.commit()

    latest_txs = get_user_transactions(user_id)
    latest_budgets = get_user_budgets(user_id)

    return jsonify({
        'success': True,
        'transactions': latest_txs,
        'budgets': latest_budgets
    })

@app.route('/api/dashboard')
@login_required
def api_dashboard():
    user_id = session['user_id']
    today = datetime.date.today()
    current_month_str = today.strftime('%Y-%m')
    transactions = get_user_transactions(user_id)

    inc = sum(t['amount'] for t in transactions if t['type'] == 'Income' and str(t['date']).startswith(current_month_str))
    exp = sum(t['amount'] for t in transactions if t['type'] == 'Expense' and str(t['date']).startswith(current_month_str))

    return jsonify({
        'success': True,
        'summary': {
            'income': inc,
            'expense': exp,
            'balance': inc - exp,
            'month': today.strftime('%B %Y')
        },
        'recent_transactions': transactions[:5]
    })

@app.route('/api/charts')
@login_required
def api_charts():
    user_id = session['user_id']
    today = datetime.date.today()
    current_month_str = today.strftime('%Y-%m')
    transactions = get_user_transactions(user_id)

    # 1. Expense Breakdown by Category for this month
    month_expenses = [t for t in transactions if t['type'] == 'Expense' and str(t['date']).startswith(current_month_str)]
    cat_map = {}
    for t in month_expenses:
        cat_map[t['category']] = cat_map.get(t['category'], 0.0) + float(t['amount'])

    sorted_cats = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
    expense_labels = [c[0] for c in sorted_cats]
    expense_data = [c[1] for c in sorted_cats]

    orange_palette = [
        '#F97316', '#FB923C', '#FDBA74', '#FED7AA',
        '#EA580C', '#C2410C', '#9A3412', '#FF7A00', '#D97706'
    ]

    # 2. Income vs Expense for last 6 months (chronological order)
    months_keys = []
    cur_y = today.year
    cur_m = today.month
    for i in range(5, -1, -1):
        m = cur_m - i
        y = cur_y
        while m <= 0:
            m += 12
            y -= 1
        months_keys.append(f"{y:04d}-{m:02d}")

    history_labels = []
    history_income = []
    history_expense = []

    for m_key in months_keys:
        dt = datetime.datetime.strptime(m_key, '%Y-%m')
        history_labels.append(dt.strftime('%b %Y'))
        m_inc = sum(t['amount'] for t in transactions if t['type'] == 'Income' and str(t['date']).startswith(m_key))
        m_exp = sum(t['amount'] for t in transactions if t['type'] == 'Expense' and str(t['date']).startswith(m_key))
        history_income.append(m_inc)
        history_expense.append(m_exp)

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
    raw_date = data.get('date', '').strip()
    note = data.get('note', '').strip()

    if tx_type not in ['Income', 'Expense']:
        return jsonify({'success': False, 'error': 'Type must be Income or Expense.'}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be a positive number.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Please enter a valid numeric amount.'}), 400

    date_str = normalize_date(raw_date)
    if not date_str:
        return jsonify({'success': False, 'error': f"Invalid date: '{raw_date}'."}), 400

    valid_categories = EXPENSE_CATEGORIES if tx_type == 'Expense' else INCOME_CATEGORIES
    if not category or category not in valid_categories:
        return jsonify({'success': False, 'error': f"Category '{category}' is invalid for {tx_type}."}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, category, date, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, tx_type, amount, category, date_str, note))
        db.commit()
        new_id = cursor.lastrowid
    except Exception as e:
        return jsonify({'success': False, 'error': f"Database error: {str(e)}"}), 500

    saved_tx = {
        'id': new_id,
        'type': tx_type,
        'amount': amount,
        'category': category,
        'date': date_str,
        'note': note
    }

    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'success': True,
            'message': 'Transaction added successfully!',
            'transaction': saved_tx
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
    raw_date = data.get('date', '').strip()
    note = data.get('note', '').strip()

    if tx_type not in ['Income', 'Expense']:
        return jsonify({'success': False, 'error': 'Type must be Income or Expense.'}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be a positive number.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount.'}), 400

    date_str = normalize_date(raw_date)
    if not date_str:
        return jsonify({'success': False, 'error': 'Invalid date format.'}), 400

    valid_categories = EXPENSE_CATEGORIES if tx_type == 'Expense' else INCOME_CATEGORIES
    if not category or category not in valid_categories:
        return jsonify({'success': False, 'error': f"Category '{category}' is invalid for {tx_type}."}), 400

    try:
        cursor.execute("""
            UPDATE transactions
            SET type = ?, amount = ?, category = ?, date = ?, note = ?
            WHERE id = ? AND user_id = ?
        """, (tx_type, amount, category, date_str, note, tx_id, user_id))
        db.commit()
    except Exception as e:
        return jsonify({'success': False, 'error': f"Update error: {str(e)}"}), 500

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

    try:
        cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        db.commit()
    except Exception as e:
        return jsonify({'success': False, 'error': f"Delete error: {str(e)}"}), 500

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

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO budgets (user_id, category, limit_amount, month, year)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, category, month, year)
            DO UPDATE SET limit_amount = excluded.limit_amount
        """, (user_id, category, limit_amount, month, year))
        db.commit()
    except Exception as e:
        return jsonify({'success': False, 'error': f"Budget error: {str(e)}"}), 500

    return jsonify({
        'success': True,
        'message': f"Budget limit for {category} updated to ₹{limit_amount:,.2f}",
        'category': category,
        'limit_amount': limit_amount
    })

# ----------------- MAIN APP RUNNER ----------------- #

if __name__ == '__main__':
    init_db()
    seed_data()

    port = int(os.environ.get('PORT', 5000))
    print("\n" + "=" * 65)
    print("  🚀 SpendWise — B.Tech. Student Edition (Parnika Lilani)")
    print(f"  🌐 Application URL: http://127.0.0.1:{port}")
    print("  👤 Student Account: parnika@spendwise.com")
    print("  🔑 Password:        test123")
    print("=" * 65 + "\n")

    app.run(host='127.0.0.1', port=port, debug=True)
