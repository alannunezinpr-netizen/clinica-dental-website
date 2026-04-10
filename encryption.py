import os
from cryptography.fernet import Fernet

_fernet = None

def get_fernet():
    global _fernet
    if _fernet is None:
        key = os.environ.get('ENCRYPTION_KEY', '').encode()
        if key:
            _fernet = Fernet(key)
    return _fernet

def encrypt_field(value):
    if not value:
        return value
    f = get_fernet()
    if not f:
        return value  # no encryption key set, store as-is
    return f.encrypt(value.encode()).decode()

def decrypt_field(value):
    if not value:
        return value
    f = get_fernet()
    if not f:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value  # fallback if decryption fails
