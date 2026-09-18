"""Generate clearly synthetic demo records for local demonstrations."""
from datetime import datetime, timedelta
import random
from faker import Faker
from werkzeug.security import generate_password_hash
from app import app, db, User, Medicine, DoseSchedule, DoseLog

fake = Faker(); random.seed(42)
with app.app_context():
    for index in range(100):
        patient = User(full_name=fake.name(), email=f'demo.patient.{index}@example.com', phone=f'+9190000{index:05d}', password_hash=generate_password_hash('DemoPass123!'), role='patient', reminder_preferences={'web': True, 'sms': False, 'email': False})
        relative = User(full_name=fake.name(), email=f'demo.relative.{index}@example.com', phone=f'+9180000{index:05d}', password_hash=generate_password_hash('DemoPass123!'), role='relative')
        db.session.add_all([patient, relative]); db.session.flush()
        for medicine_index in range(random.randint(1, 3)):
            medicine = Medicine(patient_id=patient.id, medicine_name=random.choice(['Paracetamol', 'Vitamin D', 'Metformin', 'Amlodipine']), dosage=random.choice(['250', '500', '10']), dosage_unit='mg', frequency='Once daily', start_date=(datetime.utcnow() - timedelta(days=45)).date().isoformat(), instructions='Take as prescribed')
            db.session.add(medicine); db.session.flush(); schedule = DoseSchedule(medicine_id=medicine.id, scheduled_time=random.choice(['08:00', '13:00', '20:00']), frequency=medicine.frequency); db.session.add(schedule); db.session.flush()
            for day in range(30):
                status = random.choices(['taken', 'missed', 'skipped'], weights=[78, 15, 7])[0]
                db.session.add(DoseLog(patient_id=patient.id, medicine_id=medicine.id, schedule_id=schedule.id, scheduled_time=schedule.scheduled_time, actual_time=datetime.utcnow() - timedelta(days=day) if status == 'taken' else None, status=status, created_at=datetime.utcnow() - timedelta(days=day)))
    db.session.commit(); print('Created synthetic demo records. All demo passwords are DemoPass123!.')
