"""
Tests for the user api.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**kargs):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**kargs)


class PublicUserApiTest(TestCase):
    """Test Public API endpoints."""

    payload = {
        'email': 'email@example.com',
        'password': 'email123',
        'name': 'user name',
    }

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test Create User."""

        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.payload['email'])
        self.assertTrue(user.check_password(self.payload['password']))

        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test Error Returned if user with email exists."""

        create_user(**self.payload)
        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test Error if password is too short."""
        self.payload['password'] = '12'

        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=self.payload['email']
        ).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test Generates token for valid credentials."""

        user_details = {
            'name': 'test name',
            'email': 'testname@example.com',
            'password': 'testpassword123',
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credential(self):
        """Test Error if credential not valid."""
        create_user(**self.payload)

        new_payload = {
            'email': self.payload['email'], 'password': 'sazxcadg123gz'}

        res = self.client.post(TOKEN_URL, new_payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test Posting blank password returns error."""
        payload = {
            'email': 'email@example.com',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrive_user_unautherized(self):
        """Test authentication required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Tests APIs require Authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='pass123445',
            name='test'
        )

        self.client = APIClient()

        self.client.force_authenticate(user=self.user)

    def test_retrive_profile_success(self):
        """Test Retriving profile for authenticated user."""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {'name': self.user.name, 'email': self.user.email}
        )

    def test_post_me_not_allowed(self):
        """Test Post is not allowed for me endpoint."""

        res = self.client.post(ME_URL, {'email': 'asd@example.com'})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated users."""

        payload = {'name': 'updated user name', 'password': 'newpass135'}

        res = self.client.patch(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Refresh the user and return it from the database
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
