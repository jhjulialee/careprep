# CarePrep

CarePrep is a full-stack appointment-preparation planner. Authenticated users create private appointments and maintain prioritized question lists for each visit. It is an educational project that uses **fictional demonstration data only**; do not enter real or sensitive medical information.

## Project goals

CarePrep turns scattered notes and reminders into a focused preparation workflow. It demonstrates session authentication, object-level authorization, relational data modeling, RESTful CRUD, a responsive React interface, validation, and automated backend tests.

## Features

- Register, log in, restore a session after refresh, and log out using Flask-Login sessions.
- Create, view, edit, and delete private appointments.
- Add, edit, prioritize (1–3), mark discussed, and delete questions for each appointment.
- Enforce server-side ownership on every appointment and question endpoint.
- Use protected client routes, conditional navigation, loading, empty, validation, error, and confirmation states.
- Serve the production React build from Flask when `client/dist` exists.

## Architecture

`User 1 → many Appointment 1 → many Question`

A Question is authorized through its parent Appointment. The browser never submits a trusted user ID; Flask derives identity from the authenticated session.

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React, Vite, React Router, JavaScript, CSS |
| Backend | Python, Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug |
| Database | SQLite locally; configurable with `DATABASE_URI` |
| Testing | Pytest |
| Deployment | Gunicorn-ready; Flask production-build fallback |

## Local setup

### 1. Backend

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows PowerShell: Copy-Item .env.example .env
flask --app server.app init-db
flask --app server.app run --port 5555 --debug
```

### 2. Frontend

In a second terminal:

```bash
cd client
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to Flask on port 5555.

### Demo account

Seed optional fictional data with:

```bash
flask --app server.app seed
```

Then sign in with `demo@careprep.test` / `careprep123`.

## Tests and checks

```bash
PYTHONPATH=. pytest -q
cd client
npm run lint
npm run build
```

## API routes

| Method | Endpoint | Access and purpose |
|---|---|---|
| POST | `/api/auth/register` | Public; create account and authenticated session |
| POST | `/api/auth/login` | Public; verify credentials and start session |
| GET | `/api/auth/me` | Authenticated; restore current user |
| DELETE | `/api/auth/logout` | Authenticated; end session |
| GET/POST | `/api/appointments` | List or create current user’s appointments |
| GET/PATCH/DELETE | `/api/appointments/:id` | Owner-only appointment operations |
| POST | `/api/appointments/:id/questions` | Add a question to an owned appointment |
| PATCH/DELETE | `/api/questions/:id` | Owner-only question operations |

## Environment variables

- `SECRET_KEY`: long, unpredictable key used to sign sessions.
- `DATABASE_URI`: SQLAlchemy database URL; defaults to a local SQLite file.
- `FLASK_ENV=production`: enables secure cookies for HTTPS deployment.

Never commit `.env`, real health information, or a production database file.

## Production build

```bash
cd client && npm install && npm run build
cd ..
flask --app server.app init-db
gunicorn server.app:app
```

When `client/dist` exists, Flask serves it and returns `index.html` for React client-side routes.

## Quality and security notes

- Every protected API operation verifies `current_user` server-side.
- Nonexistent and cross-user records return `404`, avoiding data disclosure.
- Passwords are hashed with Werkzeug and never returned in API JSON.
- Input validation uses clear `400` errors; unauthenticated requests receive `401`.
- SQLite is appropriate for a local demonstration. A multi-instance production deployment should use PostgreSQL, migrations, HTTPS, a strong secret, and secure operational controls.

## Known limitations and future work

Deployment is not configured for a specific host. Future improvements include password reset/email verification, reminders, calendar integration, PostgreSQL deployment, pagination, filtering, frontend tests, accessibility audits, and an undo workflow for destructive actions.
