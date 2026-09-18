from datetime import date, datetime, timedelta

import pytest
from app import app, db, DoseLog, Medicine, DoseSchedule

@pytest.fixture()
def client(tmp_path):
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI=f'sqlite:///{tmp_path / "test.db"}', JWT_SECRET_KEY='test')
    with app.app_context(): db.drop_all(); db.create_all()
    with app.test_client() as test_client: yield test_client
    with app.app_context(): db.drop_all()

def test_register_login_and_medicine(client):
    response = client.post('/api/auth/register', json={'full_name': 'Test Patient', 'email': 'test@example.com', 'password': 'Password123!', 'role': 'patient'})
    assert response.status_code == 201
    token = response.json['token']; headers = {'Authorization': f'Bearer {token}'}
    login = client.post('/api/auth/login', json={'email': 'test@example.com', 'password': 'Password123!'})
    assert login.status_code == 200
    medicine = client.post('/api/medicines', headers=headers, json={'medicine_name': 'Paracetamol', 'dosage': '500', 'start_date': '2026-01-01', 'timings': ['08:00']})
    assert medicine.status_code == 201

def test_invalid_login(client):
    client.post('/api/auth/register', json={'full_name': 'Test', 'email': 'test@example.com', 'password': 'Password123!', 'role': 'patient'})
    assert client.post('/api/auth/login', json={'email': 'test@example.com', 'password': 'bad'}).status_code == 401


def test_overdue_medicine_is_marked_missed(client):
    response = client.post('/api/auth/register', json={'full_name': 'Patient', 'email': 'patient@example.com', 'password': 'Password123!', 'role': 'patient'})
    token = response.json['token']
    headers = {'Authorization': f'Bearer {token}'}

    medicine = client.post('/api/medicines', headers=headers, json={
        'medicine_name': 'Amlodipine',
        'dosage': '10',
        'start_date': '2026-01-01',
        'timings': [datetime.utcnow().strftime('%H:%M')]
    })
    schedule_id = medicine.json['medicine']['schedules'][0]['id']

    with app.app_context():
        schedule = DoseSchedule.query.get(schedule_id)
        schedule.scheduled_time = (datetime.utcnow() - timedelta(minutes=30)).strftime('%H:%M')
        db.session.commit()

    from scheduler import check_due_reminders
    check_due_reminders()

    with app.app_context():
        log = DoseLog.query.filter_by(patient_id=response.json['user']['id'], schedule_id=schedule_id).first()
        assert log is not None
        assert log.status == 'missed'


def test_dose_remains_actionable_for_five_minute_grace_period(client):
    response = client.post('/api/auth/register', json={'full_name': 'Patient', 'email': 'grace@example.com', 'password': 'Password123!', 'role': 'patient'})
    headers = {'Authorization': f"Bearer {response.json['token']}"}
    medicine = client.post('/api/medicines', headers=headers, json={
        'medicine_name': 'Aspirin',
        'dosage': '100',
        'start_date': '2026-01-01',
        'timings': [(datetime.now() - timedelta(minutes=3)).strftime('%H:%M')]
    })
    schedule_id = medicine.json['medicine']['schedules'][0]['id']

    with app.app_context():
        schedule = DoseSchedule.query.get(schedule_id)
        schedule.scheduled_time = (datetime.now() - timedelta(minutes=3)).strftime('%H:%M')
        db.session.commit()

    result = client.get('/api/doses/today', headers=headers)
    dose = next(item for item in result.json['doses'] if item['schedule_id'] == schedule_id)
    assert dose['status'] == 'upcoming'


def test_prediction_alert_for_repeated_missed_doses(client):
    response = client.post('/api/auth/register', json={'full_name': 'Patient', 'email': 'patient2@example.com', 'password': 'Password123!', 'role': 'patient'})
    token = response.json['token']
    headers = {'Authorization': f'Bearer {token}'}

    medicine = client.post('/api/medicines', headers=headers, json={
        'medicine_name': 'Vitamin D',
        'dosage': '500',
        'start_date': '2026-01-01',
        'timings': ['08:00']
    })
    schedule_id = medicine.json['medicine']['schedules'][0]['id']

    with app.app_context():
        for offset in range(4):
            missed_day = date.today() - timedelta(days=offset)
            created_at = datetime.combine(missed_day, datetime.strptime('08:30', '%H:%M').time())
            db.session.add(DoseLog(
                patient_id=response.json['user']['id'],
                medicine_id=medicine.json['medicine']['id'],
                schedule_id=schedule_id,
                scheduled_time='08:00',
                actual_time=None,
                status='missed',
                created_at=created_at
            ))
        db.session.commit()

    result = client.post('/api/predict', headers=headers)
    assert result.status_code == 200
    prediction = result.json['prediction']
    assert 'alert' in prediction or 'alert' in result.json
    assert prediction['risk'] in {'Moderate', 'High'}
