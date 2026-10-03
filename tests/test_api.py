import pytest
from server.app import create_app, db

@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context(): db.create_all()
    yield app

@pytest.fixture
def client(app): return app.test_client()

def register(client, email='one@test.com', password='password1'):
    return client.post('/api/auth/register', json={'email': email, 'password': password})

def test_register_login_and_session(client):
    assert register(client).status_code == 201
    assert client.get('/api/auth/me').get_json()['user']['email'] == 'one@test.com'
    assert client.delete('/api/auth/logout').status_code == 204
    assert client.get('/api/auth/me').status_code == 401
    assert client.post('/api/auth/login', json={'email': 'one@test.com', 'password': 'password1'}).status_code == 200

def test_appointment_and_question_crud(client):
    register(client)
    created = client.post('/api/appointments', json={'provider': 'Dr. Test', 'date': '2026-10-20'}).get_json()['appointment']
    aid = created['id']
    assert client.patch(f'/api/appointments/{aid}', json={'notes': 'Bring notes'}).status_code == 200
    question = client.post(f'/api/appointments/{aid}/questions', json={'text': 'What should I ask?', 'priority': 1}).get_json()['question']
    assert client.patch(f"/api/questions/{question['id']}", json={'discussed': True}).get_json()['question']['discussed'] is True
    assert client.delete(f"/api/questions/{question['id']}").status_code == 204
    assert client.delete(f'/api/appointments/{aid}').status_code == 204

def test_cross_user_isolation(client):
    register(client, 'first@test.com')
    appointment = client.post('/api/appointments', json={'provider': 'Dr. First', 'date': '2026-10-21'}).get_json()['appointment']
    client.delete('/api/auth/logout')
    register(client, 'second@test.com')
    assert client.get(f"/api/appointments/{appointment['id']}").status_code == 404
    assert client.patch(f"/api/appointments/{appointment['id']}", json={'provider': 'Nope'}).status_code == 404

def test_validation(client):
    assert register(client, password='short').status_code == 400
    register(client)
    assert client.post('/api/appointments', json={'provider': '', 'date': 'nope'}).status_code == 400
