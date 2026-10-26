import os
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vercel serverless functions have a read-only filesystem, except for /tmp
IS_VERCEL = bool(os.environ.get('VERCEL'))
DB_DIR = '/tmp' if IS_VERCEL else BASE_DIR
DB_PATH = os.path.join(DB_DIR, 'spendwise.db')
PRESEEDED_DB = os.path.join(BASE_DIR, 'spendwise.db')

def ensure_database_ready():
    """Ensure database exists and is fully read-write in both local and serverless environments."""
    if IS_VERCEL:
        if not os.path.exists(DB_PATH):
            if os.path.exists(PRESEEDED_DB):
                # Use copyfile instead of copy2 so read-only file permissions are not copied
                shutil.copyfile(PRESEEDED_DB, DB_PATH)
            else:
                init_db()
                from seed import seed_data
                seed_data()
        
        # Ensure full read-write permissions on DB_PATH
        try:
            os.chmod(DB_PATH, 0o666)
        except Exception:
            pass

def get_db_connection():
    ensure_database_ready()
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Foreign keys off in serverless to prevent multi-lambda container desync errors
    conn.execute("PRAGMA foreign_keys = OFF;")
    return conn

def init_db():
    if IS_VERCEL and not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    print(f"Database initialized at {DB_PATH}")
