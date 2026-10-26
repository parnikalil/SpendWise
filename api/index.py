import sys
import os

# Add root folder to sys.path so app modules can be discovered by Vercel's Python runtime
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from database import ensure_database_ready

# Ensure DB is populated into /tmp if running serverless on Vercel
ensure_database_ready()
