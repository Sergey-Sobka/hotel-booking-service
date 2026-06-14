from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("users:register")
        self.profile_url = reverse("users:me")
        self.token_url = reverse("users:token_obtain_pair")
        self.token_refresh_url = reverse("users:token_refresh")

        self.user_data = {
            "email": "testuser@example.com",
            "password": "securepassword123",
        }

    def test_user_registration_successful(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], self.user_data["email"])
        self.assertNotIn("password", response.data)

    def test_user_login_and_jwt_obtain(self):
        """Test getting JWT tokens after successful registration."""
        self.client.post(self.register_url, self.user_data)

        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"],
        }
        response = self.client.post(self.token_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_access_me_endpoint_with_custom_authorize_header(self):
        """Test the /me/ endpoint using the custom 'Authorize' header."""
        self.client.post(self.register_url, self.user_data)
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"],
        }
        token_response = self.client.post(self.token_url, login_data)
        access_token = token_response.data["access"]

        response_unauthorized = self.client.get(self.profile_url)
        self.assertEqual(
            response_unauthorized.status_code, status.HTTP_401_UNAUTHORIZED
        )

        self.client.credentials(HTTP_AUTHORIZE=f"Authorize {access_token}")
        response_authorized = self.client.get(self.profile_url)

        self.assertEqual(response_authorized.status_code, status.HTTP_200_OK)
        self.assertEqual(response_authorized.data["email"], self.user_data["email"])

    def test_user_profile_update(self):
        """Test updating user profile details via the /me/ endpoint."""
        self.client.post(self.register_url, self.user_data)
        token_response = self.client.post(
            self.token_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )
        access_token = token_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZE=f"Authorize {access_token}")

        update_data = {"first_name": "John", "last_name": "Doe"}
        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "John")
        self.assertEqual(response.data["last_name"], "Doe")
