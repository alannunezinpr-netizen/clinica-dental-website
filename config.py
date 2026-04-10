import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production-please'
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'clinica.db')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '').encode() if os.environ.get('ENCRYPTION_KEY') else None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Auto-enable secure cookies when deployed (Vercel sets VERCEL=1)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true' \
                            or bool(os.environ.get('VERCEL'))
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours
