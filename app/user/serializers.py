"""
Serializers for the User API Views.
"""

from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.utils.translation import gettext as _

from rest_framework import serializers
from datetime import datetime


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ['id', 'is_staff', 'email', 'password', 'name']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            },
            'is_staff': {
                'read_only': True,
            }
        }

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and Return a user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data=validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validate and Authenticate user."""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = _("Unable to authenticate with provided credintials.")
            raise serializers.ValidationError(msg, code='authorization')

        user.last_login = datetime.now()
        user.save()
        attrs['user'] = user

        return attrs


class AdminDashboardSerializer(UserSerializer):
    """Serializer for the users for Admin Dashboard."""
    class Meta:
        model = get_user_model()
        fields = "__all__"
