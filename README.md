# CarePrep

CarePrep is a full-stack appointment-preparation planner. Authenticated users create private appointments and maintain prioritized question lists for each visit.

This is an educational project that uses **fictional demonstration data only**. Do not enter real or sensitive medical information. CarePrep is an organizational tool; it does not diagnose conditions, recommend treatment, or connect to real medical records.

## Project goals

CarePrep turns scattered notes and reminders into a focused preparation workflow. It demonstrates:

- Session-based authentication with Flask-Login.
- Object-level authorization so users access only their own records.
- Relational data modeling with User, Appointment, and Question resources.
- RESTful CRUD operations for appointments and appointment questions.
- A responsive React interface with protected routes and auth-state restoration.
- Frontend and backend validation, error states, and automated backend tests.

## Features

- Register, log in, restore a session after refresh, and log out using Flask-Login sessions.
- Password hashing with Werkzeug using PBKDF2 for local macOS compatibility.
- Create, view, edit, and delete private appointments.
- Add, prioritize from 1–3, mark discussed, and delete questions for an appointment.
- Enforce server-side ownership on every appointment and question endpoint.
- Use protected React routes and conditional navigation.
- Display loading, empty, validation, error, and deletion-confirmation states.
- Serve the production React build from Flask when `client/dist` exists.

## Architecture

```text
User
  └── has many Appointments
         └── has many Questions
```

A Question is authorized through its parent Appointment. The browser never submits a trusted user ID; Flask derives identity from the authenticated session and verifies ownership server-side.

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React, Vite, React Router, JavaScript, CSS |
| Backend | Python, Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug |
| Database | SQLite locally; configurable with `DATABASE_URI` |
| Testing | Pytest |
| Quality checks | ESLint and Vite production build |
| Deployment | Gunicorn-ready; Flask production-build fallback |

## Local setup

### Prerequisites

Install:

- Python 3
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone [https://github.com/jhjulialee/careprep.git](https://github.com/jhjulialee/careprep.git)
cd careprep
```

### 2. Configure the backend

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Initialize the SQLite database and add fictional demo data:

```bash
flask --app server.app init-db
flask --app server.app seed
```

Start Flask:

```bash
flask --app server.app run --port 5555 --debug
```

The backend runs at:

```text
http://127.0.0.1:5555
```

### 3. Configure the frontend

In a second terminal:

```bash
cd careprep/client
npm install
npm run dev
```

Open the URL printed by Vite, normally:

```text
http://localhost:5173
```

Vite proxies `/api` requests to Flask on port 5555.

### Demo account

After running the seed command, sign in with this fictional demo account:

```text
Email: demo@careprep.test
Password: careprep123
```

## Tests and quality checks

From the project root, activate the virtual environment and run backend tests:

```bash
source .venv/bin/activate
PYTHONPATH=. pytest -q
```

Expected result:

```text
5 passed
```

Run frontend linting and the production build:

```bash
cd client
npm run lint
npm run build
```

The project should complete both commands without lint errors or build errors.

### Test coverage

The backend test suite verifies:

- Registration, login, authenticated-session restoration, and logout behavior.
- Appointment creation, update, and deletion.
- Question creation, discussed-status updates, and deletion.
- Validation errors for invalid registration and appointment data.
- Unauthenticated requests receive `401` responses from protected appointment routes.
- Cross-user isolation: a second authenticated user receives a `404` response when attempting to access another user’s appointment.

## Demo walkthrough

1. Register a fictional user account or sign in with the seeded demo account.
2. Create an appointment with fictional provider, date, location, and preparation notes.
3. Add questions, assign priorities from 1–3, and mark a question as discussed.
4. Edit and delete records to demonstrate complete CRUD functionality.
5. Refresh the browser to verify that the authenticated session is restored.
6. Log out, create a second test account, and verify it cannot access the first account’s appointment URL.
7. Visit `/appointments` while logged out and verify that the React protected route redirects to login.

## API routes

| Method | Endpoint | Access and purpose |
|---|---|---|
| POST | `/api/auth/register` | Public; create an account and authenticated session |
| POST | `/api/auth/login` | Public; verify credentials and start a session |
| GET | `/api/auth/me` | Authenticated; restore the current user |
| DELETE | `/api/auth/logout` | Authenticated; end the active session |
| GET | `/api/appointments` | Authenticated; list the current user’s appointments |
| POST | `/api/appointments` | Authenticated; create an appointment for the current user |
| GET | `/api/appointments/:id` | Owner-only; retrieve one appointment and its questions |
| PATCH | `/api/appointments/:id` | Owner-only; update one appointment |
| DELETE | `/api/appointments/:id` | Owner-only; delete one appointment and its questions |
| POST | `/api/appointments/:id/questions` | Owner-only; add a question to an owned appointment |
| PATCH | `/api/questions/:id` | Owner-only; update question text, priority, or discussed status |
| DELETE | `/api/questions/:id` | Owner-only; delete a question |

## Environment variables

Create `.env` from `.env.example`. Never commit `.env`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Long, unpredictable key used to sign Flask sessions |
| `DATABASE_URI` | SQLAlchemy database URL; defaults to local SQLite |
| `FLASK_ENV` | Set to `production` when deploying over HTTPS so session cookies are secure |

## Security and privacy notes

- Every protected API operation verifies `current_user` server-side.
- Appointment queries are filtered by the logged-in user’s ID.
- Question ownership is checked through the parent appointment.
- Cross-user and nonexistent records return `404`, helping avoid unnecessary data disclosure.
- Passwords are hashed with Werkzeug and never returned in API JSON.
- Invalid client input returns clear `400` responses.
- Unauthenticated protected requests return `401`.
- Only fictional demonstration content should be used.

## Production build

Build the React application:

```bash
cd client
npm install
npm run build
cd ..
```

When `client/dist` exists, Flask serves the React build and returns `index.html` for React client-side routes.

For a production server, initialize the database and run Gunicorn:

```bash
flask --app server.app init-db
gunicorn server.app:app
```

## Known limitations and future work

- Deployment is not configured for a specific host.
- Local SQLite is appropriate for a demonstration but not for multi-instance production hosting.
- The app uses browser confirmation dialogs for destructive actions; an undo workflow would improve the experience.
- Future improvements may include PostgreSQL deployment, Flask-Migrate migrations, password reset, email verification, reminders, calendar integration, filtering, pagination, frontend test coverage, accessibility audits, and additional deployment configuration.