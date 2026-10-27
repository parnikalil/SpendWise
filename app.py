import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, 'backend')

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.app import app, init_db, seed_data

if __name__ == '__main__':
    init_db()
    seed_data()

    port = int(os.environ.get('PORT', 5000))
    print("\n" + "=" * 65)
    print("  SpendWise: B.Tech. Student Edition (Parnika Lilani)")
    print(f"  Local URL: http://127.0.0.1:{port}")
    print("  Student Account: parnika@spendwise.com")
    print("  Password:        test123")
    print("=" * 65 + "\n")

    app.run(host='127.0.0.1', port=port, debug=True)
