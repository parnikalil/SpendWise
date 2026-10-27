import os
import sqlite3

try:
    import libsql
    _HAS_LIBSQL = True
except ImportError:
    _HAS_LIBSQL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Hosted database credentials (set in Vercel Environment Variables)
DATABASE_URL = os.environ.get('TURSO_DATABASE_URL')
AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN')

# Kept so app.py's `from database import DB_PATH` import keeps working.
# In production this path is no longer used for data storage.
DB_PATH = os.path.join(BASE_DIR, 'spendwise.db')


def _use_hosted_db():
    """True when hosted DB credentials are present (production on Vercel)."""
    return bool(DATABASE_URL and AUTH_TOKEN and _HAS_LIBSQL)


def get_db_connection():
    """Return a database connection that works in both environments.

    The returned connection mimics the sqlite3 API (execute, cursor,
    commit, row_factory), so the rest of the app needs no changes.
    """
    if _use_hosted_db():
        conn = libsql.connect(DATABASE_URL, auth_token=AUTH_TOKEN)
        try:
            conn.row_factory = sqlite3.Row
        except Exception:
            pass
        return conn

    # Local development fallback: plain SQLite file
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they do not exist yet (safe to run repeatedly)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
        amount REAL NOT NULL CHECK(amount > 0),
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        limit_amount REAL NOT NULL CHECK(limit_amount >= 0),
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, category, month, year)
    );
    """)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print(f"Database initialized: "
          f"{'hosted Turso DB' if _use_hosted_db() else f'local file at {DB_PATH}'}")
