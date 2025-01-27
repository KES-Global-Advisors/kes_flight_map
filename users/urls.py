from django.urls import path
from .views import (
    RegisterView,
    PasswordResetView,
    PasswordUpdateView,
    RoleAssignmentView,
    RoleListView,
    UserListView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Authentication Endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Password Management
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-update/<str:uidb64>/<str:token>/', PasswordUpdateView.as_view(), name='password-update'),

    # Role Management
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('assign-role/<int:pk>/', RoleAssignmentView.as_view(), name='assign-role'),

    # User Management
    path('', UserListView.as_view(), name='user-list'),
]
