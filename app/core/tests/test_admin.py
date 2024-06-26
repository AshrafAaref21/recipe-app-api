"""
Tests for the django admin modifications
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdmineSiteTests(TestCase):
    """Tests for django admin."""

    def setUp(self):
        """Create User and Client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            'admin@example.com', 'adminpass132'
        )
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'pass123',
            name='User'
        )

    def test_users_list(self):
        """Test that users are listed on page."""
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.name)

    def test_change_user_page(self):
        """Test the edit user page."""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(str(res.status_code)[0], "2")

    def test_create_user_page(self):
        """Test the create user page."""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(str(res.status_code)[0], "2")
