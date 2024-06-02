"""
Test for the recipe API endpoints.
"""

import tempfile
import os
from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingrediant

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a recipe detail url."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload url."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    """Create and Return a recipe."""
    defaults = {
        'title': 'Sample RECIPE TITLE',
        'time_minutes': 50,
        'price': Decimal('125.50'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe1.jpg',
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


def create_user(**kargs):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**kargs)


class PublicRecipeAPITest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving the recipes."""
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of retrieving recipes is limited to authenticated user."""

        user_2 = create_user(
            email='test123@example.com', password='pass123331'
        )

        create_recipe(user_2)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        user_recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(user_recipes, many=True)

        self.assertEqual(serializer.data, res.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe_id=recipe.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test Creating a recipe api."""

        payload = {
            'title': 'sample recipe',
            'time_minutes': 20,
            'price': Decimal('5.90')
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update to a recipe."""

        original_link = 'example.com'

        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link=original_link
        )

        payload = {'title': 'New Title'}

        res = self.client.patch(detail_url(recipe.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update to a recipe."""

        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link='example.com',
            description='description for recipe.',

        )

        payload = {
            'title': 'new title',
            'link': 'new-link.com',
            'description': 'new description for recipe.',
            'time_minutes': 60,
            'price': Decimal('120.50')
        }

        res = self.client.put(detail_url(recipe.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_error(self):
        """Test error if changing a recipe user."""

        new_user = create_user(email='email21@example.com', password='apsnb21')
        recipe = create_recipe(self.user)

        payload = {'user': new_user.id}

        url = detail_url(recipe.id)

        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_deleting_recipe(self):
        """Test deleting a recipe."""

        recipe = create_recipe(self.user)

        res = self.client.delete(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_error_other_user_delete_recipe(self):
        """Test trying to delete other user recipe."""
        new_user = create_user(email='email21@example.com', password='apsnb21')
        recipe = create_recipe(new_user)

        res = self.client.delete(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test Creating a recipe with new tags."""
        payload = {
            'title': 'Egg',
            'time_minutes': 12,
            'price': Decimal(2.15),
            'tags': [
                {'name': 'Hot'},
                {'name': 'BreakFast'}
            ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)

        for tag in payload['tags']:
            exists = Tag.objects.filter(
                user=self.user, name=tag['name']).exists()
            self.assertTrue(exists)

    def test_creating_recipe_with_existing_tag(self):
        """Test Create a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')

        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal(4.15),
            'tags': [
                {'name': 'Indian'},
                {'name': 'Dinner'}
            ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)
        self.assertIn(tag_indian, recipes[0].tags.all())

        for tag in payload['tags']:
            exists = Tag.objects.filter(
                user=self.user, name=tag['name']).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test create tag when updating recipe."""
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(
            user=self.user, name=payload['tags'][0]['name'])

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(breakfast)

        lunch = Tag.objects.create(user=self.user, name='Lunch')

        payload = {'tags': [{'name': 'Lunch'}]}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(lunch, recipe.tags.all())
        self.assertNotIn(breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing recipe tags."""
        tag = Tag.objects.create(user=self.user, name="Desert")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingrediants(self):
        """Test Creating a recipe with new ingrediants."""
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal(4.15),
            'ingrediants': [
                {'name': 'Salt'},
                {'name': 'Sugar'}
            ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingrediants.count(), 2)

        for ing in payload['ingrediants']:
            self.assertTrue(
                recipe.ingrediants.filter(
                    user=self.user,
                    name=ing['name']
                ).exists()
            )

    def test_create_recipe_with_existing_ingrediant(self):
        """Test creating a recipe with existing ingrediant."""

        ingrediant = Ingrediant.objects.create(user=self.user, name='INGO')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal(4.15),
            'ingrediants': [
                {'name': 'INGO'},
                {'name': 'Salt'},
            ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingrediants.count(), 2)
        self.assertIn(ingrediant, recipe.ingrediants.all())

        for ing in payload['ingrediants']:
            self.assertTrue(
                recipe.ingrediants.filter(
                    user=self.user,
                    name=ing['name']
                ).exists()
            )

    def test_create_ingrediant_on_update(self):
        """Test Creating ingrediant when updating recipe."""

        recipe = create_recipe(user=self.user)
        payload = {
            'ingrediants': [{'name': 'Limes'}]
        }

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ing = Ingrediant.objects.get(user=self.user, name='Limes')
        self.assertIn(new_ing, recipe.ingrediants.all())

    def test_update_recipe_assign_ingrediant(self):
        """Test assigning an existing ingrediant when updating a recipe."""
        ing1 = Ingrediant.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingrediants.add(ing1)

        ing2 = Ingrediant.objects.create(user=self.user, name='Chili')

        payload = {'ingrediants': [{'name': 'Chili'}]}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ing2, recipe.ingrediants.all())
        self.assertNotIn(ing1, recipe.ingrediants.all())

    def test_clear_recipe_ingrediant(self):
        """Test clearing recipe ingrediant."""
        ing = Ingrediant.objects.create(user=self.user, name="INGO")
        recipe = create_recipe(user=self.user)
        recipe.ingrediants.add(ing)

        payload = {'ingrediants': []}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingrediants.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags."""
        r1 = create_recipe(user=self.user, title='Thai Vegetable Curry')
        r2 = create_recipe(user=self.user, title='Aubergine with Tahini')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='Fish')

        params = {'tags': f"{tag1.id},{tag2.id}"}

        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingrediants(self):
        """Test filtering recipes by ingrediants."""
        r1 = create_recipe(user=self.user, title='Thai Vegetable Curry')
        r2 = create_recipe(user=self.user, title='Aubergine with Tahini')
        ing1 = Ingrediant.objects.create(user=self.user, name='Curry')
        ing2 = Ingrediant.objects.create(user=self.user, name='Rice')
        r1.ingrediants.add(ing1)
        r2.ingrediants.add(ing2)
        r3 = create_recipe(user=self.user, title='Red Lantil Daal')

        params = {'ingrediants': f"{ing1.id},{ing2.id}"}

        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Test for image upload api."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'pass1234@'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as img_file:
            img = Image.new('RGB', (10, 10))
            img.save(img_file, format='JPEG')
            img_file.seek(0)
            payload = {
                'image': img_file
            }

            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading image invalid image."""
        url = image_upload_url(self.recipe.id)

        payload = {'image': 'not-an-image'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
