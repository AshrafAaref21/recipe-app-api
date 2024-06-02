"""
Serializer for Recipe Model.
"""

from rest_framework import serializers

from core.models import Recipe, Tag, Ingrediant
from user.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""
    class Meta:
        model = Tag
        fields = ["id", 'name']
        read_only_fields = ['id']


class IngrediantSerializer(serializers.ModelSerializer):
    """Serializer for ingrediants."""
    class Meta:
        model = Ingrediant
        fields = ["id", 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer Class for the recipe model."""

    user = serializers.ReadOnlyField(source='core.user')
    tags = TagSerializer(many=True, required=False)
    ingrediants = IngrediantSerializer(many=True, required=False)

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, isCreated = Tag.objects.get_or_create(
                user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    def _get_or_create_ingrediants(self, ingrediants, recipe):
        """Handle getting or creating ingrediants as needed"""
        auth_user = self.context['request'].user
        for ing in ingrediants:
            ing_obj, isCreated = Ingrediant.objects.get_or_create(
                user=auth_user,
                **ing
            )
            recipe.ingrediants.add(ing_obj)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes',
                  'price', 'link', 'user', 'tags', 'ingrediants']
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        """Create a recipe."""
        tags = validated_data.pop('tags', [])
        ingrediants = validated_data.pop('ingrediants', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingrediants(ingrediants, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update Recipe."""
        tags = validated_data.pop('tags', None)
        ingrediants = validated_data.pop('ingrediants', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingrediants is not None:
            instance.ingrediants.clear()
            self._get_or_create_ingrediants(ingrediants, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def get_user(self, obj):
        items = obj.user
        serializer = UserSerializer(items, many=False)
        return serializer.data


class RecipeDetailSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images for recipes."""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {
            'image': {'required': True}
        }
