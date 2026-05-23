import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    token = Token.objects.get_or_create(user=user)[0]
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.mark.django_db
class TestRegister:
    def test_register_success(self, api_client):
        response = api_client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        assert response.status_code == 201
        assert response.data['user']['username'] == 'newuser'
        assert 'token' in response.data

    def test_register_password_mismatch(self, api_client):
        response = api_client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'wrongpass'
        })
        assert response.status_code == 400
        assert 'password' in response.data

    def test_register_duplicate_username(self, api_client, user):
        response = api_client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'pass123',
            'password_confirm': 'pass123'
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user):
        response = api_client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        assert response.data['user']['username'] == 'testuser'
        assert 'token' in response.data

    def test_login_invalid_credentials(self, api_client, user):
        response = api_client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        assert response.status_code == 400

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post('/api/auth/login/', {
            'username': 'nonexistent',
            'password': 'pass123'
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogout:
    def test_logout_success(self, authenticated_client, user):
        response = authenticated_client.post('/api/auth/logout/')
        assert response.status_code == 200
        assert response.data['detail'] == 'Successfully logged out.'

    def test_logout_unauthenticated(self, api_client):
        response = api_client.post('/api/auth/logout/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestMe:
    def test_me_authenticated(self, authenticated_client, user):
        response = authenticated_client.get('/api/users/me/')
        assert response.status_code == 200
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'

    def test_me_unauthenticated(self, api_client):
        response = api_client.get('/api/users/me/')
        assert response.status_code == 401
