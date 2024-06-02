"""
Tests for the ingrediants APIs
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingrediant, Recipe
from recipe.serializers import IngrediantSerializer


INGREDIANTS_URL = reverse('recipe:ingrediant-list')


def create_user(email='test@example.com', password='pass1234@'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(ing_id):
    return reverse('recipe:ingrediant-detail', args=[ing_id])


class PublicIngrediantsAPITests(TestCase):
    """Test unauth. API endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retriving ingrediants."""

        res = self.client.get(INGREDIANTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngrediantsAPITests(TestCase):
    """Test auth. api requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingrediants(self):
        """Test retrieving list of ingrediants."""

        Ingrediant.objects.create(user=self.user, name='ING 1')
        Ingrediant.objects.create(user=self.user, name='ING 2')

        res = self.client.get(INGREDIANTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingrediants = Ingrediant.objects.filter(
            user=self.user).order_by('-name')
        serializer = IngrediantSerializer(ingrediants, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_ingrediants_limited_to_user(self):
        """Test list of ingrediants limited to user."""
        user2 = create_user(email='test2@example.com')

        Ingrediant.objects.create(user=user2, name='INGO')
        ing = Ingrediant.objects.create(user=self.user, name='Papper')

        res = self.client.get(INGREDIANTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ing.name)
        self.assertEqual(res.data[0]['id'], ing.id)

    def test_update_ingrediant(self):
        """Test updating ingrediant."""
        ingrediant = Ingrediant.objects.create(user=self.user, name='Cilantro')
        payload = {'name': 'Coriander'}

        url = detail_url(ingrediant.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingrediant.refresh_from_db()
        self.assertEqual(ingrediant.name, payload['name'])

    def test_delete_ingrediant(self):
        """Test Deleting ingrediants."""
        ingrediant = Ingrediant.objects.create(user=self.user, name='Cilantro')
        name = ingrediant.name
        url = detail_url(ingrediant.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        isExists = Ingrediant.objects.filter(
            user=self.user, name=name).exists()
        self.assertFalse(isExists)

    def test_filter_ingrediants_assigned_to_recipe(self):
        """Test listing ingrediants by those assigned to recipes."""
        ing1 = Ingrediant.objects.create(user=self.user, name='Apples')
        ing2 = Ingrediant.objects.create(user=self.user, name='Turkey')

        recipe = Recipe.objects.create(user=self.user, **{
            'title': 'Apple Crumble',
            'time_minutes': 50,
            'price': Decimal('125.50'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe1.jpg',
        })
        recipe.ingrediants.add(ing1)

        res = self.client.get(INGREDIANTS_URL, {'assigned_only': 1})

        s1 = IngrediantSerializer(ing1)
        s2 = IngrediantSerializer(ing2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingrediants_unique(self):
        """Test filtered ingrediants returns unique values."""
        ing = Ingrediant.objects.create(user=self.user, name='Eggs')
        Ingrediant.objects.create(user=self.user, name='Lentiles')

        rec1 = Recipe.objects.create(user=self.user, **{
            'title': 'Egg Bendict',
            'time_minutes': 50,
            'price': Decimal('125.50'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe1.jpg',
        })

        rec2 = Recipe.objects.create(user=self.user, **{
            'title': 'Herb Eggs',
            'time_minutes': 50,
            'price': Decimal('125.50'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe1.jpg',
        })

        rec1.ingrediants.add(ing)
        rec2.ingrediants.add(ing)

        res = self.client.get(INGREDIANTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
