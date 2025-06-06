from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import UserSerializer, UserCreateSerializer, PasswordResetSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from rest_framework.response import Response
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import RefreshToken
from kes_flight_map.settings import base as settings
from kes_flight_map.tasks import send_password_reset_email
import logging
from .throttles import UsernameLoginThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
    

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    """
    View to obtain and set the CSRF token in a cookie.
    """
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        csrf_token = get_token(request)
        response = Response(
            {'csrfToken': csrf_token},  # Send token in response body
            status=status.HTTP_200_OK
        )
        response.set_cookie(
            'csrftoken',
            csrf_token,
            max_age=60 * 60 * 24 * 7,
            secure=False,  # For development
            samesite='Lax',
            httponly=False
        )
        return response

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view to obtain JWT token pairs (access and refresh tokens).
    This view also includes CSRF protection. 
    Rate limiting is handled by DRF's built-in throttling (see UsernameLoginThrottle).
    """
    serializer_class = CustomTokenObtainPairSerializer
    authentication_classes = []  # Disable default session/auth classes
    permission_classes = [AllowAny]
    throttle_classes = [UsernameLoginThrottle]  # or [AnonRateThrottle, UsernameLoginThrottle] if desired

    def post(self, request, *args, **kwargs):
        # Check CSRF token presence
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return Response(
                {'detail': 'CSRF token missing or incorrect.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Extract username (or email) from request data if you need it for logging
        username = request.data.get('username')  # or 'email' if your payload uses "email"

        # Validate credentials with your serializer
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.warning(f"Token error for {username}: {str(e)}")
            raise InvalidToken(e.args[0])

        # On success, retrieve tokens
        access = serializer.validated_data.get('access')
        refresh = serializer.validated_data.get('refresh')

        # Create a response with an HTTP-only cookie for the refresh token
        response = Response({'access': access}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7  # 7 days
        )

        # Return a fresh CSRF token in the response
        response.data['csrf_token'] = get_token(request)
        return response

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view to refresh JWT tokens using the refresh token stored in cookies.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token missing'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        request.data['refresh'] = refresh_token
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        access = serializer.validated_data.get('access')
        new_refresh = serializer.validated_data.get('refresh', None)

        response = Response({'access': access}, status=status.HTTP_200_OK)

        if new_refresh:
            response.set_cookie(
                key='refresh_token',
                value=new_refresh,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=60 * 60 * 24 * 7,
            )

        return response


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    """
    Handles user logout by blacklisting refresh token and clearing cookies
    """
    def post(self, request):
        # Extract refresh token from cookies
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Blacklist the refresh token if present
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Successfully blacklisted token for user {token.payload.get('user_id')}")
            except Exception as e:
                logger.error(f"Error blacklisting token: {str(e)}", 
                           extra={'user_id': token.payload.get('user_id', 'unknown')})
        
        # Build response with cookie clearing
        response = Response(
            {'detail': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )
        
        # Secure cookie deletion parameters (match cookie settings)
        response.delete_cookie(
            'refresh_token',
            path='/',
            domain=None,
            samesite='Lax',
            secure=False  # Set True in production
        )
        
        # Clear CSRF token cookie if needed
        response.delete_cookie(
            'csrftoken',
            path='/',
            domain=None,
            samesite='Lax',
            secure=False  # Set True in production
        )
        
        return response


# @method_decorator(csrf_protect, name='dispatch')
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
        

class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['email']
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Queue email task
            send_password_reset_email.delay(
                email=user.email,
                reset_link=reset_link
            )
            
            return Response({'message': 'Password reset email queued'}, status=200)


class PasswordUpdateView(APIView):
    @method_decorator(ratelimit(key='post:password', rate='3/h', method='POST'))
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
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(password, user)
                user.set_password(password)
                user.save()
                return Response({'message': 'Password updated successfully!'}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Password not provided'}, status=status.HTTP_400_BAD_REQUEST)


class RoleAssignmentView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        role = request.data.get('role')
        if role not in dict(User.ROLE_CHOICES).keys():
            raise ValidationError({"error": f"Invalid role: {role}. Allowed roles are: {list(dict(User.ROLE_CHOICES).keys())}"})
        return super().partial_update(request, *args, **kwargs)


class RoleListView(APIView):
    def get(self, request):
        roles = [{'key': role[0], 'label': role[1]} for role in User.ROLE_CHOICES]
        return Response(roles)


class UserDetailView(RetrieveAPIView):
    """
    Retrieve a user's details by their ID. This view is restricted to admin users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserUpdateView(UpdateAPIView):
    """
    Allows an admin to update any user's information by specifying their ID.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]