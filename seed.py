#!/usr/bin/env python3
"""Seed the database with realistic demo data for Clinica Dental Familiar."""
import os
import sys
import sqlite3
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, execute_db, query_db, init_db, DB_PATH
from encryption import encrypt_field

print(f"Using database: {DB_PATH}")

# Delete old database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Deleted old database.")

# Also remove WAL/SHM files
for ext in ['-shm', '-wal']:
    p = DB_PATH + ext
    if os.path.exists(p):
        os.remove(p)

init_db()
print("Database initialized.")

import bcrypt

def hashpw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(12)).decode()

today = date.today().isoformat()

def dt(days_offset):
    return (date.today() + timedelta(days=days_offset)).isoformat()

def ts(days_offset=0, h=9, m=0):
    d = date.today() + timedelta(days=days_offset)
    return f"{d.isoformat()} {h:02d}:{m:02d}:00"

# USERS
users = [
    ('admin', 'admin@clinica.pr', hashpw('Admin2024!'), 'Administrador Sistema', 'admin'),
    ('dra.berrios', 'dra.berrios@clinica.pr', hashpw('Dental2024!'), 'Dra. Maria I. Berrios Hernandez', 'dentist'),
    ('recepcion', 'recepcion@clinica.pr', hashpw('Recep2024!'), 'María Recepción', 'front_desk'),
]
user_ids = {}
for u in users:
    uid = execute_db("INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?,?,?,?,?)", u)
    user_ids[u[0]] = uid
    print(f"  Created user: {u[0]} ({u[4]})")

admin_id = user_ids['admin']
dentist_id = user_ids['dra.berrios']
recep_id = user_ids['recepcion']

# PATIENTS - 12 realistic PR patients
patients_data = [
    # (first, last, dob, gender, phone, phone_alt, email, address, city, insurance, ins_id, medical_alerts, notes, recall_interval)
    ('Carlos', 'Rivera Ortiz', '1985-03-15', 'M', '787-555-0101', '787-555-0201', 'carlos.rivera@email.com',
     'Urb. Villa del Rey Calle 5 B-12', 'Gurabo', 'Triple-S', 'TSS-123456', '', 'Paciente puntual', 6),
    ('Maria', 'Lopez Santos', '1972-07-22', 'F', '787-555-0102', '', 'maria.lopez@email.com',
     'Calle Betances #45', 'Caguas', 'MCS', 'MCS-789012', 'Alérgica a la penicilina', 'Prefiere mañanas', 6),
    ('Juan', 'Hernandez Torres', '1990-11-08', 'M', '787-555-0103', '787-555-0203', '',
     'HC-02 Box 5678', 'Gurabo', 'Reforma', 'REF-345678', 'Diabetes Tipo 2 - requiere glucosa antes del procedimiento', 'Paciente nervioso', 3),
    ('Ana', 'Morales Cruz', '1965-05-30', 'F', '787-555-0104', '', 'ana.morales@email.com',
     'Urb. Monte Bello Casa 23', 'San Lorenzo', 'Humana', 'HUM-901234', '', 'Seguro vence en diciembre', 12),
    ('Pedro', 'Colon Vazquez', '2010-02-14', 'M', '787-555-0105', '787-555-0205', '',
     'Calle Sol #89 Apt 3', 'Juncos', 'Triple-S Gold', 'TSSG-567890', 'Ansiedad dental severa - necesita sedación', 'Paciente pediátrico', 6),
    ('Sofia', 'Ramos Figueroa', '2008-09-03', 'F', '787-555-0106', '', 'sramos@email.com',
     'Urb. Los Pinos Calle 2 D-5', 'Gurabo', 'MCS Kids', 'MCSK-123789', '', 'Le gustan los stickers', 6),
    ('Roberto', 'Diaz Perez', '1955-12-25', 'M', '787-555-0107', '787-555-0207', '',
     'Calle Marginal #12', 'Las Piedras', 'Medicare', 'MED-456123', 'Hipertensión, toma Lisinopril 10mg. Anticoagulante Warfarina', 'Mayor de edad, viene con hijo', 3),
    ('Carmen', 'Gonzalez Medina', '1988-04-18', 'F', '787-555-0108', '', 'cgonzalez@email.com',
     'Urb. Alturas de Cayey C-34', 'Cayey', 'BCBS', 'BCBS-789456', '', 'Quiere blanqueamiento', 6),
    ('Luis', 'Rodriguez Santiago', '1978-08-12', 'M', '787-555-0109', '787-555-0209', 'lrodriguez@email.com',
     'Calle 8 #456 Urb. Country Club', 'Gurabo', 'Triple-S', 'TSS-654321', 'Alérgico al látex', 'Trabaja de noche', 6),
    ('Isabel', 'Flores Reyes', '2015-06-07', 'F', '787-555-0110', '', 'iflores.parent@email.com',
     'Res. Las Palmas Edif 3 Apt 101', 'Humacao', 'Medicaid Kids', 'MCKPR-111222', '', 'Primera visita, tímida', 6),
    ('Miguel', 'Torres Acevedo', '1995-01-29', 'M', '787-555-0111', '787-555-0211', 'mtorres@email.com',
     'Urb. Villas de Castro Casa 78', 'Caguas', 'Uninsured', '', 'Fumador activo - riesgo periodontal', 'Paga en efectivo', 3),
    ('Gabriela', 'Nieves Robles', '1982-10-16', 'F', '787-555-0112', '', 'gnieves@email.com',
     'Calle Kennedy #234 Apt 2B', 'Gurabo', 'MCS', 'MCS-333444', 'Embarazada - 2do trimestre. NO rayos X.', 'Preferida por la mañana', 3),
]

patient_ids = []
for p in patients_data:
    first, last, dob, gender, phone, phone_alt, email, address, city, ins, ins_id, alerts, notes, recall = p
    encrypted_alerts = encrypt_field(alerts) if alerts else ''
    next_recall = (date.today() + timedelta(days=recall*30)).isoformat()
    pid = execute_db("""
        INSERT INTO patients (first_name, last_name, dob, gender, phone, phone_alt, email,
            address, city, insurance_name, insurance_id, medical_alerts, notes,
            recall_interval, next_recall_date, created_by)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (first, last, dob, gender, phone, phone_alt, email, address, city, ins, ins_id,
          encrypted_alerts, notes, recall, next_recall, admin_id))
    patient_ids.append(pid)
    print(f"  Created patient: {first} {last} (ID {pid})")

# EMERGENCY CONTACTS
ec_data = [
    (patient_ids[0], 'Rosa Rivera', 'Esposa', '787-555-0301'),
    (patient_ids[1], 'Jorge Lopez', 'Esposo', '787-555-0302'),
    (patient_ids[2], 'Carmen Torres', 'Madre', '787-555-0303'),
    (patient_ids[3], 'Luis Morales', 'Esposo', '787-555-0304'),
    (patient_ids[4], 'Ana Vazquez', 'Madre', '787-555-0305'),
    (patient_ids[5], 'Ricardo Ramos', 'Padre', '787-555-0306'),
    (patient_ids[6], 'Carmen Diaz', 'Hija', '787-555-0307'),
    (patient_ids[7], 'Pedro Gonzalez', 'Hermano', '787-555-0308'),
    (patient_ids[8], 'Lucia Santiago', 'Esposa', '787-555-0309'),
    (patient_ids[9], 'Maria Flores', 'Madre', '787-555-0310'),
    (patient_ids[10], 'Elena Acevedo', 'Madre', '787-555-0311'),
    (patient_ids[11], 'Carlos Nieves', 'Esposo', '787-555-0312'),
]
for ec in ec_data:
    execute_db("INSERT INTO emergency_contacts (patient_id, name, relationship, phone) VALUES (?,?,?,?)", ec)

print("  Emergency contacts created.")

# APPOINTMENTS - variety of statuses including today
appointments_data = [
    # Today's appointments (6 appointments today)
    (patient_ids[0], dentist_id, today, '09:00', 60, 'Limpieza dental', 'confirmed', 'paid', admin_id),
    (patient_ids[1], dentist_id, today, '10:00', 90, 'Empaste molar', 'checked_in', 'unpaid', admin_id),
    (patient_ids[2], dentist_id, today, '11:30', 60, 'Revisión periódica', 'scheduled', 'unpaid', recep_id),
    (patient_ids[5], dentist_id, today, '13:00', 45, 'Sellantes pediátricos', 'confirmed', 'paid', recep_id),
    (patient_ids[11], dentist_id, today, '14:00', 60, 'Consulta embarazo', 'scheduled', 'unpaid', admin_id),
    (patient_ids[7], dentist_id, today, '15:00', 90, 'Corona temporal', 'scheduled', 'unpaid', recep_id),

    # Past completed appointments
    (patient_ids[0], dentist_id, dt(-30), '09:00', 60, 'Examen inicial', 'completed', 'paid', admin_id),
    (patient_ids[1], dentist_id, dt(-45), '10:00', 90, 'Extracciones #18', 'completed', 'paid', admin_id),
    (patient_ids[3], dentist_id, dt(-14), '11:00', 60, 'Limpieza profunda', 'completed', 'paid', admin_id),
    (patient_ids[6], dentist_id, dt(-7), '09:30', 60, 'Revisión implante', 'completed', 'partial', admin_id),
    (patient_ids[8], dentist_id, dt(-21), '14:00', 60, 'Blanqueamiento sesión 1', 'completed', 'paid', recep_id),
    (patient_ids[4], dentist_id, dt(-10), '10:00', 45, 'Fluoruro pediátrico', 'completed', 'paid', recep_id),

    # Past cancelled/no-show
    (patient_ids[9], dentist_id, dt(-5), '11:00', 60, 'Primera visita', 'no_show', 'unpaid', recep_id),
    (patient_ids[10], dentist_id, dt(-3), '09:00', 60, 'Urgencia dental', 'cancelled', 'unpaid', recep_id),

    # Future appointments
    (patient_ids[3], dentist_id, dt(1), '10:00', 60, 'Limpieza semestral', 'scheduled', 'unpaid', admin_id),
    (patient_ids[6], dentist_id, dt(2), '09:30', 90, 'Corona permanente', 'confirmed', 'unpaid', recep_id),
    (patient_ids[9], dentist_id, dt(3), '14:00', 60, 'Revisión ortodoncia', 'scheduled', 'unpaid', recep_id),
    (patient_ids[10], dentist_id, dt(5), '11:00', 60, 'Raspado y alisado', 'scheduled', 'unpaid', admin_id),
    (patient_ids[2], dentist_id, dt(7), '10:30', 90, 'Puente dental consulta', 'scheduled', 'unpaid', admin_id),
    (patient_ids[11], dentist_id, dt(14), '09:00', 60, 'Control prenatal dental', 'scheduled', 'unpaid', recep_id),
]

appt_ids = []
for a in appointments_data:
    pid, did, adate, atime, dur, reason, status, pay_status, created_by = a
    aid = execute_db("""
        INSERT INTO appointments (patient_id, dentist_id, date, time, duration, reason, status, payment_status, created_by)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (pid, did, adate, atime, dur, reason, status, pay_status, created_by))
    appt_ids.append(aid)

print(f"  Created {len(appt_ids)} appointments.")

# VISIT NOTES for completed appointments
notes_data = [
    (patient_ids[0], appt_ids[6], dentist_id, 'Examen inicial', 'Revisión general',
     'Paciente en buenas condiciones de higiene. Se observa leve acumulación de sarro en zona posterior. Radiografías periapicales tomadas, sin hallazgos patológicos.',
     'Profilaxis dental, instrucciones de higiene oral', 0, ''),
    (patient_ids[1], appt_ids[7], dentist_id, 'Extracción #18', 'Dolor intenso molar inferior izquierdo',
     'Molar #18 con caries extensiva que llega a pulpa. Irreparable. Se realizó extracción bajo anestesia local. Procedimiento sin complicaciones.',
     'Extracción del #18, sutura con Vicryl 3-0', 1, 'Cita de revisión en 7 días'),
    (patient_ids[3], appt_ids[8], dentist_id, 'Limpieza profunda', 'Encías sangrantes',
     'Periodontitis leve generalizada. Profundidades de sondeo 3-4mm. Se realizó destartraje y alisado radicular en cuatro cuadrantes.',
     'Destartraje supragingival e infragingival, alisado radicular', 1, 'Reevaluación periodontal en 6 semanas'),
    (patient_ids[6], appt_ids[9], dentist_id, 'Revisión implante', 'Revisión de implante #3',
     'Implante en posición #3 estable, sin movilidad. Mucosa peri-implantaria sana, sin signos de periimplantitis. Corona de porcelana con buen ajuste oclusal.',
     'Pulido de corona, instrucciones de higiene peri-implantaria', 0, ''),
    (patient_ids[8], appt_ids[10], dentist_id, 'Blanqueamiento sesión 1', 'Quiere dientes más blancos',
     'Blanqueamiento en consultorio con peróxido de hidrógeno 35%. Se colocó dique de goma para protección gingival. Aplicación por 3 rondas de 15 minutos. Buena tolerancia.',
     'Blanqueamiento en consultorio', 1, 'Segunda sesión en 2 semanas para refuerzo'),
    (patient_ids[4], appt_ids[11], dentist_id, 'Fluoruro pediátrico', 'Aplicación preventiva',
     'Paciente colaborador. Examen bucal: sin caries activas. Higiene oral mejorada desde última visita. Radiografías bite-wing: sin hallazgos interproximales.',
     'Aplicación de fluoruro en barniz, sellante en #3 y #14', 0, ''),
]

for n in notes_data:
    pid, aid, author, title, complaint, notes, treatment, followup, followup_notes = n
    execute_db("""
        INSERT INTO visit_notes (patient_id, appointment_id, author_id, title, chief_complaint,
            clinical_notes, treatment_performed, follow_up_needed, follow_up_notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (pid, aid, author, title, complaint, notes, treatment, followup, followup_notes))

print("  Visit notes created.")

# TREATMENT PLANS
plan1 = execute_db("INSERT INTO treatment_plans (patient_id, title, status, notes, created_by) VALUES (?,?,?,?,?)",
    (patient_ids[6], 'Plan rehabilitación oral completa', 'active',
     'Paciente con pérdida ósea moderada, necesita tratamiento integral', dentist_id))

plan_items = [
    (plan1, 'Corona porcelana sobre implante #3', '#3', 'completed', 1800.00),
    (plan1, 'Raspado y alisado cuadrante I', 'Q1', 'completed', 350.00),
    (plan1, 'Raspado y alisado cuadrante II', 'Q2', 'planned', 350.00),
    (plan1, 'Raspado y alisado cuadrante III', 'Q3', 'planned', 350.00),
    (plan1, 'Placa oclusal nocturna', '', 'planned', 450.00),
]
for item in plan_items:
    execute_db("INSERT INTO treatment_items (plan_id, description, tooth, status, cost_estimate) VALUES (?,?,?,?,?)", item)

plan2 = execute_db("INSERT INTO treatment_plans (patient_id, title, status, notes, created_by) VALUES (?,?,?,?,?)",
    (patient_ids[2], 'Plan tratamiento caries múltiples', 'active',
     'Control diabetes - tratamiento en citas cortas', dentist_id))

plan_items2 = [
    (plan2, 'Empaste composite #14', '#14', 'planned', 180.00),
    (plan2, 'Empaste composite #19', '#19', 'planned', 180.00),
    (plan2, 'Endodoncia #30', '#30', 'planned', 850.00),
    (plan2, 'Corona porcelana #30', '#30', 'planned', 1200.00),
]
for item in plan_items2:
    execute_db("INSERT INTO treatment_items (plan_id, description, tooth, status, cost_estimate) VALUES (?,?,?,?,?)", item)

plan3 = execute_db("INSERT INTO treatment_plans (patient_id, title, status, notes, created_by) VALUES (?,?,?,?,?)",
    (patient_ids[10], 'Control periodontal', 'active', 'Fumador - mayor riesgo', dentist_id))
execute_db("INSERT INTO treatment_items (plan_id, description, tooth, status, cost_estimate) VALUES (?,?,?,?,?)",
    (plan3, 'Raspado y alisado 4 cuadrantes', 'Todos', 'planned', 1200.00))
execute_db("INSERT INTO treatment_items (plan_id, description, tooth, status, cost_estimate) VALUES (?,?,?,?,?)",
    (plan3, 'Reevaluación periodontal', '', 'planned', 0))

print("  Treatment plans created.")

# TASKS
tasks_data = [
    ('Llamar a paciente Juan Hernandez para confirmar cita', patient_ids[2], recep_id, admin_id, dt(0), 'urgent', 'open', 'No ha confirmado, intentar 3 veces'),
    ('Solicitar pre-autorización seguro Triple-S - Carlos Rivera', patient_ids[0], recep_id, admin_id, dt(1), 'high', 'open', 'Corona temporal en progreso'),
    ('Ordenar suministros: guantes, mascarillas, composite A2', None, admin_id, admin_id, dt(2), 'normal', 'open', 'Se están acabando guantes talla M'),
    ('Revisar esterilización de instrumentos', None, dentist_id, admin_id, dt(0), 'high', 'in_progress', ''),
    ('Enviar recordatorio citas semana próxima', None, recep_id, admin_id, dt(0), 'normal', 'open', 'Usar el sistema de mensajes'),
    ('Certificado de salud dental - Sofia Ramos (escuela)', patient_ids[5], recep_id, recep_id, dt(3), 'normal', 'open', 'Mamá llamó ayer'),
    ('Seguimiento no-show - Isabel Flores', patient_ids[9], recep_id, admin_id, dt(1), 'high', 'open', 'Segunda vez que falta'),
    ('Actualizar seguro de Roberto Diaz - vence este mes', patient_ids[6], recep_id, admin_id, dt(5), 'normal', 'open', 'Llamar a Medicare para verificar'),
    ('Comprobante de pago pendiente - Miguel Torres', patient_ids[10], recep_id, recep_id, dt(0), 'high', 'open', '$350 pendiente de último tratamiento'),
    ('Preparar silla pediátrica para las 9am', None, recep_id, recep_id, dt(0), 'normal', 'done', ''),
]
for t in tasks_data:
    title, pid, assigned, created_by, due, priority, status, notes = t
    execute_db("""
        INSERT INTO tasks (title, patient_id, assigned_to, created_by, due_date, priority, status, notes)
        VALUES (?,?,?,?,?,?,?,?)
    """, (title, pid, assigned, created_by, due, priority, status, notes))

print("  Tasks created.")

# RECALLS
recalls_data = [
    (patient_ids[1], dt(-90), 'overdue', 'Última visita hace 9 meses'),
    (patient_ids[3], dt(-30), 'overdue', 'Limpieza semestral vencida'),
    (patient_ids[6], dt(-15), 'contacted', 'Llamada el martes, cita agendada'),
    (patient_ids[7], dt(-60), 'overdue', 'Paciente mayor, difícil contactar'),
    (patient_ids[8], dt(30), 'pending', 'Segunda sesión blanqueamiento'),
    (patient_ids[10], dt(14), 'pending', 'Control periodontal'),
    (patient_ids[11], dt(45), 'pending', 'Control prenatal dental'),
    (patient_ids[0], dt(60), 'pending', 'Limpieza semestral programada'),
    (patient_ids[4], dt(-10), 'overdue', 'Paciente pediátrico sin contactar'),
    (patient_ids[5], dt(90), 'pending', 'Sellantes de seguimiento'),
]
for r in recalls_data:
    execute_db("INSERT INTO recalls (patient_id, due_date, status, notes) VALUES (?,?,?,?)", r)

# Update patient next_recall_date for overdue ones
execute_db("UPDATE patients SET next_recall_date=? WHERE id=?", (dt(-90), patient_ids[1]))
execute_db("UPDATE patients SET next_recall_date=? WHERE id=?", (dt(-30), patient_ids[3]))
execute_db("UPDATE patients SET next_recall_date=? WHERE id=?", (dt(-60), patient_ids[7]))
execute_db("UPDATE patients SET next_recall_date=? WHERE id=?", (dt(-10), patient_ids[4]))

print("  Recalls created.")

# PAYMENT RECORDS
payments_data = [
    (patient_ids[0], appt_ids[6], 150.00, 'paid', 'insurance', 'Triple-S cubrió 80%, paciente pagó 30'),
    (patient_ids[0], appt_ids[0], 0.00, 'unpaid', '', 'Pendiente de cobro'),
    (patient_ids[1], appt_ids[7], 450.00, 'paid', 'cash', 'Extracción + anestesia'),
    (patient_ids[1], appt_ids[1], 280.00, 'unpaid', '', 'Empaste por cobrar'),
    (patient_ids[3], appt_ids[8], 700.00, 'paid', 'credit_card', 'Visa terminada en 4532'),
    (patient_ids[3], appt_ids[14], 0.00, 'unpaid', '', 'Limpieza próxima cita'),
    (patient_ids[6], appt_ids[9], 1800.00, 'partial', 'insurance', 'Medicare pagó 1200, balance 600'),
    (patient_ids[8], appt_ids[10], 350.00, 'paid', 'cash', 'Sesión 1 blanqueamiento'),
    (patient_ids[4], appt_ids[11], 120.00, 'paid', 'insurance', 'Cubierto por MCS'),
    (patient_ids[10], None, 350.00, 'unpaid', '', 'Balance pendiente raspado y alisado'),
    (patient_ids[2], None, 180.00, 'unpaid', '', 'Empaste pendiente'),
    (patient_ids[7], appt_ids[3], 250.00, 'partial', 'check', 'Cheque #1234, balance 150 pendiente'),
]
for p in payments_data:
    pid, aid, amount, status, method, notes = p
    execute_db("""
        INSERT INTO payment_records (patient_id, appointment_id, amount, status, method, notes)
        VALUES (?,?,?,?,?,?)
    """, (pid, aid, amount, status, method, notes))

print("  Payment records created.")

# ACTIVITY LOG
activity_entries = [
    (admin_id, 'admin', 'login', None, None, 'Inicio de sesión exitoso', '127.0.0.1'),
    (admin_id, 'admin', 'patient_created', 'patient', patient_ids[0], 'Carlos Rivera Ortiz', '127.0.0.1'),
    (recep_id, 'recepcion', 'appointment_created', 'appointment', appt_ids[0], 'Cita programada para hoy', '127.0.0.1'),
    (dentist_id, 'dra.berrios', 'note_added', 'visit_note', 1, 'Nota clínica agregada', '127.0.0.1'),
    (admin_id, 'admin', 'user_created', 'user', recep_id, 'recepcion (front_desk)', '127.0.0.1'),
    (recep_id, 'recepcion', 'login', None, None, 'Inicio de sesión', '127.0.0.1'),
    (dentist_id, 'dra.berrios', 'login', None, None, 'Inicio de sesión', '127.0.0.1'),
    (admin_id, 'admin', 'appointment_completed', 'appointment', appt_ids[6], 'Cita completada', '127.0.0.1'),
    (recep_id, 'recepcion', 'task_created', 'task', 1, 'Nueva tarea asignada', '127.0.0.1'),
    (admin_id, 'admin', 'patient_updated', 'patient', patient_ids[5], 'Sofia Ramos Figueroa', '127.0.0.1'),
]
for entry in activity_entries:
    execute_db("""
        INSERT INTO activity_log (user_id, username, action, entity_type, entity_id, details, ip_address)
        VALUES (?,?,?,?,?,?,?)
    """, entry)

print("  Activity log created.")
print("\n" + "="*60)
print("  DATABASE SEEDED SUCCESSFULLY!")
print("="*60)
print("\nDemo Credentials:")
print("  Admin:      admin / Admin2024!")
print("  Dentist:    dra.berrios / Dental2024!")
print("  Reception:  recepcion / Recep2024!")
print(f"\nPatients created: {len(patient_ids)}")
print(f"Appointments: {len(appt_ids)}")
print("="*60 + "\n")
