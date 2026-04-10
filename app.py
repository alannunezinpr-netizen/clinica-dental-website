import os
import secrets
from datetime import datetime, date, timedelta
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, jsonify, abort, g)
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bcrypt
from database import init_db, query_db, execute_db, log_activity, get_db, close_db
from encryption import encrypt_field, decrypt_field
from decorators import role_required, admin_required
from config import Config
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder.'
login_manager.login_message_category = 'warning'

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri="memory://"
)

with app.app_context():
    init_db()

@app.teardown_appcontext
def teardown_db(exception):
    from flask import g
    db = g.pop('_database', None)
    close_db(db)

class User(UserMixin):
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.full_name = row['full_name']
        self.role = row['role']
        self.email = row['email']
        self.is_active_account = bool(row['is_active'])

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.is_active_account

@login_manager.user_loader
def load_user(user_id):
    row = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    return User(row) if row else None

def generate_csrf():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf():
    token = session.get('_csrf_token')
    form_token = request.form.get('_csrf_token')
    if not token or token != form_token:
        abort(400)

app.jinja_env.globals['csrf_token'] = generate_csrf

def today_str():
    return date.today().isoformat()

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_all_dentists():
    return query_db("SELECT id, full_name FROM users WHERE role='dentist' AND is_active=1 ORDER BY full_name")

def get_all_staff():
    return query_db("SELECT id, full_name, role FROM users WHERE is_active=1 ORDER BY full_name")

STATUS_COLORS = {
    'scheduled': 'blue', 'confirmed': 'teal', 'checked_in': 'purple',
    'completed': 'green', 'cancelled': 'gray', 'no_show': 'red',
    'active': 'green', 'inactive': 'gray', 'open': 'blue', 'in_progress': 'amber',
    'done': 'green', 'pending': 'amber', 'contacted': 'blue', 'overdue': 'red',
    'unpaid': 'red', 'partial': 'amber', 'paid': 'green',
}
app.jinja_env.globals['STATUS_COLORS'] = STATUS_COLORS

# AUTH
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        if not username or not password:
            error = 'Por favor ingresa usuario y contraseña.'
        else:
            user_row = query_db("SELECT * FROM users WHERE lower(username)=?", (username,), one=True)
            if user_row:
                if user_row['locked_until']:
                    lock_time = datetime.fromisoformat(user_row['locked_until'])
                    if datetime.now() < lock_time:
                        remaining = int((lock_time - datetime.now()).total_seconds() / 60) + 1
                        error = f'Cuenta bloqueada. Intenta en {remaining} minutos.'
                        log_activity(user_row['id'], username, 'login_blocked', ip=request.remote_addr)
                    else:
                        execute_db("UPDATE users SET login_attempts=0, locked_until=NULL WHERE id=?", (user_row['id'],))
                        user_row = query_db("SELECT * FROM users WHERE id=?", (user_row['id'],), one=True)
                if not error:
                    if not user_row['is_active']:
                        error = 'Esta cuenta está desactivada.'
                    elif bcrypt.checkpw(password.encode(), user_row['password_hash'].encode()):
                        execute_db("UPDATE users SET login_attempts=0, locked_until=NULL, last_login=? WHERE id=?",
                                   (now_str(), user_row['id']))
                        login_user(User(user_row), remember=True)
                        log_activity(user_row['id'], username, 'login', ip=request.remote_addr)
                        return redirect(request.args.get('next') or url_for('dashboard'))
                    else:
                        attempts = (user_row['login_attempts'] or 0) + 1
                        if attempts >= 5:
                            locked_until = (datetime.now() + timedelta(minutes=15)).isoformat()
                            execute_db("UPDATE users SET login_attempts=?, locked_until=? WHERE id=?",
                                       (attempts, locked_until, user_row['id']))
                            error = 'Demasiados intentos. Cuenta bloqueada por 15 minutos.'
                        else:
                            execute_db("UPDATE users SET login_attempts=? WHERE id=?", (attempts, user_row['id']))
                            error = f'Credenciales incorrectas. ({attempts}/5 intentos)'
                        log_activity(user_row['id'], username, 'login_failed', ip=request.remote_addr)
            else:
                error = 'Credenciales incorrectas.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, current_user.username, 'logout', ip=request.remote_addr)
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

# DASHBOARD
@app.route('/')
@login_required
def dashboard():
    today = today_str()
    today_appts = query_db("""
        SELECT a.*, p.first_name, p.last_name, p.phone, p.medical_alerts, u.full_name as dentist_name
        FROM appointments a JOIN patients p ON a.patient_id=p.id JOIN users u ON a.dentist_id=u.id
        WHERE a.date=? ORDER BY a.time
    """, (today,))
    total_patients = query_db("SELECT COUNT(*) as n FROM patients WHERE status='active'", one=True)['n']
    today_count = query_db("SELECT COUNT(*) as n FROM appointments WHERE date=?", (today,), one=True)['n']
    pending_tasks = query_db("SELECT COUNT(*) as n FROM tasks WHERE status != 'done' AND (assigned_to=? OR assigned_to IS NULL)", (current_user.id,), one=True)['n']
    overdue_recalls_count = query_db("SELECT COUNT(*) as n FROM recalls WHERE due_date <= ? AND status IN ('pending','overdue')", (today,), one=True)['n']
    overdue_recalls = query_db("""
        SELECT r.*, p.first_name, p.last_name, p.phone FROM recalls r JOIN patients p ON r.patient_id=p.id
        WHERE r.due_date <= ? AND r.status IN ('pending', 'overdue') ORDER BY r.due_date LIMIT 8
    """, (today,))
    my_tasks = query_db("""
        SELECT t.*, p.first_name, p.last_name FROM tasks t LEFT JOIN patients p ON t.patient_id=p.id
        WHERE t.status != 'done' AND t.assigned_to=?
        ORDER BY CASE t.priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, t.due_date
        LIMIT 8
    """, (current_user.id,))
    upcoming = query_db("""
        SELECT a.*, p.first_name, p.last_name, u.full_name as dentist_name
        FROM appointments a JOIN patients p ON a.patient_id=p.id JOIN users u ON a.dentist_id=u.id
        WHERE a.date > ? AND a.date <= ? AND a.status NOT IN ('cancelled','no_show')
        ORDER BY a.date, a.time LIMIT 8
    """, (today, (date.today() + timedelta(days=4)).isoformat()))
    activity = query_db("SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 10")
    today_appts_list = []
    for a in today_appts:
        a = dict(a)
        a['medical_alerts'] = decrypt_field(a['medical_alerts'])
        today_appts_list.append(a)
    return render_template('dashboard.html',
        today_appts=today_appts_list, total_patients=total_patients, today_count=today_count,
        pending_tasks=pending_tasks, overdue_recalls_count=overdue_recalls_count,
        overdue_recalls=overdue_recalls, my_tasks=my_tasks, upcoming=upcoming,
        activity=activity, today=today)

# PATIENTS
@app.route('/patients')
@login_required
def patients_list():
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'active')
    recall_filter = request.args.get('recall', '')
    sql = """
        SELECT p.*,
               (SELECT MAX(a.date) FROM appointments a WHERE a.patient_id=p.id AND a.status='completed') as last_visit,
               (SELECT MIN(a.date) FROM appointments a WHERE a.patient_id=p.id AND a.status='scheduled' AND a.date >= ?) as next_appt
        FROM patients p WHERE 1=1
    """
    params = [today_str()]
    if status_filter:
        sql += " AND p.status=?"; params.append(status_filter)
    if q:
        sql += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR p.phone LIKE ? OR p.phone_alt LIKE ?)"
        pq = f'%{q}%'; params += [pq, pq, pq, pq]
    if recall_filter == 'due':
        sql += " AND p.next_recall_date <= ?"; params.append(today_str())
    sql += " ORDER BY p.last_name, p.first_name"
    patients = query_db(sql, params)
    result = []
    for p in patients:
        p = dict(p); p['medical_alerts'] = decrypt_field(p['medical_alerts']); result.append(p)
    return render_template('patients/list.html', patients=result, q=q, status_filter=status_filter, recall_filter=recall_filter)

@app.route('/patients/new', methods=['GET', 'POST'])
@login_required
def patient_new():
    if request.method == 'POST':
        validate_csrf()
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        if not first or not last:
            flash('Nombre y apellido son requeridos.', 'error')
            return render_template('patients/form.html', patient=request.form, action='new', ec={})
        medical_alerts = encrypt_field(request.form.get('medical_alerts', '').strip())
        recall_interval = int(request.form.get('recall_interval', 6))
        next_recall = (date.today() + timedelta(days=recall_interval*30)).isoformat()
        pid = execute_db("""
            INSERT INTO patients (first_name, last_name, dob, gender, phone, phone_alt, email,
                address, city, insurance_name, insurance_id, medical_alerts, notes,
                recall_interval, next_recall_date, created_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (first, last, request.form.get('dob'), request.form.get('gender'),
              request.form.get('phone','').strip(), request.form.get('phone_alt','').strip(),
              request.form.get('email','').strip(), request.form.get('address','').strip(),
              request.form.get('city','').strip(), request.form.get('insurance_name','').strip(),
              request.form.get('insurance_id','').strip(), medical_alerts,
              request.form.get('notes','').strip(), recall_interval, next_recall, current_user.id))
        ec_name = request.form.get('ec_name', '').strip()
        if ec_name:
            execute_db("INSERT INTO emergency_contacts (patient_id, name, relationship, phone) VALUES (?,?,?,?)",
                (pid, ec_name, request.form.get('ec_relationship',''), request.form.get('ec_phone','')))
        log_activity(current_user.id, current_user.username, 'patient_created', 'patient', pid, f'{first} {last}', request.remote_addr)
        flash(f'Paciente {first} {last} registrado exitosamente.', 'success')
        return redirect(url_for('patient_profile', pid=pid))
    return render_template('patients/form.html', patient={}, action='new', ec={})

@app.route('/patients/<int:pid>')
@login_required
def patient_profile(pid):
    p = query_db("SELECT * FROM patients WHERE id=?", (pid,), one=True)
    if not p: abort(404)
    p = dict(p); p['medical_alerts'] = decrypt_field(p['medical_alerts'])
    ec = query_db("SELECT * FROM emergency_contacts WHERE patient_id=?", (pid,), one=True)
    appointments = query_db("""
        SELECT a.*, u.full_name as dentist_name FROM appointments a JOIN users u ON a.dentist_id=u.id
        WHERE a.patient_id=? ORDER BY a.date DESC, a.time DESC
    """, (pid,))
    notes = query_db("""
        SELECT vn.*, u.full_name as author_name FROM visit_notes vn JOIN users u ON vn.author_id=u.id
        WHERE vn.patient_id=? ORDER BY vn.created_at DESC
    """, (pid,))
    treatment_plans = query_db("""
        SELECT tp.*, u.full_name as created_by_name,
               (SELECT COUNT(*) FROM treatment_items ti WHERE ti.plan_id=tp.id AND ti.status='planned') as pending_items,
               (SELECT COUNT(*) FROM treatment_items ti WHERE ti.plan_id=tp.id) as total_items
        FROM treatment_plans tp LEFT JOIN users u ON tp.created_by=u.id
        WHERE tp.patient_id=? ORDER BY tp.created_at DESC
    """, (pid,))
    treatment_items = {}
    for plan in treatment_plans:
        treatment_items[plan['id']] = query_db("SELECT * FROM treatment_items WHERE plan_id=? ORDER BY id", (plan['id'],))
    tasks = query_db("""
        SELECT t.*, u.full_name as assigned_name FROM tasks t LEFT JOIN users u ON t.assigned_to=u.id
        WHERE t.patient_id=? AND t.status != 'done' ORDER BY t.due_date
    """, (pid,))
    recalls = query_db("SELECT * FROM recalls WHERE patient_id=? ORDER BY due_date DESC LIMIT 5", (pid,))
    payments = query_db("""
        SELECT pr.*, a.date as appt_date, a.reason as appt_reason
        FROM payment_records pr LEFT JOIN appointments a ON pr.appointment_id=a.id
        WHERE pr.patient_id=? ORDER BY pr.created_at DESC
    """, (pid,))
    dentists = get_all_dentists()
    return render_template('patients/profile.html', p=p, ec=ec, appointments=appointments, notes=notes,
        treatment_plans=treatment_plans, treatment_items=treatment_items, tasks=tasks,
        recalls=recalls, payments=payments, dentists=dentists)

@app.route('/patients/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def patient_edit(pid):
    p = query_db("SELECT * FROM patients WHERE id=?", (pid,), one=True)
    if not p: abort(404)
    p = dict(p); p['medical_alerts'] = decrypt_field(p['medical_alerts'])
    ec = query_db("SELECT * FROM emergency_contacts WHERE patient_id=?", (pid,), one=True)
    if request.method == 'POST':
        validate_csrf()
        first = request.form.get('first_name','').strip()
        last = request.form.get('last_name','').strip()
        if not first or not last:
            flash('Nombre y apellido son requeridos.', 'error')
            return render_template('patients/form.html', patient=request.form, action='edit', pid=pid, ec=ec)
        medical_alerts = encrypt_field(request.form.get('medical_alerts','').strip())
        recall_interval = int(request.form.get('recall_interval', 6))
        execute_db("""
            UPDATE patients SET first_name=?, last_name=?, dob=?, gender=?, phone=?, phone_alt=?, email=?,
            address=?, city=?, insurance_name=?, insurance_id=?, medical_alerts=?, notes=?, recall_interval=?, updated_at=? WHERE id=?
        """, (first, last, request.form.get('dob'), request.form.get('gender'),
              request.form.get('phone','').strip(), request.form.get('phone_alt','').strip(),
              request.form.get('email','').strip(), request.form.get('address','').strip(),
              request.form.get('city','').strip(), request.form.get('insurance_name','').strip(),
              request.form.get('insurance_id','').strip(), medical_alerts,
              request.form.get('notes','').strip(), recall_interval, now_str(), pid))
        ec_name = request.form.get('ec_name','').strip()
        if ec_name:
            if ec:
                execute_db("UPDATE emergency_contacts SET name=?, relationship=?, phone=? WHERE patient_id=?",
                    (ec_name, request.form.get('ec_relationship',''), request.form.get('ec_phone',''), pid))
            else:
                execute_db("INSERT INTO emergency_contacts (patient_id, name, relationship, phone) VALUES (?,?,?,?)",
                    (pid, ec_name, request.form.get('ec_relationship',''), request.form.get('ec_phone','')))
        log_activity(current_user.id, current_user.username, 'patient_updated', 'patient', pid, f'{first} {last}', request.remote_addr)
        flash('Paciente actualizado.', 'success')
        return redirect(url_for('patient_profile', pid=pid))
    return render_template('patients/form.html', patient=p, ec=ec, action='edit', pid=pid)

@app.route('/patients/<int:pid>/status', methods=['POST'])
@login_required
def patient_status(pid):
    validate_csrf()
    new_status = request.form.get('status', 'inactive')
    execute_db("UPDATE patients SET status=?, updated_at=? WHERE id=?", (new_status, now_str(), pid))
    log_activity(current_user.id, current_user.username, f'patient_{new_status}', 'patient', pid, ip=request.remote_addr)
    flash('Estado del paciente actualizado.', 'success')
    return redirect(url_for('patient_profile', pid=pid))

# APPOINTMENTS
@app.route('/appointments')
@login_required
def appointments_list():
    view = request.args.get('view', 'today')
    status_filter = request.args.get('status', '')
    dentist_filter = request.args.get('dentist', '')
    q = request.args.get('q', '').strip()
    today = today_str()
    if view == 'today':
        date_sql = "AND a.date = ?"; date_params = [today]; date_label = 'Hoy'
    elif view == 'week':
        week_end = (date.today() + timedelta(days=7)).isoformat()
        date_sql = "AND a.date BETWEEN ? AND ?"; date_params = [today, week_end]; date_label = 'Esta semana'
    elif view == 'tomorrow':
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        date_sql = "AND a.date = ?"; date_params = [tomorrow]; date_label = 'Mañana'
    else:
        date_sql = "AND a.date >= ?"; date_params = [today]; date_label = 'Próximas'
    sql = f"""
        SELECT a.*, p.first_name, p.last_name, p.phone, p.medical_alerts, u.full_name as dentist_name
        FROM appointments a JOIN patients p ON a.patient_id=p.id JOIN users u ON a.dentist_id=u.id
        WHERE 1=1 {date_sql}
    """
    params = date_params
    if status_filter: sql += " AND a.status=?"; params.append(status_filter)
    if dentist_filter: sql += " AND a.dentist_id=?"; params.append(dentist_filter)
    if q:
        sql += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR a.reason LIKE ?)"
        pq = f'%{q}%'; params += [pq, pq, pq]
    sql += " ORDER BY a.date, a.time"
    appointments = query_db(sql, params)
    appts_list = []
    for a in appointments:
        a = dict(a); a['medical_alerts'] = decrypt_field(a['medical_alerts']); appts_list.append(a)
    dentists = get_all_dentists()
    return render_template('appointments/list.html', appointments=appts_list, view=view,
        date_label=date_label, status_filter=status_filter, dentist_filter=dentist_filter,
        dentists=dentists, q=q, today=today)

@app.route('/appointments/new', methods=['GET', 'POST'])
@login_required
def appointment_new():
    if request.method == 'POST':
        validate_csrf()
        pid = request.form.get('patient_id')
        dentist_id = request.form.get('dentist_id')
        appt_date = request.form.get('date')
        appt_time = request.form.get('time')
        if not all([pid, dentist_id, appt_date, appt_time]):
            flash('Paciente, dentista, fecha y hora son requeridos.', 'error')
            return redirect(url_for('appointment_new'))
        aid = execute_db("""
            INSERT INTO appointments (patient_id, dentist_id, date, time, duration, reason, status, notes, created_by)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (pid, dentist_id, appt_date, appt_time, int(request.form.get('duration', 60)),
              request.form.get('reason','').strip(), request.form.get('status','scheduled'),
              request.form.get('notes','').strip(), current_user.id))
        p = query_db("SELECT first_name, last_name FROM patients WHERE id=?", (pid,), one=True)
        log_activity(current_user.id, current_user.username, 'appointment_created', 'appointment', aid,
                     f'{p["first_name"]} {p["last_name"]} - {appt_date} {appt_time}', request.remote_addr)
        flash('Cita programada.', 'success')
        return redirect(request.form.get('next_url', url_for('appointments_list')))
    patient_id = request.args.get('patient_id', '')
    all_patients = query_db("SELECT id, first_name, last_name, phone FROM patients WHERE status='active' ORDER BY last_name, first_name")
    dentists = get_all_dentists()
    return render_template('appointments/form.html', appt={}, action='new', patient_id=patient_id,
        all_patients=all_patients, dentists=dentists, today=today_str())

@app.route('/appointments/<int:aid>/edit', methods=['GET', 'POST'])
@login_required
def appointment_edit(aid):
    appt = query_db("SELECT * FROM appointments WHERE id=?", (aid,), one=True)
    if not appt: abort(404)
    if request.method == 'POST':
        validate_csrf()
        execute_db("""
            UPDATE appointments SET patient_id=?, dentist_id=?, date=?, time=?, duration=?, reason=?,
            status=?, notes=?, cancellation_reason=?, payment_status=?, updated_at=? WHERE id=?
        """, (request.form.get('patient_id'), request.form.get('dentist_id'),
              request.form.get('date'), request.form.get('time'), int(request.form.get('duration', 60)),
              request.form.get('reason','').strip(), request.form.get('status','scheduled'),
              request.form.get('notes','').strip(), request.form.get('cancellation_reason','').strip(),
              request.form.get('payment_status','unpaid'), now_str(), aid))
        log_activity(current_user.id, current_user.username, 'appointment_updated', 'appointment', aid, ip=request.remote_addr)
        flash('Cita actualizada.', 'success')
        return redirect(request.form.get('next_url', url_for('appointments_list')))
    all_patients = query_db("SELECT id, first_name, last_name FROM patients WHERE status='active' ORDER BY last_name")
    dentists = get_all_dentists()
    return render_template('appointments/form.html', appt=appt, action='edit', aid=aid,
        all_patients=all_patients, dentists=dentists, today=today_str())

@app.route('/appointments/<int:aid>/status', methods=['POST'])
@login_required
def appointment_status(aid):
    validate_csrf()
    new_status = request.form.get('status')
    cancel_reason = request.form.get('cancellation_reason', '').strip()
    if new_status not in ['scheduled','confirmed','checked_in','completed','cancelled','no_show']:
        abort(400)
    execute_db("UPDATE appointments SET status=?, cancellation_reason=?, updated_at=? WHERE id=?",
               (new_status, cancel_reason if cancel_reason else None, now_str(), aid))
    log_activity(current_user.id, current_user.username, f'appointment_{new_status}', 'appointment', aid, ip=request.remote_addr)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True, 'status': new_status})
    flash(f'Estado de cita actualizado.', 'success')
    return redirect(request.referrer or url_for('appointments_list'))

# VISIT NOTES
@app.route('/notes/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'dentist')
def note_new():
    if request.method == 'POST':
        validate_csrf()
        pid = request.form.get('patient_id')
        content = request.form.get('clinical_notes', '').strip()
        if not pid or not content:
            flash('Paciente y notas clínicas son requeridos.', 'error')
            return redirect(request.referrer)
        nid = execute_db("""
            INSERT INTO visit_notes (patient_id, appointment_id, author_id, title, chief_complaint,
                clinical_notes, treatment_performed, follow_up_needed, follow_up_notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (pid, request.form.get('appointment_id') or None, current_user.id,
              request.form.get('title','').strip(), request.form.get('chief_complaint','').strip(),
              content, request.form.get('treatment_performed','').strip(),
              1 if request.form.get('follow_up_needed') else 0,
              request.form.get('follow_up_notes','').strip()))
        execute_db("UPDATE patients SET last_recall_date=? WHERE id=?", (today_str(), pid))
        log_activity(current_user.id, current_user.username, 'note_added', 'visit_note', nid, f'patient_id={pid}', request.remote_addr)
        flash('Nota clínica guardada.', 'success')
        return redirect(url_for('patient_profile', pid=pid))
    pid = request.args.get('patient_id', '')
    aid = request.args.get('appointment_id', '')
    all_patients = query_db("SELECT id, first_name, last_name FROM patients WHERE status='active' ORDER BY last_name")
    appt = query_db("SELECT * FROM appointments WHERE id=?", (aid,), one=True) if aid else None
    return render_template('notes/form.html', pid=pid, aid=aid, all_patients=all_patients, appt=appt)

@app.route('/notes/<int:nid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'dentist')
def note_edit(nid):
    note = query_db("SELECT * FROM visit_notes WHERE id=?", (nid,), one=True)
    if not note: abort(404)
    if request.method == 'POST':
        validate_csrf()
        execute_db("""
            UPDATE visit_notes SET title=?, chief_complaint=?, clinical_notes=?,
            treatment_performed=?, follow_up_needed=?, follow_up_notes=?, updated_at=? WHERE id=?
        """, (request.form.get('title','').strip(), request.form.get('chief_complaint','').strip(),
              request.form.get('clinical_notes','').strip(), request.form.get('treatment_performed','').strip(),
              1 if request.form.get('follow_up_needed') else 0,
              request.form.get('follow_up_notes','').strip(), now_str(), nid))
        log_activity(current_user.id, current_user.username, 'note_updated', 'visit_note', nid, ip=request.remote_addr)
        flash('Nota actualizada.', 'success')
        return redirect(url_for('patient_profile', pid=note['patient_id']))
    return render_template('notes/form.html', note=note, action='edit')

@app.route('/notes/<int:nid>/delete', methods=['POST'])
@login_required
@admin_required
def note_delete(nid):
    validate_csrf()
    note = query_db("SELECT * FROM visit_notes WHERE id=?", (nid,), one=True)
    if not note: abort(404)
    execute_db("DELETE FROM visit_notes WHERE id=?", (nid,))
    log_activity(current_user.id, current_user.username, 'note_deleted', 'visit_note', nid, ip=request.remote_addr)
    flash('Nota eliminada.', 'info')
    return redirect(url_for('patient_profile', pid=note['patient_id']))

# TREATMENT PLANS
@app.route('/treatment-plan/new', methods=['POST'])
@login_required
@role_required('admin', 'dentist')
def treatment_plan_new():
    validate_csrf()
    pid = request.form.get('patient_id')
    title = request.form.get('title','').strip()
    if not pid or not title:
        flash('Paciente y título son requeridos.', 'error')
        return redirect(request.referrer)
    plan_id = execute_db("INSERT INTO treatment_plans (patient_id, title, notes, created_by) VALUES (?,?,?,?)",
        (pid, title, request.form.get('notes',''), current_user.id))
    items = request.form.getlist('item_description')
    teeth = request.form.getlist('item_tooth')
    costs = request.form.getlist('item_cost')
    for i, desc in enumerate(items):
        if desc.strip():
            execute_db("INSERT INTO treatment_items (plan_id, description, tooth, cost_estimate) VALUES (?,?,?,?)",
                (plan_id, desc.strip(), teeth[i] if i < len(teeth) else '',
                 float(costs[i]) if i < len(costs) and costs[i] else None))
    log_activity(current_user.id, current_user.username, 'treatment_plan_created', 'treatment_plan', plan_id, f'patient_id={pid}', request.remote_addr)
    flash('Plan de tratamiento creado.', 'success')
    return redirect(url_for('patient_profile', pid=pid))

@app.route('/treatment-item/<int:iid>/status', methods=['POST'])
@login_required
@role_required('admin', 'dentist')
def treatment_item_status(iid):
    validate_csrf()
    new_status = request.form.get('status', 'completed')
    completed_at = now_str() if new_status == 'completed' else None
    execute_db("UPDATE treatment_items SET status=?, completed_at=? WHERE id=?", (new_status, completed_at, iid))
    flash('Estado actualizado.', 'success')
    return redirect(request.referrer)

# TASKS
@app.route('/tasks')
@login_required
def tasks_list():
    status_filter = request.args.get('status', 'open')
    assigned_filter = request.args.get('assigned', str(current_user.id) if current_user.role != 'admin' else '')
    priority_filter = request.args.get('priority', '')
    sql = """
        SELECT t.*, p.first_name, p.last_name, u_assign.full_name as assigned_name, u_create.full_name as created_by_name
        FROM tasks t LEFT JOIN patients p ON t.patient_id=p.id
        LEFT JOIN users u_assign ON t.assigned_to=u_assign.id
        LEFT JOIN users u_create ON t.created_by=u_create.id
        WHERE 1=1
    """
    params = []
    if status_filter and status_filter != 'all':
        if status_filter == 'open':
            sql += " AND t.status IN ('open', 'in_progress')"
        else:
            sql += " AND t.status=?"; params.append(status_filter)
    if assigned_filter: sql += " AND t.assigned_to=?"; params.append(assigned_filter)
    if priority_filter: sql += " AND t.priority=?"; params.append(priority_filter)
    sql += " ORDER BY CASE t.status WHEN 'open' THEN 1 WHEN 'in_progress' THEN 2 ELSE 3 END, CASE t.priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, t.due_date"
    tasks = query_db(sql, params)
    all_staff = get_all_staff()
    return render_template('tasks/list.html', tasks=tasks, all_staff=all_staff,
        status_filter=status_filter, assigned_filter=assigned_filter, priority_filter=priority_filter, today=today_str())

@app.route('/tasks/new', methods=['POST'])
@login_required
def task_new():
    validate_csrf()
    title = request.form.get('title','').strip()
    if not title:
        flash('El título es requerido.', 'error')
        return redirect(request.referrer)
    tid = execute_db("INSERT INTO tasks (title, patient_id, assigned_to, created_by, due_date, priority, notes) VALUES (?,?,?,?,?,?,?)",
        (title, request.form.get('patient_id') or None,
         request.form.get('assigned_to') or current_user.id,
         current_user.id, request.form.get('due_date') or None,
         request.form.get('priority','normal'), request.form.get('notes','').strip()))
    log_activity(current_user.id, current_user.username, 'task_created', 'task', tid, title, request.remote_addr)
    flash('Tarea creada.', 'success')
    return redirect(request.referrer or url_for('tasks_list'))

@app.route('/tasks/<int:tid>/status', methods=['POST'])
@login_required
def task_status(tid):
    validate_csrf()
    new_status = request.form.get('status', 'done')
    execute_db("UPDATE tasks SET status=?, updated_at=? WHERE id=?", (new_status, now_str(), tid))
    log_activity(current_user.id, current_user.username, f'task_{new_status}', 'task', tid, ip=request.remote_addr)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})
    flash('Tarea actualizada.', 'success')
    return redirect(request.referrer or url_for('tasks_list'))

@app.route('/tasks/<int:tid>/delete', methods=['POST'])
@login_required
def task_delete(tid):
    validate_csrf()
    execute_db("DELETE FROM tasks WHERE id=?", (tid,))
    flash('Tarea eliminada.', 'info')
    return redirect(request.referrer or url_for('tasks_list'))

# RECALLS
@app.route('/recalls')
@login_required
def recalls_list():
    status_filter = request.args.get('status', '')
    today = today_str()
    sql = """
        SELECT r.*, p.first_name, p.last_name, p.phone, p.phone_alt, p.next_recall_date, p.recall_interval,
               (SELECT MAX(a.date) FROM appointments a WHERE a.patient_id=p.id AND a.status='completed') as last_visit
        FROM recalls r JOIN patients p ON r.patient_id=p.id WHERE 1=1
    """
    params = []
    if status_filter:
        sql += " AND r.status=?"; params.append(status_filter)
    else:
        sql += " AND r.status IN ('pending', 'overdue', 'contacted')"
    sql += " ORDER BY r.due_date"
    recalls = query_db(sql, params)
    overdue_patients = query_db("""
        SELECT p.* FROM patients p WHERE p.status='active' AND p.next_recall_date IS NOT NULL
        AND p.next_recall_date <= ?
        AND p.id NOT IN (SELECT DISTINCT patient_id FROM recalls WHERE status IN ('pending','contacted'))
        ORDER BY p.next_recall_date
    """, (today,))
    return render_template('recalls/list.html', recalls=recalls, overdue_patients=overdue_patients,
        status_filter=status_filter, today=today)

@app.route('/recalls/new', methods=['POST'])
@login_required
def recall_new():
    validate_csrf()
    pid = request.form.get('patient_id')
    due_date = request.form.get('due_date')
    if not pid or not due_date:
        flash('Paciente y fecha son requeridos.', 'error')
        return redirect(request.referrer)
    execute_db("INSERT INTO recalls (patient_id, due_date, status, notes) VALUES (?,?,?,?)",
               (pid, due_date, 'pending', request.form.get('notes','')))
    execute_db("UPDATE patients SET next_recall_date=? WHERE id=?", (due_date, pid))
    flash('Recordatorio de recall creado.', 'success')
    return redirect(request.referrer)

@app.route('/recalls/<int:rid>/status', methods=['POST'])
@login_required
def recall_status(rid):
    validate_csrf()
    new_status = request.form.get('status', 'contacted')
    execute_db("UPDATE recalls SET status=?, notes=? WHERE id=?",
               (new_status, request.form.get('notes',''), rid))
    flash('Estado de recall actualizado.', 'success')
    return redirect(request.referrer)

# BILLING
@app.route('/billing')
@login_required
def billing_list():
    status_filter = request.args.get('status', '')
    q = request.args.get('q', '').strip()
    sql = """
        SELECT pr.*, p.first_name, p.last_name, a.date as appt_date, a.reason as appt_reason
        FROM payment_records pr JOIN patients p ON pr.patient_id=p.id
        LEFT JOIN appointments a ON pr.appointment_id=a.id WHERE 1=1
    """
    params = []
    if status_filter: sql += " AND pr.status=?"; params.append(status_filter)
    if q:
        sql += " AND (p.first_name LIKE ? OR p.last_name LIKE ?)"; pq = f'%{q}%'; params += [pq, pq]
    sql += " ORDER BY pr.created_at DESC"
    payments = query_db(sql, params)
    totals = query_db("""
        SELECT COALESCE(SUM(CASE WHEN status='paid' THEN amount ELSE 0 END),0) as paid,
               COALESCE(SUM(CASE WHEN status='unpaid' THEN amount ELSE 0 END),0) as unpaid,
               COALESCE(SUM(CASE WHEN status='partial' THEN amount ELSE 0 END),0) as partial,
               COALESCE(SUM(amount),0) as total FROM payment_records
    """, one=True)
    return render_template('billing/list.html', payments=payments, totals=totals, status_filter=status_filter, q=q)

@app.route('/billing/new', methods=['POST'])
@login_required
def billing_new():
    validate_csrf()
    pid = request.form.get('patient_id')
    amount = request.form.get('amount')
    if not pid or not amount:
        flash('Paciente y monto son requeridos.', 'error')
        return redirect(request.referrer)
    execute_db("INSERT INTO payment_records (patient_id, appointment_id, amount, status, method, notes) VALUES (?,?,?,?,?,?)",
        (pid, request.form.get('appointment_id') or None, float(amount),
         request.form.get('status','unpaid'), request.form.get('method',''), request.form.get('notes','')))
    flash('Registro de pago creado.', 'success')
    return redirect(url_for('billing_list'))

@app.route('/billing/<int:bid>/status', methods=['POST'])
@login_required
def billing_status(bid):
    validate_csrf()
    execute_db("UPDATE payment_records SET status=? WHERE id=?", (request.form.get('status','paid'), bid))
    flash('Estado de pago actualizado.', 'success')
    return redirect(request.referrer)

# ADMIN
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = query_db("SELECT * FROM users ORDER BY full_name")
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_new():
    if request.method == 'POST':
        validate_csrf()
        username = request.form.get('username','').strip().lower()
        password = request.form.get('password','').strip()
        full_name = request.form.get('full_name','').strip()
        role = request.form.get('role','front_desk')
        if not all([username, password, full_name]):
            flash('Todos los campos son requeridos.', 'error')
            return render_template('admin/user_form.html', user={}, action='new')
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'error')
            return render_template('admin/user_form.html', user={}, action='new')
        if query_db("SELECT id FROM users WHERE username=?", (username,), one=True):
            flash('El nombre de usuario ya existe.', 'error')
            return render_template('admin/user_form.html', user={}, action='new')
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
        uid = execute_db("INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?,?,?,?,?)",
            (username, request.form.get('email','').strip(), pw_hash, full_name, role))
        log_activity(current_user.id, current_user.username, 'user_created', 'user', uid, f'{username} ({role})', request.remote_addr)
        flash(f'Usuario {username} creado.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/user_form.html', user={}, action='new')

@app.route('/admin/users/<int:uid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_edit(uid):
    user = query_db("SELECT * FROM users WHERE id=?", (uid,), one=True)
    if not user: abort(404)
    if request.method == 'POST':
        validate_csrf()
        full_name = request.form.get('full_name','').strip()
        role = request.form.get('role','front_desk')
        is_active = 1 if request.form.get('is_active') else 0
        execute_db("UPDATE users SET full_name=?, email=?, role=?, is_active=? WHERE id=?",
                   (full_name, request.form.get('email','').strip(), role, is_active, uid))
        new_password = request.form.get('new_password','').strip()
        if new_password:
            if len(new_password) < 8:
                flash('La contraseña debe tener al menos 8 caracteres.', 'error')
                return render_template('admin/user_form.html', user=dict(user), action='edit', uid=uid)
            pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(12)).decode()
            execute_db("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, uid))
        log_activity(current_user.id, current_user.username, 'user_updated', 'user', uid, f'role={role}', request.remote_addr)
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/user_form.html', user=dict(user), action='edit', uid=uid)

@app.route('/admin/users/<int:uid>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_user_toggle(uid):
    validate_csrf()
    if uid == current_user.id:
        flash('No puedes desactivar tu propio usuario.', 'error')
        return redirect(url_for('admin_users'))
    user = query_db("SELECT is_active FROM users WHERE id=?", (uid,), one=True)
    new_status = 0 if user['is_active'] else 1
    execute_db("UPDATE users SET is_active=? WHERE id=?", (new_status, uid))
    log_activity(current_user.id, current_user.username, 'user_activated' if new_status else 'user_deactivated', 'user', uid, ip=request.remote_addr)
    flash('Estado del usuario actualizado.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/activity')
@login_required
@admin_required
def admin_activity():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    total = query_db("SELECT COUNT(*) as n FROM activity_log", one=True)['n']
    logs = query_db("SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ? OFFSET ?", (per_page, offset))
    return render_template('admin/activity.html', logs=logs, page=page, total=total,
        per_page=per_page, pages=((total-1)//per_page)+1 if total > 0 else 1)

# API
@app.route('/api/patients/search')
@login_required
def api_patient_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2: return jsonify([])
    pq = f'%{q}%'
    rows = query_db("""
        SELECT id, first_name, last_name, phone, dob FROM patients
        WHERE status='active' AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?)
        ORDER BY last_name, first_name LIMIT 10
    """, (pq, pq, pq))
    return jsonify([dict(r) for r in rows])

@app.route('/api/appointments/today-count')
@login_required
def api_today_count():
    today = today_str()
    counts = query_db("SELECT status, COUNT(*) as n FROM appointments WHERE date=? GROUP BY status", (today,))
    return jsonify({r['status']: r['n'] for r in counts})

# ERROR HANDLERS
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(400)
def bad_request(e):
    flash('Solicitud inválida. Posible token CSRF faltante.', 'error')
    return redirect(request.referrer or url_for('dashboard'))

@app.errorhandler(429)
def rate_limit(e):
    return render_template('errors/429.html'), 429

if __name__ == '__main__':
    print('\n' + '='*60)
    print('  Clínica Dental Familiar – Dra. Maria I. Berrios Hernandez')
    print('  Sistema de Gestión v2.0')
    print('  Abre tu navegador en: http://localhost:8080')
    print('='*60 + '\n')
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, port=port, host='127.0.0.1')
