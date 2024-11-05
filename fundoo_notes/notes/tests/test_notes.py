import pytest
from rest_framework.reverse import reverse
from rest_framework import status
import json
from user.models import CustomUser
from labels.models import Label
from notes.models import Note

@pytest.fixture
def create_user(client):
    data = {
        "username": "Testuser",
        "email": "testuser@gmail.com",
        "password": "Password@123"
    }
    url = reverse('register')
    response = client.post(url, data=data, content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED, f"User creation failed: {response.data}"
    return data

@pytest.fixture
def create_user_two(client):
    data = {
        "username": "UserTwo",
        "email": "usertwo@gmail.com",
        "password": "Password@123"
    }
    url = reverse('register')
    response = client.post(url, data=data, content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED, f"User creation failed: {response.data}"
    return data

@pytest.fixture
def generate_usertoken(client, create_user):
    data = {
        "email": create_user['email'],
        "password": create_user['password']
    }
    url = reverse('login')
    response = client.post(url, data=data, content_type='application/json')

    assert response.status_code == status.HTTP_200_OK, f"Login failed: {response.data}"
    return response.data["access"]

@pytest.fixture
def generate_usertoken_two(client, create_user_two):
    data = {
        "email": create_user_two['email'],
        "password": create_user_two['password']
    }
    url = reverse('login')
    response = client.post(url, data=data, content_type='application/json')

    assert response.status_code == status.HTTP_200_OK, f"Login failed: {response.data}"
    return response.data["access"]

@pytest.fixture
def create_note(client, generate_usertoken):
    NOTE_DATA = {
        "title": "Test Notes",
        "description": "This is the description of my test note.",
        "color": "violet",
        "is_archive": False,
        "is_trash": False
    }
    url = reverse('notes-list')
    response = client.post(
        url,
        HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
        data=NOTE_DATA,
        content_type='application/json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.data['data']['id']  # Return the created note ID

@pytest.mark.django_db
class TestNotes:

    def test_note_create(self, client, generate_usertoken):
        NOTE_DATA = {
        "title": "Test Notes",
        "description": "This is the description of my test note.",
        "color": "violet",
        "is_archive": False,
        "is_trash": False
        }
        url = reverse('notes-list')
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=NOTE_DATA,
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_all_note_user_one(self, client, generate_usertoken):
        url = reverse('notes-list')
        response = client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_update_note(self, client, generate_usertoken, create_note):
        note_id = create_note
        data = {
            "title": "Updated Test Notes",
            "description": "Updated description"
        }
        url = reverse('notes-detail', args=[note_id])
        response = client.put(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', data=data, content_type='application/json')

        assert response.status_code == status.HTTP_200_OK

    def test_delete_note(self, client, generate_usertoken, create_note):
        note_id = create_note
        url = reverse('notes-detail', args=[note_id])
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')

        assert response.status_code == 204

    def test_retrieve_note(self, client, generate_usertoken, create_note):
            note_id = create_note
            url = reverse('notes-detail', args=[note_id])
            response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')

            assert response.status_code == 200
    
    def test_note_retrieve_invalid_id(self, client, generate_usertoken):
        url = reverse('notes-detail', kwargs={"pk": 999})
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')
        assert response.status_code == 500

    def test_note_create_invalid_token(self, client):
        url = reverse('notes-list')
        invalid_token = "invalid.user.token"
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {invalid_token}',
            data={"title": "Invalid Note", "description": "Test"},
            content_type='application/json'
        )
        assert response.status_code == 401

    def test_note_create_invalid_data(self, client, generate_usertoken):
        url = reverse('notes-list')
        data = {
            "description": "This is the description of my test note.",
            "color": "violet",
            "is_archive": False,
            "is_trash": False
        }
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=data,
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_note_delete_invalid_id(self, client, generate_usertoken):
        url = reverse('notes-detail', kwargs={"pk": 999})
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')
        assert response.status_code == 500

    def test_note_toggle_archive(self, client, generate_usertoken, create_note):
        note_id = create_note
        url = reverse('notes-toggle-archive', args=[note_id])
        response = client.patch(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')
        assert response.status_code == 200

    def test_note_toggle_trash(self, client, generate_usertoken, create_note):
        note_id = create_note
        url = reverse('notes-toggle-trash', args=[note_id])
        response = client.patch(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')
        assert response.status_code == 200

    def test_note_archived(self, client, generate_usertoken):
        url = reverse('notes-archived')
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')
        assert response.status_code == 200

    def test_note_trashed(self, client, generate_usertoken):
        url = reverse('notes-trashed')
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', content_type='application/json')
        assert response.status_code == 200

    def test_add_collaborator(self, client, generate_usertoken, create_note, generate_usertoken_two):
        url = reverse('notes-add-collaborator')
        data = {
            "note_id": create_note,
            "user_ids": [CustomUser.objects.get(email="usertwo@gmail.com").id],
            "access_type": "read_only"
        }
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert response.data["message"] == "Collaborators processed successfully"
    
    def test_add_collaborator_invalid_user(self, client, generate_usertoken, create_note):
        url = reverse('notes-add-collaborator')
        data = {
            "note_id": create_note,
            "user_ids": [9999],  
            "access_type": "read_only"
        }
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"
        assert "Invalid user IDs" in response.data["message"]

    def test_remove_collaborator(self, client, generate_usertoken, create_note, generate_usertoken_two):
        """
        Test removing a collaborator from a note.
        """
        # First, add a collaborator
        add_collaborator_url = reverse('notes-add-collaborator')
        data = {
            "note_id": create_note,
            "user_ids": [CustomUser.objects.get(email="usertwo@gmail.com").id],
            "access_type": "read_only"
        }
        client.post(
            add_collaborator_url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=json.dumps(data),
            content_type='application/json'
        )

        # Now, remove the collaborator
        remove_collaborator_url = reverse('notes-remove-collaborator')
        data = {
            "note_id": create_note,
            "collaborator_ids": [CustomUser.objects.get(email="usertwo@gmail.com").id]
        }
        response = client.post(
            remove_collaborator_url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert response.data["message"] == "Collaborators removed successfully"

    def test_remove_invalid_collaborator(self, client, generate_usertoken, create_note, generate_usertoken_two):
            remove_collaborator_url = reverse('notes-remove-collaborator')
            data = {
                "note_id": create_note,
                "collaborator_ids": [CustomUser.objects.get(email="usertwo@gmail.com").id]
            }
            response = client.post(
                remove_collaborator_url,
                HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
                data=json.dumps(data),
                content_type='application/json'
            )
            assert response.status_code == 400
            assert response.data["status"] == "error"

    def test_add_labels(self, client, generate_usertoken, create_note):
        """
        Test adding labels to a note.
        """
        # Create a label
        label = Label.objects.create(name="Urgent", user=CustomUser.objects.get(email="testuser@gmail.com"))
        
        url = reverse('notes-add-labels')
        data = {
            "note_id": create_note,
            "label_ids": [label.id]
        }
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert response.data["message"] == "Labels added successfully"
    
    def test_remove_labels(self, client, generate_usertoken, create_note):
        """
        Test removing labels from a note.
        """
        # Create a label and add it to the note
        label = Label.objects.create(name="Urgent", user=CustomUser.objects.get(email="testuser@gmail.com"))
        note = Note.objects.get(id=create_note)
        note.labels.add(label)

        url = reverse('notes-remove-labels')
        data = {
            "note_id": create_note,
            "label_ids": [label.id]
        }
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert response.data["message"] == "Labels removed successfully"