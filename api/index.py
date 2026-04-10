import sys
import os

# Add project root to path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

from app import app

# Vercel needs the WSGI app exposed as 'app' or 'handler'
handler = app
