import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL', '')


def get_db():
    """Return a database connection, stored in Flask g if available."""
    try:
        from flask import g
        db = g.get('_database', None)
        if db is None or db.closed:
            db = psycopg2.connect(DATABASE_URL)
            g._database = db
    except RuntimeError:
        # No Flask app context (e.g., running scripts directly)
        db = psycopg2.connect(DATABASE_URL)
    return db


def close_db(db):
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def _pg(sql):
    """Convert SQLite-style ? placeholders to PostgreSQL %s."""
    return sql.replace('?', '%s')


def query_db(sql, args=(), one=False):
    sql = _pg(sql)
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, args if args else None)
    rv = cur.fetchall()
    cur.close()
    result = [dict(row) for row in rv]
    return (result[0] if result else None) if one else result


def execute_db(sql, args=()):
    sql = _pg(sql)
    db = get_db()
    cur = db.cursor()
    stripped = sql.strip().upper()
    if stripped.startswith('INSERT') and 'RETURNING' not in stripped:
        returning_sql = sql.rstrip().rstrip(';') + ' RETURNING id'
        cur.execute(returning_sql, args if args else None)
        row = cur.fetchone()
        db.commit()
        cur.close()
        return row[0] if row else None
    else:
        cur.execute(sql, args if args else None)
        db.commit()
        cur.close()
        return None


def log_activity(user_id, username, action, entity_type=None, entity_id=None, details=None, ip=None):
    execute_db("""
        INSERT INTO activity_log (user_id, username, action, entity_type, entity_id, details, ip_address)
        VALUES (?,?,?,?,?,?,?)
    """, (user_id, username, action, entity_type, entity_id, details, ip))


# ── PostgreSQL Schema ────────────────────────────────────────────────────────

_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'front_desk',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        last_login TEXT,
        login_attempts INTEGER DEFAULT 0,
        locked_until TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        dob TEXT,
        gender TEXT,
        phone TEXT,
        phone_alt TEXT,
        email TEXT,
        address TEXT,
        city TEXT,
        insurance_name TEXT,
        insurance_id TEXT,
        medical_alerts TEXT,
        notes TEXT,
        status TEXT DEFAULT 'active',
        recall_interval INTEGER DEFAULT 6,
        last_recall_date TEXT,
        next_recall_date TEXT,
        created_by INTEGER,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        updated_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )""",
    """CREATE TABLE IF NOT EXISTS emergency_contacts (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        relationship TEXT,
        phone TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )""",
    """CREATE TABLE IF NOT EXISTS appointments (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        dentist_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        duration INTEGER DEFAULT 60,
        reason TEXT,
        status TEXT DEFAULT 'scheduled',
        notes TEXT,
        cancellation_reason TEXT,
        payment_status TEXT DEFAULT 'unpaid',
        created_by INTEGER,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        updated_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (dentist_id) REFERENCES users(id)
    )""",
    """CREATE TABLE IF NOT EXISTS visit_notes (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        appointment_id INTEGER,
        author_id INTEGER NOT NULL,
        title TEXT,
        chief_complaint TEXT,
        clinical_notes TEXT NOT NULL,
        treatment_performed TEXT,
        follow_up_needed INTEGER DEFAULT 0,
        follow_up_notes TEXT,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        updated_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (appointment_id) REFERENCES appointments(id),
        FOREIGN KEY (author_id) REFERENCES users(id)
    )""",
    """CREATE TABLE IF NOT EXISTS treatment_plans (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_by INTEGER,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )""",
    """CREATE TABLE IF NOT EXISTS treatment_items (
        id SERIAL PRIMARY KEY,
        plan_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        tooth TEXT,
        status TEXT DEFAULT 'planned',
        cost_estimate REAL,
        notes TEXT,
        completed_at TEXT,
        FOREIGN KEY (plan_id) REFERENCES treatment_plans(id)
    )""",
    """CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        patient_id INTEGER,
        assigned_to INTEGER,
        created_by INTEGER,
        due_date TEXT,
        priority TEXT DEFAULT 'normal',
        status TEXT DEFAULT 'open',
        notes TEXT,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        updated_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (assigned_to) REFERENCES users(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )""",
    """CREATE TABLE IF NOT EXISTS recalls (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )""",
    """CREATE TABLE IF NOT EXISTS activity_log (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        action TEXT NOT NULL,
        entity_type TEXT,
        entity_id INTEGER,
        details TEXT,
        ip_address TEXT,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""",
    """CREATE TABLE IF NOT EXISTS payment_records (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        appointment_id INTEGER,
        amount REAL DEFAULT 0,
        status TEXT DEFAULT 'unpaid',
        method TEXT,
        notes TEXT,
        created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    )""",
]


def init_db():
    """Create tables and seed initial users if the users table is empty."""
    db = get_db()
    cur = db.cursor()
    for stmt in _SCHEMA:
        cur.execute(stmt)
    db.commit()

    # Seed the three clinic accounts only on first run (empty users table)
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        _seed_initial_users(db, cur)

    cur.close()


def _seed_initial_users(db, cur):
    """Create the three default staff accounts on first deployment."""
    import bcrypt

    def hashpw(pw):
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(12)).decode()

    staff = [
        ('admin',       os.environ.get('ADMIN_EMAIL', 'admin@clinica.pr'),
         hashpw(os.environ.get('ADMIN_PASSWORD', 'Admin2024!')),
         'Administrador Sistema', 'admin'),
        ('dra.berrios', os.environ.get('DENTIST_EMAIL', 'dra.berrios@clinica.pr'),
         hashpw(os.environ.get('DENTIST_PASSWORD', 'Dental2024!')),
         'Dra. Maria I. Berrios Hernandez', 'dentist'),
        ('recepcion',   os.environ.get('RECEP_EMAIL', 'recepcion@clinica.pr'),
         hashpw(os.environ.get('RECEP_PASSWORD', 'Recep2024!')),
         'Recepcionista', 'front_desk'),
    ]
    for u in staff:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, full_name, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            u
        )
    db.commit()
    print("Initial staff accounts created.")
