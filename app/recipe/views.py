"""
Views for the Recipe API.
"""

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingrediant
from .serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngrediantSerializer,
    RecipeImageSerializer
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma Seperated list of IDs to filter.'
            ),
            OpenApiParameter(
                'ingrediants',
                OpenApiTypes.STR,
                description='Comma Seperated list of IDs to filter.'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage Recipe API endpoints."""

    serializer_class = RecipeDetailSerializer
    authentication_classes = [TokenAuthentication]
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def _params_to_list_of_int(self, params):
        """Convert a comma seperated strings to list of integers."""
        return [int(str_id.strip()) for str_id in params.split(',')]

    def get_queryset(self):
        """Retrieve For authenticated user."""
        tags = self.request.query_params.get('tags')
        ingrediants = self.request.query_params.get('ingrediants')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_list_of_int(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingrediants:
            ingrediants_ids = self._params_to_list_of_int(ingrediants)
            queryset = queryset.filter(ingrediants__id__in=ingrediants_ids)

        return queryset.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the Serializer class for specific request."""
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        "Method to utilize the create recipe object."
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description="Filter by items assigned to recipes."
            )
        ]
    )
)
class BaseRecipeAttrViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Base View Set for recipe attributes."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # def _get_params(self):

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage Tags in the Database."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    # def create(self, *args, **kwargs):
    #     user = self.request.user
    #     tag = Tag.objects.create(user=user, **kwargs)
    #     tag.save()

    #     return Response(TagSerializer(tag).data)


class IngrediantsViewSet(BaseRecipeAttrViewSet):
    """Manage Ingrediants in the database."""

    serializer_class = IngrediantSerializer
    queryset = Ingrediant.objects.all()
