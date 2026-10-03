import os
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__, static_folder=str(Path(__file__).resolve().parent.parent / 'client' / 'dist'), static_url_path='')
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'development-only-change-me'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URI', 'sqlite:///careprep.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = None

    from .models import User, Appointment, Question

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Authentication required.'}), 401

    def data():
        return request.get_json(silent=True) or {}

    def error(message, code=400):
        return jsonify({'error': message}), code

    def required_text(payload, field):
        value = payload.get(field, '')
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field.replace("_", " ").title()} is required.')
        return value.strip()

    def owned_appointment(appointment_id):
        return Appointment.query.filter_by(id=appointment_id, user_id=current_user.id).first()

    @app.post('/api/auth/register')
    def register():
        payload = data()
        email = str(payload.get('email', '')).strip().lower()
        password = str(payload.get('password', ''))
        if not email or '@' not in email:
            return error('Enter a valid email address.')
        if len(password) < 8:
            return error('Password must contain at least 8 characters.')
        if User.query.filter_by(email=email).first():
            return error('An account with that email already exists.')
        user = User(email=email, password_hash=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(user); db.session.commit(); login_user(user)
        return jsonify({'user': user.to_dict()}), 201

    @app.post('/api/auth/login')
    def login():
        payload = data(); email = str(payload.get('email', '')).strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, str(payload.get('password', ''))):
            return error('Invalid email or password.', 401)
        login_user(user)
        return jsonify({'user': user.to_dict()})

    @app.get('/api/auth/me')
    @login_required
    def me():
        return jsonify({'user': current_user.to_dict()})

    @app.delete('/api/auth/logout')
    @login_required
    def logout():
        logout_user()
        return '', 204

    @app.route('/api/appointments', methods=['GET', 'POST'])
    @login_required
    def appointments():
        if request.method == 'GET':
            rows = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.asc()).all()
            return jsonify({'appointments': [a.to_dict() for a in rows]})
        payload = data()
        try:
            provider = required_text(payload, 'provider'); date = required_text(payload, 'date')
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError as exc:
            return error(str(exc) if 'required' in str(exc) else 'Date must use YYYY-MM-DD.')
        appointment = Appointment(user_id=current_user.id, provider=provider, date=date,
            visit_type=str(payload.get('visit_type', 'General visit')).strip() or 'General visit',
            location=str(payload.get('location', '')).strip(), notes=str(payload.get('notes', '')).strip())
        db.session.add(appointment); db.session.commit()
        return jsonify({'appointment': appointment.to_dict()}), 201

    @app.route('/api/appointments/<int:appointment_id>', methods=['GET', 'PATCH', 'DELETE'])
    @login_required
    def appointment_detail(appointment_id):
        appointment = owned_appointment(appointment_id)
        if not appointment: return error('Appointment not found.', 404)
        if request.method == 'GET': return jsonify({'appointment': appointment.to_dict(True)})
        if request.method == 'DELETE':
            db.session.delete(appointment); db.session.commit(); return '', 204
        payload = data()
        try:
            if 'provider' in payload: appointment.provider = required_text(payload, 'provider')
            if 'date' in payload:
                datetime.strptime(required_text(payload, 'date'), '%Y-%m-%d'); appointment.date = payload['date'].strip()
        except ValueError as exc:
            return error(str(exc) if 'required' in str(exc) else 'Date must use YYYY-MM-DD.')
        for field in ('visit_type', 'location', 'notes'):
            if field in payload:
                setattr(appointment, field, str(payload[field]).strip())
        db.session.commit(); return jsonify({'appointment': appointment.to_dict(True)})

    @app.post('/api/appointments/<int:appointment_id>/questions')
    @login_required
    def create_question(appointment_id):
        if not (appointment := owned_appointment(appointment_id)): return error('Appointment not found.', 404)
        payload = data()
        try: text = required_text(payload, 'text')
        except ValueError as exc: return error(str(exc))
        priority = payload.get('priority', 2)
        if type(priority) is not int or priority not in (1, 2, 3): return error('Priority must be 1, 2, or 3.')
        question = Question(appointment_id=appointment.id, text=text, priority=priority)
        db.session.add(question); db.session.commit(); return jsonify({'question': question.to_dict()}), 201

    @app.route('/api/questions/<int:question_id>', methods=['PATCH', 'DELETE'])
    @login_required
    def question_detail(question_id):
        question = Question.query.join(Appointment).filter(Question.id == question_id, Appointment.user_id == current_user.id).first()
        if not question: return error('Question not found.', 404)
        if request.method == 'DELETE':
            db.session.delete(question); db.session.commit(); return '', 204
        payload = data()
        if 'text' in payload:
            try: question.text = required_text(payload, 'text')
            except ValueError as exc: return error(str(exc))
        if 'priority' in payload:
            if type(payload['priority']) is not int or payload['priority'] not in (1, 2, 3): return error('Priority must be 1, 2, or 3.')
            question.priority = payload['priority']
        if 'discussed' in payload:
            if type(payload['discussed']) is not bool: return error('Discussed must be true or false.')
            question.discussed = payload['discussed']
        db.session.commit(); return jsonify({'question': question.to_dict()})

    @app.cli.command('init-db')
    def init_db():
        db.create_all(); print('Database initialized.')

    @app.cli.command('seed')
    def seed():
        db.create_all()
        user = User.query.filter_by(email='demo@careprep.test').first()
        if not user:
            user = User(email='demo@careprep.test', password_hash=generate_password_hash('careprep123', method='pbkdf2:sha256'))
            db.session.add(user); db.session.flush()
        if not user.appointments:
            appointment = Appointment(user_id=user.id, provider='Dr. Rivera', visit_type='Annual checkup', date='2026-10-15', location='Fictional Health Center', notes='Bring a fictional insurance card and prior notes.')
            db.session.add(appointment); db.session.flush()
            db.session.add_all([Question(appointment_id=appointment.id, text='What preventive screenings should I discuss?', priority=1), Question(appointment_id=appointment.id, text='Can we review my wellness goals?', priority=2)])
        db.session.commit(); print('Fictional demo data seeded.')

    @app.get('/')
    @app.get('/<path:path>')
    def serve_client(path=''):
        if path.startswith('api/'):
            return error('Not found.', 404)
        dist = Path(app.static_folder)
        if (dist / 'index.html').exists():
            if path and (dist / path).exists(): return send_from_directory(dist, path)
            return send_from_directory(dist, 'index.html')
        return jsonify({'message': 'CarePrep API is running. Start Vite for the development client.'})

    return app

app = create_app()
