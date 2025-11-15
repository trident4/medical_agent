"""
Test case for user CRUD operation with HIPAA compliance.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.services.user_services import UserService


class TestUserCRUD:
    """ Test suite for user CRUD operation"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient, admin_token: str):
        """Test creating a user successfully with ADMIN role."""
        user_data = {
            "username": "newdoctor",
            "email": "newdoctor@example.com",
            "full_name": "New Doctor",
            "password": "Securepassword123",
            "role": "doctor",  # Changed from UserRole.DOCTOR to string
            "is_active": True,
            "is_verified": True
        }
        response = await client.post("/api/v1/users/", json=user_data,
                                     headers={"Authorization": f"Bearer {admin_token}"})

        # Debug: Print response if assertion fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_create_duplicate_username(self, client: AsyncClient, admin_token: str):
        """Test creating a user with duplicate username."""
        user_data = {
            "username": "existinguser",
            "email": "existinguser@example.com",
            "full_name": "Existing User",
            "password": "Securepassword123",
            "role": "nurse",  # Changed from UserRole.NURSE to string
            "is_active": True,
            "is_verified": True
        }
        # First creation should succeed
        response1 = await client.post("/api/v1/users/", json=user_data,
                                      headers={"Authorization": f"Bearer {admin_token}"})
        assert response1.status_code == 201

        # Second creation with same username should fail
        response2 = await client.post("/api/v1/users/", json=user_data,
                                      headers={"Authorization": f"Bearer {admin_token}"})
        print(f"Response status: {response2.status_code}")
        print(f"Response body: {response2.json()}")
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "User with username existinguser already exists"

    @pytest.mark.asyncio
    async def test_create_duplicate_email(self, client: AsyncClient, admin_token: str):
        """ Testing creating user with duplicate email."""
        # First user details
        user_detail = {
            "username": "user1",
            "email": "user1@example.com",
            "full_name": "User One",
            "password": "Securepassword123",
            "role": "nurse",  # Changed from UserRole.ADMIN to string
        }

        # Second user details
        duplicate_email_user = {
            "username": "user2",
            "email": "user1@example.com",  # Same email as user1
            "full_name": "User Two",
            "password": "Securepassword123",
            "role": "doctor",  # Changed from UserRole.DOCTOR to string
        }

        # Create the first user
        response1 = await client.post("/api/v1/users/", json=user_detail,
                                      headers={"Authorization": f"Bearer {admin_token}"})
        assert response1.status_code == 201
        # Attempt to create the second user with duplicate email
        response2 = await client.post("/api/v1/users/", json=duplicate_email_user,
                                      headers={"Authorization": f"Bearer {admin_token}"})
        print(f"Response status: {response2.status_code}")
        print(f"Response body: {response2.json()}")
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "User with email user1@example.com already exists"

    @pytest.mark.asyncio
    async def test_create_user_unauthorized(self, client: AsyncClient):
        """Test creating a user without authorization."""
        user_data = {
            "username": "unauthuser",
            "email": "unauthuser@example.com",
            "full_name": "Unauth User",
            "password": "Securepassword123",
            "role": "nurse",  # Changed from UserRole.NURSE to string
            "is_active": True,
            "is_verified": True
        }
        response = await client.post("/api/v1/users/", json=user_data)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_create_user_success_use_doctor_token(self, client: AsyncClient, doctor_token: str):
        """Test creating a user successfully with ADMIN role."""
        user_data = {
            "username": "newdoctor",
            "email": "newdoctor@example.com",
            "full_name": "New Doctor",
            "password": "Securepassword123",
            "role": "nurse",  # Changed from UserRole.DOCTOR to string
            "is_active": True,
            "is_verified": True
        }
        response = await client.post("/api/v1/users/", json=user_data,
                                     headers={"Authorization": f"Bearer {doctor_token}"})

        # Debug: Print response if assertion fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Access denied. Required role: admin"

    @pytest.mark.asyncio
    async def test_get_users_list(self, client: AsyncClient, admin_token: str):
        """ Test retrieving the list of users"""
        response = await client.get("/api/v1/users/",
                                    headers={"Authorization": f"Bearer {admin_token}"})

        # Debug: Print response if assertion fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_update_user_success(self, client: AsyncClient, admin_token: str):
        """ Test updating user successfully"""
        # First, create a user to update
        user_data = {
            "username": "updatableuser",
            "email": "updatableuser@example.com",
            "full_name": "Updatable User",
            "password": "Securepassword123",
            "role": "nurse",  # Changed from UserRole.NURSE to string
            "is_active": True,
            "is_verified": True
        }
        create_response = await client.post("/api/v1/users/", json=user_data,
                                            headers={"Authorization": f"Bearer {admin_token}"})
        assert create_response.status_code == 201
        created_user = create_response.json()
        user_id = created_user["id"]
        # Now, update the user's full_name
        update_data = {
            "full_name": "Updated User Name"
        }
        print(f"Updating user ID: {user_id} with data: {update_data}")
        update_response = await client.put(f"/api/v1/users/{user_id}", json=update_data,
                                           headers={"Authorization": f"Bearer {admin_token}"})
        assert update_response.status_code == 200
        updated_user = update_response.json()
        assert updated_user["full_name"] == update_data["full_name"]
        assert updated_user["username"] == user_data["username"]  # unchanged
        assert updated_user["email"] == user_data["email"]  # unchanged

    @pytest.mark.asyncio
    async def test_delete_user_success(self, client: AsyncClient, admin_token: str):
        """ Test deleting user successfully"""
        # First, create a user to delete
        user_data = {
            "username": "deletableuser",
            "email": "deletableuser@example.com",
            "full_name": "Deletable User",
            "password": "Securepassword123",
            "role": "nurse",  # Changed from UserRole.NURSE to string
            "is_active": True,
            "is_verified": True
        }
        create_response = await client.post("/api/v1/users/", json=user_data,
                                            headers={"Authorization": f"Bearer {admin_token}"})
        assert create_response.status_code == 201
        created_user = create_response.json()
        user_id = created_user["id"]
        # Now, delete the user
        delete_response = await client.delete(f"/api/v1/users/{user_id}",
                                              headers={"Authorization": f"Bearer {admin_token}"})
        assert delete_response.status_code == 204
        # Verify the user is deleted
        get_response = await client.get(f"/api/v1/users/{user_id}",
                                        headers={"Authorization": f"Bearer {admin_token}"})
        assert get_response.status_code == 404
