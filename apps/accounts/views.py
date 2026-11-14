from rest_framework import generics, status, viewsets, filters, serializers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import User, Profile, UserRole
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    ProfileSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .permissions import IsAdminUser
from apps.common.utils import api_response


def set_refresh_cookie(response, refresh_token):
    """
    Sets the JWT refresh token as an HttpOnly, secure cookie to protect against XSS.
    """
    cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH', 'refresh_token')
    max_age = getattr(settings, 'AUTH_COOKIE_MAX_AGE', 7 * 24 * 60 * 60)
    secure = getattr(settings, 'AUTH_COOKIE_SECURE', not settings.DEBUG)
    httponly = getattr(settings, 'AUTH_COOKIE_HTTP_ONLY', True)
    path = getattr(settings, 'AUTH_COOKIE_PATH', '/')
    samesite = getattr(settings, 'AUTH_COOKIE_SAMESITE', 'Lax')

    response.set_cookie(
        key=cookie_name,
        value=str(refresh_token),
        max_age=max_age,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
        path=path,
    )


def delete_refresh_cookie(response):
    """
    Clears the JWT refresh token cookie upon logout.
    """
    cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH', 'refresh_token')
    path = getattr(settings, 'AUTH_COOKIE_PATH', '/')
    samesite = getattr(settings, 'AUTH_COOKIE_SAMESITE', 'Lax')
    response.delete_cookie(
        key=cookie_name,
        path=path,
        samesite=samesite,
    )


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get('refresh')
        access_token = serializer.validated_data.get('access')
        user_data = serializer.validated_data.get('user')

        # Return only access token and user payload in JSON body
        response = Response(
            {
                'access': access_token,
                'user': user_data,
            },
            status=status.HTTP_200_OK
        )
        if refresh_token:
            set_refresh_cookie(response, refresh_token)
        return response


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH', 'refresh_token')
        refresh_token = (
            request.data.get('refresh')
            if hasattr(request, 'data') and request.data.get('refresh')
            else request.COOKIES.get(cookie_name)
        )

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not provided in request body or cookie.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['refresh'] = refresh_token

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        new_refresh = serializer.validated_data.get('refresh')
        new_access = serializer.validated_data.get('access')

        response_data = {'access': new_access}
        # If client explicitly provided refresh in body, also echo in body for backward compatibility
        if request.data.get('refresh') and new_refresh:
            response_data['refresh'] = new_refresh

        response = Response(response_data, status=status.HTTP_200_OK)
        if new_refresh:
            set_refresh_cookie(response, new_refresh)
        return response


class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens immediately upon registration
        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['first_name'] = user.first_name
        refresh['last_name'] = user.last_name

        # Return only access token and user payload in JSON response body
        data = {
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
        }
        response = api_response(
            success=True,
            data=data,
            message="User registered successfully",
            status_code=status.HTTP_201_CREATED
        )
        set_refresh_cookie(response, str(refresh))
        return response

class CurrentUserView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return api_response(
            success=True,
            data=serializer.data,
            message="User profile retrieved"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(
            success=True,
            data=UserSerializer(instance).data,
            message="Profile updated successfully"
        )

class LogoutView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer

    def post(self, request):
        cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH', 'refresh_token')
        refresh_token = (
            request.data.get('refresh')
            if hasattr(request, 'data') and request.data.get('refresh')
            else request.COOKIES.get(cookie_name)
        )
        try:
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            response = api_response(
                success=True,
                data={},
                message="Successfully logged out"
            )
            delete_refresh_cookie(response)
            return response
        except TokenError:
            response = api_response(
                success=False,
                message="Invalid or expired token",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            delete_refresh_cookie(response)
            return response

class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgotPasswordSerializer
    throttle_scope = 'auth'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            return api_response(
                success=True,
                data={'uid': uid, 'token': token, 'reset_link': f"/reset-password?uid={uid}&token={token}"},
                message="Password reset instructions generated"
            )
        except User.DoesNotExist:
            return api_response(
                success=True,
                data={},
                message="If the email exists, a reset link will be sent"
            )

class ResetPasswordView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer
    throttle_scope = 'auth'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return api_response(
                success=True,
                message="Password has been reset successfully"
            )
        return api_response(
            success=False,
            message="Invalid or expired reset token",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    queryset = User.objects.all().select_related('profile').order_by('-created_at')
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('role', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering_fields = ('created_at', 'email', 'role')
