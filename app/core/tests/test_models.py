"""
Tests for Models.
"""

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from decimal import Decimal
from core import models


def create_user(
    email='test@example.com',
    password='password123'
):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):
    """Test Models."""

    def test_create_user_with_email_successfull(self):
        """Test Creating a user with an email is successed."""

        email = 'test@example.com'
        password = 'pass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_normalized(self):
        """Test email is normalized for new user."""

        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, excpcted in sample_emails:
            user = get_user_model().objects.create_user(email, 'pass123')
            self.assertEqual(user.email, excpcted)

    def test_new_user_without_email_raises_error(self):
        """Test that creating user without an email raises a valueError."""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'pass123')

    def test_create_superuser(self):
        """Test creating superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'password123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test Creating a recipe."""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'password123'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='recipe name',
            time_minutes=5,
            price=Decimal('9.55'),
            description='Described recipe.'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test create tag."""

        user = create_user()

        tag = models.Tag.objects.create(user=user, name='test tag')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingrediant(self):
        """Test Create ingrediants"""
        user = create_user()
        ingrediant = models.Ingrediant.objects.create(
            user=user,
            name='Ing.1'
        )
        self.assertEqual(str(ingrediant), ingrediant.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
