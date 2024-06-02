"""
URL Mappings for recipe app.
"""


from django.urls import (
    path,
    include
)

from rest_framework.routers import DefaultRouter

from .views import *


app_name = 'recipe'

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingrediants', IngrediantsViewSet)

urlpatterns = [
    path('', include(router.urls))
]
