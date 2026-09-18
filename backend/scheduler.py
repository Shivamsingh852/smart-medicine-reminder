"""Optional reminder scheduler. Run alongside the API after provider keys are configured."""
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
# Imports will be loaded inside functions to avoid circular imports
from services.email_service import send_email
from services.twilio_service import send_sms


def _parse_time(value):
    try:
        return datetime.strptime(str(value), '%H:%M').time()
    except (TypeError, ValueError):
        return None


def check_due_reminders():
    from app import app, db, User, Medicine, DoseSchedule, Reminder, DoseLog, reconcile_missed_doses
    now = datetime.now()
    grace_period = timedelta(minutes=5)
    with app.app_context():
        for patient in User.query.filter_by(role='patient').all():
            reconcile_missed_doses(patient.id)
        for schedule in DoseSchedule.query.filter_by(active=True).all():
            due_time = _parse_time(schedule.scheduled_time)
            if due_time is None:
                continue
            due_today = datetime.combine(now.date(), due_time)
            due_yesterday = datetime.combine(now.date() - timedelta(days=1), due_time)
            if due_today > now and due_yesterday > now:
                continue
            medicine = Medicine.query.get(schedule.medicine_id)
            if medicine is None:
                continue
            user = User.query.get(medicine.patient_id)
            if user is None:
                continue
            existing_today = DoseLog.query.filter_by(
                patient_id=user.id,
                medicine_id=medicine.id,
                schedule_id=schedule.id,
            ).filter(
                DoseLog.created_at >= datetime.combine(now.date(), datetime.min.time()),
                DoseLog.created_at < datetime.combine(now.date() + timedelta(days=1), datetime.min.time()),
            ).order_by(DoseLog.created_at.desc()).first()
            if existing_today is None:
                prior_log = DoseLog.query.filter_by(
                    patient_id=user.id,
                    medicine_id=medicine.id,
                    schedule_id=schedule.id,
                ).filter(
                    DoseLog.created_at >= datetime.combine(now.date() - timedelta(days=1), datetime.min.time()),
                    DoseLog.created_at < datetime.combine(now.date(), datetime.min.time()),
                ).order_by(DoseLog.created_at.desc()).first()
                if due_yesterday + grace_period <= now and prior_log is None:
                    db.session.add(DoseLog(
                        patient_id=user.id,
                        medicine_id=medicine.id,
                        schedule_id=schedule.id,
                        scheduled_time=schedule.scheduled_time,
                        status='missed',
                        actual_time=None,
                        created_at=due_yesterday,
                    ))
                    continue
                if due_today + grace_period <= now:
                    db.session.add(DoseLog(
                        patient_id=user.id,
                        medicine_id=medicine.id,
                        schedule_id=schedule.id,
                        scheduled_time=schedule.scheduled_time,
                        status='missed',
                        actual_time=None,
                        created_at=now,
                    ))
            elif existing_today.status in {'taken', 'skipped'}:
                continue
            duplicate = Reminder.query.filter_by(
                patient_id=user.id,
                medicine_id=medicine.id,
                dose_schedule_id=schedule.id,
                scheduled_time=now.replace(second=0, microsecond=0)
            ).first()
            if duplicate:
                continue
            message = f"Medicine Reminder: It is time to take your {medicine.dosage} {medicine.dosage_unit} {medicine.medicine_name}."
            reminder = Reminder(
                patient_id=user.id,
                medicine_id=medicine.id,
                dose_schedule_id=schedule.id,
                reminder_type='web',
                scheduled_time=now,
                status='sent',
                sent_at=now,
                message=message
            )
            db.session.add(reminder)
            prefs = user.reminder_preferences or {}
            if prefs.get('sms') and user.phone:
                send_sms(user.phone, message)
            if prefs.get('email'):
                send_email(user.email, 'Medicine Reminder - Dose Due', f"<p>{message}</p>")
        db.session.commit()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_due_reminders, 'interval', minutes=1)
    scheduler.start()

if __name__ == '__main__':
    start_scheduler()

