import sys
import os

# Add the clinica root to the path so we can import app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel calls this WSGI handler
handler = app
