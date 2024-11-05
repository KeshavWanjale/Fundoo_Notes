import pytest
from rest_framework.reverse import reverse
from rest_framework import status

@pytest.fixture
def create_user(client):
    data = {
        "username": "TestUser",
        "email": "testuser@gmail.com",
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

@pytest.mark.django_db
class TestLabelSuccess:

    def test_create_labels(self, client, generate_usertoken):

        label_data = {
            "name": "the book",
            "color": "black"
        }
        
        url = reverse('label-list-create')  
        response = client.post(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', data=label_data, content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED
        return response.data['data']['id']
    
    def test_list_labels(self, client, generate_usertoken):

        url = reverse('label-list-create')
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == "success"
        assert "data" in response.data
        assert isinstance(response.data['data'], list)

    def test_update_label(self, client, generate_usertoken):

        label_id = self.test_create_labels(client, generate_usertoken)
        update_data = {
            "name": "updated book",
            "color": "blue"
        }

        url = reverse('label-update-delete', args=[label_id])
        response = client.put(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', data=update_data, content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == "success"
        assert response.data['message'] == "Label updated successfully."
        assert response.data['data']['name'] == "updated book"
        assert response.data['data']['color'] == "blue"

    def test_delete_label(self, client, generate_usertoken):
        # First, create a label to delete
        label_id = self.test_create_labels(client, generate_usertoken)
        
        url = reverse('label-update-delete', args=[label_id])
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == "success"
        assert response.data['message'] == "Label deleted successfully."

    def test_create_label_validation_error(self, client, generate_usertoken):
        # Missing 'name' field in data to trigger validation error
        label_data = {
            "color": "black"
        }
        url = reverse('label-list-create')
        response = client.post(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', data=label_data, content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == "error"
        assert "errors" in response.data

    def test_update_label_validation_error(self, client, generate_usertoken):

        label_id = self.test_create_labels(client, generate_usertoken)
        update_data = {
            "color": "blue"
        }
        url = reverse('label-update-delete', args=[label_id])
        response = client.put(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', data=update_data, content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_nonexistent_label(self, client, generate_usertoken):
        # Attempt to update a non-existing label
        label_data = {
            "name": "non-existent label",
            "color": "red"
        }
        url = reverse('label-update-delete', kwargs={"pk": 999})  
        response = client.put(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}', data=label_data, content_type='application/json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_label(self, client, generate_usertoken):
        # Attempt to delete a non-existing label
        url = reverse('label-update-delete', kwargs={"pk": 999})
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {generate_usertoken}')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_invalid_token(self, client, generate_usertoken):
        # Attempt to delete a non-existing label
        invalid_token = "invalid.user.token"
        url = reverse('label-update-delete', kwargs={"pk": 999})
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {invalid_token}')
        assert response.status_code == 401