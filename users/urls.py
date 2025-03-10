from django.urls import path
from .views import (
    RegisterView,
    PasswordResetView,
    PasswordUpdateView,
    RoleAssignmentView,
    RoleListView,
    UserListView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    GetCSRFToken,
    CurrentUserView,
    UserUpdateView,
    UserDetailView,
)

urlpatterns = [
    # Authentication Endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Add CSRF endpoint
    path('csrf/', GetCSRFToken.as_view(), name='csrf_token'),

    # Password Management
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-update/<str:uidb64>/<str:token>/', PasswordUpdateView.as_view(), name='password-update'),

    # Role Management
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('assign-role/<int:pk>/', RoleAssignmentView.as_view(), name='assign-role'),

    # User Management
    path('', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
]
