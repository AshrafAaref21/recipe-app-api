"""
URL Mappings for the User API.
"""

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'user'

router = DefaultRouter()
router.register('users', views.AdminUserView)


urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateAuthTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),

    path('admin/', include(router.urls)),
    path('resetpass/', views.send_email, name='reset-pass')
]
