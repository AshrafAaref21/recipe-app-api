"""
Views for the user API.
"""

from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view

from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, authentication, permissions, viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import uuid

from core.models import User

from .serializers import (
    UserSerializer,
    AuthTokenSerializer,
    AdminDashboardSerializer,
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer
    # http_method_names = ['get','post']


class CreateAuthTokenView(ObtainAuthToken):
    """Create a new auth token for a user."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage The authenticated user (get, patch|put)."""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return authenticated user."""
        return self.request.user


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2
    max_page_size = 2
    page_query_param = 'page'
    # page_size_query_param = 'page_size'


# Editing The Get Method in The Documentation API to recieve paramter
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(name='page', description='Page Number', type=int),
        ]
    )
)
class AdminUserView(viewsets.ModelViewSet):
    """Manage Users API for admin Dashoard."""
    serializer_class = AdminDashboardSerializer
    pagination_class = StandardResultsSetPagination
    queryset = User.objects.all().order_by('id')
    authentication_classes = [authentication.TokenAuthentication]

    permission_classes = [permissions.IsAdminUser]


@api_view(['POST'])
def send_email(request):
    data = request.data
    new_pass = str(uuid.uuid4())[:10]
    message = f"""
    Your New Password is: {new_pass}
    Use It to login.
    """
    email = data.get("email", "")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        Response("User Not found.", status=status.HTTP_400_BAD_REQUEST)

    email_from = settings.EMAIL_HOST_USER
    if data.get('email') and User.objects.filter(email=email).exists():
        try:
            user.set_password(new_pass)
            user.save()
            send_mail(message=message, subject='Reset Passsowrd',
                      from_email=email_from, recipient_list=[email])
        except BadHeaderError:
            return Response("Invalid header found.", status=status.HTTP_400_BAD_REQUEST)
        return Response('Check Your Mail', status=status.HTTP_200_OK)
    else:
        return Response("It's not a valid Email.", status=status.HTTP_400_BAD_REQUEST)
