import os
from datetime import datetime, date, timedelta, timezone
from functools import wraps
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda *args, **kwargs: None
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from ml.predict import predict_risk
from services.email_service import send_email
from services.twilio_service import send_sms

load_dotenv(Path(__file__).with_name('.env'))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///medicine_reminder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'development-only-secret')
db = SQLAlchemy(app)
JWTManager(app)
CORS(app)


class User(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='patient')
    reminder_preferences = db.Column(db.JSON, default=lambda: {'web': True, 'sms': False, 'email': False})
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RelativeRelationship(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    relative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    relationship_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Medicine(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    dosage_unit = db.Column(db.String(30), nullable=False, default='mg')
    frequency = db.Column(db.String(50), nullable=False, default='Once daily')
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=True)
    instructions = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DoseSchedule(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    scheduled_time = db.Column(db.String(10), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DoseLog(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('dose_schedule.id'), nullable=True)
    scheduled_time = db.Column(db.String(10), nullable=False)
    actual_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Reminder(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    dose_schedule_id = db.Column(db.Integer, db.ForeignKey('dose_schedule.id'), nullable=True)
    reminder_type = db.Column(db.String(20), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')
    message = db.Column(db.String(300), nullable=True)


def user_payload(user):
    return {'id': user.id, 'full_name': user.full_name, 'email': user.email, 'phone': user.phone, 'role': user.role, 'date_of_birth': user.date_of_birth, 'gender': user.gender, 'reminder_preferences': user.reminder_preferences or {}}


def medicine_payload(medicine):
    schedules = DoseSchedule.query.filter_by(medicine_id=medicine.id, active=True).all()
    return {'id': medicine.id, 'medicine_name': medicine.medicine_name, 'dosage': medicine.dosage, 'dosage_unit': medicine.dosage_unit, 'frequency': medicine.frequency, 'start_date': medicine.start_date, 'end_date': medicine.end_date, 'instructions': medicine.instructions, 'schedules': [{'id': s.id, 'scheduled_time': s.scheduled_time, 'frequency': s.frequency} for s in schedules]}


def current_user():
    try:
        identity = get_jwt_identity()
        if identity is None:
            return None
        return User.query.get(int(identity))
    except Exception:
        return None


def patient_only(fn):
    @wraps(fn)
    @jwt_required()
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify(success=False, message='Session invalid or user not found. Please sign in again.'), 401
        if user.role != 'patient':
            return jsonify(success=False, message='Patient access required'), 403
        return fn(*args, **kwargs)
    return wrapped


def accessible_patient(patient_id):
    user = current_user()
    if not user:
        return False
    if user.role == 'patient' and user.id == patient_id:
        return True
    return RelativeRelationship.query.filter_by(patient_id=patient_id, relative_id=user.id, status='approved').first() is not None


@app.get('/api/health')
def health():
    return jsonify(success=True, message='Smart Medicine Reminder API is running')


@app.post('/api/auth/register')
def register():
    data = request.get_json() or {}
    required = ['full_name', 'email', 'password', 'role']
    if any(not data.get(field) for field in required) or data['role'] not in ('patient', 'relative'):
        return jsonify(success=False, message='Full name, email, password and a valid role are required'), 400
    email = data['email'].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify(success=False, message='An account with this email already exists'), 409
    user = User(full_name=data['full_name'].strip(), email=email, phone=data.get('phone'), password_hash=generate_password_hash(data['password']), date_of_birth=data.get('date_of_birth'), gender=data.get('gender'), role=data['role'], reminder_preferences=data.get('reminder_preferences', {'web': True, 'sms': False, 'email': False}))
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify(success=True, user=user_payload(user), token=token), 201


@app.post('/api/auth/login')
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=str(data.get('email', '')).strip().lower()).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify(success=False, message='Invalid email or password'), 401
    return jsonify(success=True, user=user_payload(user), token=create_access_token(identity=str(user.id)))


@app.get('/api/users/me')
@jwt_required()
def me():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    return jsonify(success=True, user=user_payload(user))


@app.put('/api/users/me')
@jwt_required()
def update_me():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    data = request.get_json() or {}
    for field in ('full_name', 'phone', 'date_of_birth', 'gender', 'reminder_preferences'):
        if field in data: setattr(user, field, data[field])
    db.session.commit()
    return jsonify(success=True, user=user_payload(user))


@app.post('/api/relatives/link')
@patient_only
def link_relative():
    data = request.get_json() or {}
    relative = User.query.filter_by(email=str(data.get('relative_email', '')).strip().lower(), role='relative').first()
    if not relative:
        return jsonify(success=False, message='Relative must register first using that email'), 404
    existing = RelativeRelationship.query.filter_by(patient_id=current_user().id, relative_id=relative.id).first()
    if existing: return jsonify(success=False, message='Relationship already exists'), 409
    link = RelativeRelationship(patient_id=current_user().id, relative_id=relative.id, relationship_type=data.get('relationship_type', 'Caregiver'), status='approved')
    db.session.add(link); db.session.commit()
    return jsonify(success=True, message='Relative linked successfully'), 201


@app.get('/api/relatives/patients')
@jwt_required()
def linked_patients():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    if user.role == 'patient': return jsonify(success=True, patients=[])
    links = RelativeRelationship.query.filter_by(relative_id=user.id, status='approved').all()
    return jsonify(success=True, patients=[user_payload(User.query.get(link.patient_id)) for link in links if User.query.get(link.patient_id)])


@app.post('/api/medicines')
@patient_only
def create_medicine():
    data = request.get_json() or {}
    for field in ('medicine_name', 'dosage', 'start_date', 'timings'):
        if not data.get(field): return jsonify(success=False, message=f'{field} is required'), 400
    user = current_user()
    medicine = Medicine(patient_id=user.id, medicine_name=data['medicine_name'], dosage=str(data['dosage']), dosage_unit=data.get('dosage_unit', 'mg'), frequency=data.get('frequency', 'Once daily'), start_date=data['start_date'], end_date=data.get('end_date'), instructions=data.get('instructions'))
    db.session.add(medicine); db.session.flush()
    for time_value in data['timings'] if isinstance(data['timings'], list) else [data['timings']]:
        db.session.add(DoseSchedule(medicine_id=medicine.id, scheduled_time=time_value, frequency=medicine.frequency))
    db.session.commit()
    return jsonify(success=True, medicine=medicine_payload(medicine)), 201


@app.get('/api/medicines')
@jwt_required()
def medicines():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    patient_id = int(request.args.get('patient_id', user.id))
    if not accessible_patient(patient_id): return jsonify(success=False, message='You are not authorized to view this patient'), 403
    return jsonify(success=True, medicines=[medicine_payload(m) for m in Medicine.query.filter_by(patient_id=patient_id).order_by(Medicine.created_at.desc()).all()])


@app.put('/api/medicines/<int:medicine_id>')
@patient_only
def update_medicine(medicine_id):
    user = current_user()
    medicine = Medicine.query.filter_by(id=medicine_id, patient_id=user.id).first()
    if not medicine: return jsonify(success=False, message='Medicine not found'), 404
    data = request.get_json() or {}
    for field in ('medicine_name', 'dosage', 'dosage_unit', 'frequency', 'start_date', 'end_date', 'instructions'):
        if field in data: setattr(medicine, field, data[field])
    if 'timings' in data:
        DoseSchedule.query.filter_by(medicine_id=medicine.id).update({'active': False})
        for time_value in data['timings']: db.session.add(DoseSchedule(medicine_id=medicine.id, scheduled_time=time_value, frequency=medicine.frequency))
    db.session.commit(); return jsonify(success=True, medicine=medicine_payload(medicine))


@app.delete('/api/medicines/<int:medicine_id>')
@patient_only
def delete_medicine(medicine_id):
    user = current_user()
    medicine = Medicine.query.filter_by(id=medicine_id, patient_id=user.id).first()
    if not medicine: return jsonify(success=False, message='Medicine not found'), 404
    DoseSchedule.query.filter_by(medicine_id=medicine.id).update({'active': False}); db.session.delete(medicine); db.session.commit()
    return jsonify(success=True, message='Medicine removed')


def _parse_time(value):
    try:
        return datetime.strptime(str(value), '%H:%M').time()
    except (TypeError, ValueError):
        return None


def reconcile_missed_doses(patient_id):
    now = datetime.now()
    today = date.today()
    grace_period = timedelta(minutes=5)
    for medicine in Medicine.query.filter_by(patient_id=patient_id).all():
        for schedule in DoseSchedule.query.filter_by(medicine_id=medicine.id, active=True).all():
            due_time = _parse_time(schedule.scheduled_time)
            if due_time is None:
                continue
            due_today = datetime.combine(today, due_time)
            due_yesterday = datetime.combine(today - timedelta(days=1), due_time)
            if due_today > now and due_yesterday > now:
                continue
            existing_log = DoseLog.query.filter_by(
                patient_id=patient_id,
                medicine_id=medicine.id,
                schedule_id=schedule.id,
            ).filter(
                DoseLog.created_at >= datetime.combine(today, datetime.min.time()),
                DoseLog.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time()),
            ).order_by(DoseLog.created_at.desc()).first()
            if existing_log is not None:
                if existing_log.status in {'taken', 'skipped'}:
                    continue
                continue
            if due_yesterday + grace_period <= now and not DoseLog.query.filter_by(
                patient_id=patient_id,
                medicine_id=medicine.id,
                schedule_id=schedule.id,
            ).filter(
                DoseLog.created_at >= datetime.combine(today - timedelta(days=1), datetime.min.time()),
                DoseLog.created_at < datetime.combine(today, datetime.min.time()),
            ).first():
                db.session.add(DoseLog(
                    patient_id=patient_id,
                    medicine_id=medicine.id,
                    schedule_id=schedule.id,
                    scheduled_time=schedule.scheduled_time,
                    status='missed',
                    actual_time=None,
                    created_at=due_yesterday,
                ))
            if due_today + grace_period <= now:
                db.session.add(DoseLog(
                    patient_id=patient_id,
                    medicine_id=medicine.id,
                    schedule_id=schedule.id,
                    scheduled_time=schedule.scheduled_time,
                    status='missed',
                    actual_time=None,
                    created_at=now,
                ))
    db.session.commit()


def dose_rows(patient_id, start=None):
    query = DoseLog.query.filter_by(patient_id=patient_id)
    if start: query = query.filter(DoseLog.created_at >= start)
    return query.order_by(DoseLog.created_at.desc()).all()


@app.get('/api/doses/today')
@jwt_required()
def today_doses():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    patient_id = int(request.args.get('patient_id', user.id))
    if not accessible_patient(patient_id): return jsonify(success=False, message='You are not authorized to view this patient'), 403
    reconcile_missed_doses(patient_id)
    medicines_list = Medicine.query.filter_by(patient_id=patient_id).all(); result = []
    for medicine in medicines_list:
        for schedule in DoseSchedule.query.filter_by(medicine_id=medicine.id, active=True).all():
            log = DoseLog.query.filter_by(patient_id=patient_id, medicine_id=medicine.id, schedule_id=schedule.id).filter(db.func.date(DoseLog.created_at) == date.today().isoformat()).first()
            if log is None:
                due_time = _parse_time(schedule.scheduled_time)
                grace_deadline = datetime.combine(date.today(), due_time) + timedelta(minutes=5) if due_time else None
                status = 'upcoming' if grace_deadline is not None and grace_deadline > datetime.now() else 'missed'
            else:
                status = log.status
            result.append({'id': log.id if log else None, 'medicine_id': medicine.id, 'schedule_id': schedule.id, 'medicine_name': medicine.medicine_name, 'dosage': medicine.dosage, 'dosage_unit': medicine.dosage_unit, 'scheduled_time': schedule.scheduled_time, 'status': status, 'actual_time': log.actual_time.isoformat() if log and log.actual_time else None})
    return jsonify(success=True, doses=sorted(result, key=lambda row: row['scheduled_time']))


def log_dose(schedule_id, status):
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    schedule = DoseSchedule.query.get(schedule_id)
    medicine = Medicine.query.get(schedule.medicine_id) if schedule else None
    if not schedule or not medicine or medicine.patient_id != user.id: return jsonify(success=False, message='Dose not found'), 404
    log = DoseLog.query.filter_by(patient_id=user.id, medicine_id=medicine.id, schedule_id=schedule.id).filter(db.func.date(DoseLog.created_at) == date.today().isoformat()).first()
    if not log: log = DoseLog(patient_id=user.id, medicine_id=medicine.id, schedule_id=schedule.id, scheduled_time=schedule.scheduled_time, status=status); db.session.add(log)
    else: log.status = status
    log.actual_time = datetime.now(timezone.utc) if status == 'taken' else None
    db.session.commit(); return jsonify(success=True, dose={'id': log.id, 'status': log.status})


@app.post('/api/doses/<int:schedule_id>/taken')
@patient_only
def taken(schedule_id): return log_dose(schedule_id, 'taken')


@app.post('/api/doses/<int:schedule_id>/skipped')
@patient_only
def skipped(schedule_id): return log_dose(schedule_id, 'skipped')


@app.get('/api/doses/history')
@jwt_required()
def history():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    patient_id = int(request.args.get('patient_id', user.id))
    if not accessible_patient(patient_id): return jsonify(success=False, message='You are not authorized to view this patient'), 403
    rows = dose_rows(patient_id, datetime.utcnow() - timedelta(days=int(request.args.get('days', 30))))
    return jsonify(success=True, history=[{'id': row.id, 'medicine_name': Medicine.query.get(row.medicine_id).medicine_name, 'scheduled_time': row.scheduled_time, 'actual_time': row.actual_time.isoformat() if row.actual_time else None, 'status': row.status, 'created_at': row.created_at.isoformat()} for row in rows])


def analytics_for(patient_id, days):
    start = datetime.utcnow() - timedelta(days=days); rows = dose_rows(patient_id, start)
    taken_count = sum(row.status == 'taken' for row in rows); missed_count = sum(row.status == 'missed' for row in rows); skipped_count = sum(row.status == 'skipped' for row in rows)
    total = len(rows)
    return {'total': total, 'taken': taken_count, 'missed': missed_count, 'skipped': skipped_count, 'adherence': round(taken_count / total * 100, 1) if total else 0}


@app.get('/api/analytics/<period>')
@jwt_required()
def analytics(period):
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    patient_id = int(request.args.get('patient_id', user.id))
    if not accessible_patient(patient_id): return jsonify(success=False, message='You are not authorized to view this patient'), 403
    days = 30 if period == 'monthly' else 7
    summary = analytics_for(patient_id, days)
    return jsonify(success=True, period=period, summary=summary)


def repeated_miss_alert(patient_id, days=5):
    cutoff = datetime.utcnow() - timedelta(days=days)
    missed_logs = DoseLog.query.filter_by(patient_id=patient_id, status='missed').filter(DoseLog.created_at >= cutoff).all()
    by_time = {}
    for row in missed_logs:
        by_time[row.scheduled_time] = by_time.get(row.scheduled_time, 0) + 1
    same_time_missed_days = max(by_time.values(), default=0)
    if same_time_missed_days >= 4:
        return {
            'same_time_missed_days': same_time_missed_days,
            'alert': 'You have missed this medicine at the same time for 4-5 days. Do not miss the next dose. Set a 30-minute reminder, keep the dose visible, and ask a caregiver to check in with you.',
            'severity': 'high'
        }
    if same_time_missed_days >= 2:
        return {
            'same_time_missed_days': same_time_missed_days,
            'alert': 'This medicine has been missed on the same schedule more than once recently. Try a stronger reminder before the next dose is due.',
            'severity': 'moderate'
        }
    return {'same_time_missed_days': same_time_missed_days, 'alert': '', 'severity': 'low'}


@app.post('/api/predict')
@jwt_required()
def prediction():
    user = current_user()
    if not user: return jsonify(success=False, message='User not found'), 401
    patient_id = int(request.args.get('patient_id', user.id))
    if not accessible_patient(patient_id): return jsonify(success=False, message='You are not authorized to view this patient'), 403
    reconcile_missed_doses(patient_id)
    summary = analytics_for(patient_id, 30); patient = User.query.get(patient_id)
    data = request.get_json(silent=True) or {}
    pattern = repeated_miss_alert(patient_id)
    features = {
        'age': data.get('age', 45),
        'medicine_frequency': data.get('medicine_frequency', 1),
        'previous_missed_doses': data.get('previous_missed_doses', summary['missed']),
        'previous_taken_doses': data.get('previous_taken_doses', summary['taken']),
        'adherence_percentage': data.get('adherence_percentage', summary['adherence']),
        'reminder_response_time': data.get('reminder_response_time', 15),
        'number_of_active_medicines': data.get('number_of_active_medicines', Medicine.query.filter_by(patient_id=patient_id).count()),
        'reminder_preference': data.get('reminder_preference', 'web'),
        'same_time_missed_days': pattern['same_time_missed_days'],
        'missed_streak': pattern['same_time_missed_days'],
    }
    result = predict_risk(features)
    if pattern['alert']:
        result['alert'] = pattern['alert']
        if result.get('recommendation'):
            result['recommendation'] = pattern['alert']
    result['current_adherence'] = summary['adherence']; result['patient_name'] = patient.full_name
    return jsonify(success=True, prediction=result)


@app.post('/api/chatbot')
@jwt_required()
def chatbot():
    text = str((request.get_json() or {}).get('message', '')).lower()
    if any(word in text for word in ('diagnose', 'stop', 'change dose', 'symptom')):
        reply = "I can help manage medicine reminders, but I cannot diagnose conditions or change prescribed treatment. Please consult your doctor or pharmacist."
    elif 'miss' in text or 'adherence' in text:
        reply = "You can review missed, taken, and skipped doses in History. I can also run an adherence prediction from the AI Prediction page."
    elif 'schedule' in text or 'reminder' in text:
        reply = "Use Add Medicine to save a medicine, one or more daily times, and web/SMS/email preferences."
    elif 'upcoming' in text or 'today' in text:
        reply = "Your next scheduled dose appears on the Dashboard. Mark it Taken or Skipped after the dose is due."
    else:
        reply = "I can help with medicine schedules, reminder preferences, dose tracking, adherence, and navigating this application."
    return jsonify(success=True, reply=reply)


@app.post('/api/reminders/send')
@patient_only
def send_reminder():
    data = request.get_json() or {}; user = current_user(); medicine = Medicine.query.filter_by(id=data.get('medicine_id'), patient_id=user.id).first()
    if not medicine: return jsonify(success=False, message='Medicine not found'), 404
    channels = data.get('channels', ['web']); message = f"Medicine Reminder: It is time to take your {medicine.dosage} {medicine.dosage_unit} {medicine.medicine_name}."
    results = {}
    if 'sms' in channels: results['sms'] = send_sms(user.phone, message) if user.phone else (False, 'No phone number registered')
    if 'email' in channels: results['email'] = send_email(user.email, 'Medicine Reminder - Dose Due', f'<p>Hello {user.full_name},</p><p>{message}</p>')
    return jsonify(success=True, results={key: {'sent': value[0], 'message': value[1]} for key, value in results.items()})


with app.app_context():
    db.create_all()
    from scheduler import start_scheduler
    start_scheduler()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
