from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import UserSerializer, UserCreateSerializer, PasswordResetSerializer

User = get_user_model()


# User Registration View
class RegisterView(APIView):
    """
    POST: Register a new user.
    """
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Password Reset Request View
class PasswordResetView(APIView):
    """
    POST: Send a password reset email to the user.
    """
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password reset email sent successfully!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Password Update View
class PasswordUpdateView(APIView):
    """
    POST: Reset the user's password using the token.
    """
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid token or user ID'}, status=status.HTTP_400_BAD_REQUEST)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get('password')
        if password:
            user.set_password(password)
            user.save()
            return Response({'message': 'Password updated successfully!'}, status=status.HTTP_200_OK)
        return Response({'error': 'Password not provided'}, status=status.HTTP_400_BAD_REQUEST)


# Role Assignment View
class RoleAssignmentView(UpdateAPIView):
    """
    PATCH: Update the role of a user (Admin-only).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def partial_update(self, request, *args, **kwargs):
        role = request.data.get('role')
        if role not in dict(User.ROLE_CHOICES).keys():
            raise ValidationError({"error": f"Invalid role: {role}. Allowed roles are: {dict(User.ROLE_CHOICES).keys()}"})
        return super().partial_update(request, *args, **kwargs)


# Fetch Predefined Roles
class RoleListView(APIView):
    """
    GET: Return a list of predefined roles.
    """
    def get(self, request):
        roles = [{'key': role[0], 'label': role[1]} for role in User.ROLE_CHOICES]
        return Response(roles)


# List All Users (Admin-only)
class UserListView(ListAPIView):
    """
    GET: List all users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
