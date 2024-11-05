import pytest
from rest_framework.reverse import reverse
from user.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken


# Registration tests
@pytest.mark.django_db
def test_user_register_api_success(client):
    data = {
        "username": "Testuser",
        "email": "testuser@gmail.com",
        "password": "Password@123"
    }
    
    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 201


@pytest.mark.django_db
def test_user_register_api_already_registered(client):
    data = {
        "username": "Testuser",
        "email": "testuser@gmail.com",
        "password": "Password@123"
    }
    
    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db 
def test_user_registration_missing_fields(client):
    data = {
        "username": "Testuser",
        "email": "testuser@gmail.com"
    }

    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

@pytest.mark.django_db 
def test_user_registration_missing_all_fields(client):
    data = {}
    
    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

@pytest.mark.django_db
def test_user_register_invalid_username(client):
    data = {
        "username": "test",
        "email": "testuser@gmail.com",
        "password": "Password@123"
    }

    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

@pytest.mark.django_db
def test_user_register_invalid_email(client):
    data = {
        "username": "Testuser",
        "email": "testusergmail.com",
        "password": "Password@123"
    }

    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

@pytest.mark.django_db
def test_user_register_invalid_password(client):
    data = {
        "username": "Testuser",
        "email": "testuser@gmail.com",
        "password": "Password123"
    }

    url = reverse('register')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

# Login Tests
@pytest.mark.django_db
def test_user_login_api_success(client):
    user = CustomUser.objects.create_user(
        username='TestUser',
        email='testuser@example.com',
        password='Password@123'
    )

    data = {
        "email": "testuser@example.com",
        "password": "Password@123"
    }

    url = reverse('login')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 200
    assert 'access' in response.data

@pytest.mark.django_db
def test_user_login_api_invalid_credentials(client):
    data = {
        "email": "testuser@example.com",
        "password": "Password@123"
    }

    url = reverse('login')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

@pytest.mark.django_db
def test_login_user_missing_field(client):
    data = {
        "email": "testuser@example.com",
    }

    url = reverse('login')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

@pytest.mark.django_db
def test_missing_login_all_fields(client):
    data = {}

    url = reverse('login')
    response = client.post(path=url, data=data, content_type='application/json')
    assert response.status_code == 400

# Verify Registered User
@pytest.mark.django_db
def test_verify_registered_user_valid_token(client):
    user = CustomUser.objects.create_user(
        username='TestUser',
        email='testuser@example.com',
        password='strongpassword123'
    )
    token = RefreshToken.for_user(user).access_token
    encoded_token = str(token)
    url = reverse('verify_user', args=[encoded_token])
    response = client.get(path=url)
    assert response.status_code == 200
    assert response.data['message'] == "User verification successful"
    
@pytest.mark.django_db
def test_verify_registered_user_invalid_token(client):
    invalid_token = "invalid.token.value"
    url = reverse('verify_user', args=[invalid_token])
    response = client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == "Invalid or expired token"