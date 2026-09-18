# Smart Medicine Reminder with AI

A functional academic full-stack application for patient medicine reminders and authorized relative/caregiver monitoring. The supplied workbook in `dataset/Smart_Medicine_Reminder_dataset_Final.xlsx` is used by the Random Forest training pipeline. It is treated as project/demo data; do not use it as a production clinical database.

## Features

- JWT authentication with patient and relative roles
- SQLite persistence through SQLAlchemy
- Medicine CRUD with multiple daily schedule times
- Web dose check-in: taken, skipped, and historical records
- Weekly/monthly adherence summaries
- Random Forest missed-dose prediction with explainable support language
- Rule-based chatbot for scheduling, reminders, adherence, and safe boundaries
- Optional Twilio SMS and Resend email integrations with graceful missing-key failures
- Relative linking by registered email and authorization checks
- Optional APScheduler process for due reminders
- Responsive React/Vite dashboard

## Structure

- `backend/app.py`: Flask API, models, auth, authorization, and REST routes
- `backend/ml/`: workbook preprocessing, training, evaluation, and prediction
- `backend/services/`: Twilio and Resend adapters
- `backend/seed_demo.py`: synthetic local data generator
- `frontend/src/`: React routes, pages, API client, auth context, and styles
- `dataset/`: supplied training workbook

## Run locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

The API runs at `http://localhost:5000`. The database is created automatically on first start.

Train and inspect the model explicitly:

```powershell
python -m ml.train_model
```

Generate synthetic demo records (optional):

```powershell
python seed_demo.py
```

To run the optional scheduler in another terminal:

```powershell
python scheduler.py
```

### Frontend

Install Node.js 20+ first, then:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Environment variables

`backend/.env.example` contains SQLite, JWT, timezone, Twilio, and Resend settings. Provider credentials never enter frontend code. Without Twilio/Resend settings, reminder requests return a structured `not configured` result and web tracking still works.

## Core API

- `POST /api/auth/register`, `POST /api/auth/login`
- `GET/PUT /api/users/me`
- `POST /api/relatives/link`, `GET /api/relatives/patients`
- `POST/GET/PUT/DELETE /api/medicines`
- `GET /api/doses/today`, `GET /api/doses/history`
- `POST /api/doses/:schedule_id/taken`, `POST /api/doses/:schedule_id/skipped`
- `GET /api/analytics/weekly`, `GET /api/analytics/monthly`
- `POST /api/predict`, `POST /api/chatbot`, `POST /api/reminders/send`

## ML methodology

The workbook has 10,001 records and 20 columns. The model target is `Missed_Dose`. The training pipeline only uses pre-outcome variables: age, frequency, numeric dose, historical missed count, historical confirmation delay, confirmation channel, and follow-up reminder time. Patient names, contact details, prescription text, and the future target are excluded to reduce leakage and privacy exposure. It reports accuracy, precision, recall, F1, confusion matrix, class distribution, and the selected feature list. The prediction is decision support, not a diagnosis.

## Testing

The backend is structured for Flask test-client coverage. Add provider credentials only in `.env`; mocked Twilio/Resend tests should assert both successful sends and graceful failures. A basic manual acceptance flow is: register, login, add medicine, open Dashboard, mark a dose Taken/Skipped, open History/Analytics, run AI Prediction, and test chatbot safety language.

## Screenshots

_Add screenshots here after running the Vite frontend._

## Future improvements

Background missed-dose reconciliation, refresh-token rotation, timezone-aware per-user schedules, invitation email flow, Alembic migrations, richer chart series, and an external LLM adapter behind a feature flag.

## Disclaimer

This app is an educational reminder and adherence-tracking project. It does not diagnose, prescribe, change dosage, or replace a doctor or pharmacist.
