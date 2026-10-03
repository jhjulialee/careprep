from flask_login import UserMixin
from .app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    appointments = db.relationship('Appointment', backref='user', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'email': self.email}

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    provider = db.Column(db.String(120), nullable=False)
    visit_type = db.Column(db.String(120), nullable=False, default='General visit')
    date = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(180), default='')
    notes = db.Column(db.Text, default='')
    questions = db.relationship('Question', backref='appointment', cascade='all, delete-orphan', lazy=True)

    def to_dict(self, include_questions=False):
        data = {'id': self.id, 'provider': self.provider, 'visit_type': self.visit_type, 'date': self.date, 'location': self.location, 'notes': self.notes}
        if include_questions:
            data['questions'] = [q.to_dict() for q in sorted(self.questions, key=lambda q: (q.priority, q.id))]
        return data

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=2)
    discussed = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {'id': self.id, 'appointment_id': self.appointment_id, 'text': self.text, 'priority': self.priority, 'discussed': self.discussed}
