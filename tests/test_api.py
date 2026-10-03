import pytest

from server.app import create_app, db


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            'TESTING': True,
            'SECRET_KEY': 'test',
            'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'test.db'}",
        }
    )

    with app.app_context():
        db.create_all()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, email='one@test.com', password='password1'):
    return client.post(
        '/api/auth/register',
        json={
            'email': email,
            'password': password,
        },
    )


def test_register_login_and_session(client):
    assert register(client).status_code == 201

    response = client.get('/api/auth/me')
    assert response.status_code == 200
    assert response.get_json()['user']['email'] == 'one@test.com'

    assert client.delete('/api/auth/logout').status_code == 204

    assert client.get('/api/auth/me').status_code == 401

    response = client.post(
        '/api/auth/login',
        json={
            'email': 'one@test.com',
            'password': 'password1',
        },
    )
    assert response.status_code == 200


def test_appointment_and_question_crud(client):
    register(client)

    response = client.post(
        '/api/appointments',
        json={
            'provider': 'Dr. Test',
            'date': '2026-10-20',
        },
    )
    assert response.status_code == 201

    appointment = response.get_json()['appointment']
    appointment_id = appointment['id']

    response = client.patch(
        f'/api/appointments/{appointment_id}',
        json={
            'notes': 'Bring notes',
        },
    )
    assert response.status_code == 200
    assert response.get_json()['appointment']['notes'] == 'Bring notes'

    response = client.post(
        f'/api/appointments/{appointment_id}/questions',
        json={
            'text': 'What should I ask?',
            'priority': 1,
        },
    )
    assert response.status_code == 201

    question = response.get_json()['question']
    question_id = question['id']

    response = client.patch(
        f'/api/questions/{question_id}',
        json={
            'discussed': True,
        },
    )
    assert response.status_code == 200
    assert response.get_json()['question']['discussed'] is True

    assert client.delete(f'/api/questions/{question_id}').status_code == 204
    assert client.delete(f'/api/appointments/{appointment_id}').status_code == 204


def test_cross_user_isolation(client):
    register(client, 'first@test.com')

    response = client.post(
        '/api/appointments',
        json={
            'provider': 'Dr. First',
            'date': '2026-10-21',
        },
    )
    assert response.status_code == 201

    appointment = response.get_json()['appointment']

    assert client.delete('/api/auth/logout').status_code == 204

    register(client, 'second@test.com')

    assert client.get(
        f"/api/appointments/{appointment['id']}"
    ).status_code == 404

    response = client.patch(
        f"/api/appointments/{appointment['id']}",
        json={
            'provider': 'Nope',
        },
    )
    assert response.status_code == 404


def test_validation(client):
    assert register(client, password='short').status_code == 400

    register(client)

    response = client.post(
        '/api/appointments',
        json={
            'provider': '',
            'date': 'nope',
        },
    )
    assert response.status_code == 400


def test_protected_routes_require_authentication(client):
    assert client.get('/api/appointments').status_code == 401

    response = client.post(
        '/api/appointments',
        json={
            'provider': 'Dr. Test',
            'date': '2026-10-20',
        },
    )
    assert response.status_code == 401

    assert client.get('/api/appointments/1').status_code == 401