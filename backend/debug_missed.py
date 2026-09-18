from datetime import datetime, timedelta
from app import app, db, User, Medicine, DoseSchedule, DoseLog, reconcile_missed_doses
from scheduler import _parse_time, check_due_reminders

with app.app_context():
    db.drop_all()
    db.create_all()
    user = User(full_name='P', email='x@example.com', password_hash='x', role='patient')
    db.session.add(user)
    db.session.commit()
    med = Medicine(patient_id=user.id, medicine_name='M', dosage='1', dosage_unit='mg', frequency='Once daily', start_date='2026-01-01')
    db.session.add(med)
    db.session.flush()
    sched = DoseSchedule(medicine_id=med.id, scheduled_time=(datetime.utcnow() - timedelta(minutes=30)).strftime('%H:%M'), frequency=med.frequency)
    db.session.add(sched)
    db.session.commit()
    now = datetime.now()
    due_time = _parse_time(sched.scheduled_time)
    print('before', sched.scheduled_time, now.strftime('%H:%M'))
    print('due_time', due_time, 'now_time', now.time(), 'due_time > now?', due_time > now.time(), 'due_time <= now?', due_time <= now.time())
    print('count before', DoseLog.query.count())
    reconcile_missed_doses(user.id)
    print('count after reconcile', DoseLog.query.count())
    print('rows after reconcile', [(r.patient_id, r.medicine_id, r.schedule_id, r.status, r.scheduled_time) for r in DoseLog.query.all()])
    check_due_reminders()
    print('count after scheduler', DoseLog.query.count())
    print('rows after scheduler', [(r.patient_id, r.medicine_id, r.schedule_id, r.status, r.scheduled_time) for r in DoseLog.query.all()])
