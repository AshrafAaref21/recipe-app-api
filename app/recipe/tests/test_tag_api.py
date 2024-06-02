"""
Test Tag API endpoints.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def create_user(email='test@example.com', password='oasadfjz12'):
    """Create and Return an user."""
    return get_user_model().objects.create_user(email=email, password=password)


def create_tag(user, **params):
    return Tag.objects.create(user=user, **params)


def detail_url(tag_id):
    """Create and Return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagsAPITests(TestCase):
    """Public Tests for API endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication required."""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Private tags api test"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test retreiving a list of tags."""
        create_tag(user=self.user, name='Tag 1')
        create_tag(user=self.user, name='Tag 2')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertTrue(len(res.data) == 2)

    def test_tags_limited_to_authenticated_user(self):
        """Test Retriving only tags for authenticated user."""

        new_user = create_user(email='newemail@example.com')

        tag = create_tag(user=self.user, name='Tag #1')
        create_tag(user=new_user, name='Tag #2')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_update_tag(self):
        """Test updating tag."""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Desert'}

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test Deleting a tag."""
        tag = Tag.objects.create(user=self.user, name='Tagy')

        url = detail_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        isExist = Tag.objects.filter(user=self.user).exists()

        self.assertFalse(isExist)

    def test_filter_tags_assigned_to_recipe(self):
        """Test listing tags to thos assigned recipes."""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')

        recipe = Recipe.objects.create(user=self.user, **{
            'title': 'Apple Crumble',
            'time_minutes': 50,
            'price': Decimal('125.50'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe1.jpg',
        })
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns unique values."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')

        recipe1 = Recipe.objects.create(user=self.user, **{
            'title': 'Apple Crumble',
            'time_minutes': 50,
            'price': Decimal('125.50'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe1.jpg',
        })

        recipe2 = Recipe.objects.create(user=self.user, **{
            'title': 'Pancakes',
            'time_minutes': 50,
            'price': Decimal('125.50'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe1.jpg',
        })

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
