# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import *
import logging
from django.shortcuts import get_object_or_404
from .serializers import *
from rest_framework import generics
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    Handles user registration with name, email, and password.
    Returns JWT access and refresh tokens upon successful registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")

        # --- Input validation ---
        if not all([name, email, password]):
            return Response(
                {"error": "Name, email, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Password validation ---
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # --- Create user and profile ---
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
            )

            profile = Profile.objects.create(user=user)
            send_welcome_email(user)

            # --- Generate JWT tokens ---
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            logger.info(f"New user registered: {email}")

            return Response(
                {
                    "message": "User registered successfully.",
                    "access_token": str(access),
                    "refresh_token": str(refresh),
                    "user": {
                        "email": user.email,
                        "name": user.first_name,
                        "xp": profile.xp,
                        "coins": profile.coins,
                        "level": profile.level,
                        "avatar": profile.avatar,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("Registration failed")
            return Response(
                {"error": "An unexpected error occurred during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class EmailLoginView(APIView):
    """
    Handles login with email and password.
    Returns JWT access and refresh tokens upon successful authentication.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # --- Input validation ---
        if not all([email, password]):
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Check if user exists but has no usable password (Google login) ---
        user_obj = User.objects.filter(email=email).first()
        if user_obj and not user_obj.has_usable_password():
            return Response(
                {"error": "This account was created using Google. Please log in with Google Sign-In."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Authenticate user normally ---
        user = authenticate(username=email, password=password)
        if user is None:
            logger.warning(f"Failed login attempt for {email}")
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # --- Generate JWT tokens ---
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            profile, _ = Profile.objects.get_or_create(user=user)

            logger.info(f"User logged in: {email}")

            return Response(
                {
                    "message": "Login successful.",
                    "access_token": str(access),
                    "refresh_token": str(refresh),
                    "user": {
                        "email": user.email,
                        "name": user.first_name,
                        "xp": profile.xp,
                        "coins": profile.coins,
                        "level": profile.level,
                        "avatar": profile.avatar,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Login failed")
            return Response(
                {"error": "An unexpected error occurred during login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def send_welcome_email(user):
    """Send HTML welcome email after signup."""
    subject = "🎉 Welcome to CodeLearn!"
    html_message = render_to_string("emails/welcome_email.html", {"user": user})
    email = EmailMessage(subject, html_message, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.content_subtype = "html"
    email.send(fail_silently=True)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "No token provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.info("Verifying Google token...")

            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                "490520721899-pgvbcqq3ol2rbl03gq09n6ts1i3273nl.apps.googleusercontent.com"
            )

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError("Wrong issuer")

            email = idinfo.get("email")
            name = idinfo.get("name") or ""
            avatar_url = idinfo.get("picture")

            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": name}
            )

            # Create or update profile
            profile, profile_created = Profile.objects.get_or_create(user=user)
            if created or profile_created:
                profile.avatar = avatar_url
                profile.save()
                logger.info(f"Created new profile for {email}")

            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            return Response({
                "access_token": str(access),
                "refresh_token": str(refresh),
                "email": user.email,
                "name": user.first_name,
                "xp": profile.xp,
                "coins": profile.coins,
                "level": profile.level,
                "avatar": profile.avatar,
            }, status=200)

        except ValueError:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.exception("Google login failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        data = {
            "id": user.id,
            "email": user.email,
            "name": user.first_name,
            "xp": profile.xp,
            "level": profile.level,
            "coins": profile.coins,
            "avatar": profile.avatar,
        }
        return Response(data, status=200)
    
class LogoutView(APIView):
    """
    Log out user by blacklisting their refresh token (if blacklist app is enabled).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
 

            if not refresh_token:
               
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
          
            # Try to blacklist only if blacklist app is enabled
            try:
                token.blacklist()
                message = "Successfully logged out and token blacklisted."
               
            except AttributeError:
                # Blacklist not configured
                message = "Logout successful (blacklist not enabled)."

            return Response({"message": message}, status=status.HTTP_200_OK)

        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TokenRefreshView(APIView):
    """
    Takes a refresh token and returns a new access token (and optionally a new refresh token).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            logger.error("No refresh token provided in request.")
            return Response({"error": "No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.info("Attempting to refresh access token...")

            # Validate and decode the refresh token
            refresh = RefreshToken(refresh_token)
            
            # Create new access token
            new_access_token = str(refresh.access_token)

            # Optional: rotate refresh token (recommended for security)
            refresh.blacklist()  # If using blacklist app
            new_refresh_token = str(refresh)

            logger.info("Access token refreshed successfully.")

            return Response({
                "access_token": new_access_token,
                "refresh_token": new_refresh_token  # optional if you want rotation
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            logger.error(f"Invalid refresh token: {str(e)}")
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.exception("Unexpected error during token refresh")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not all([old_password, new_password]):
            return Response({"error": "Old and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


# -----------------------------
# Forgot Password (Request Reset)
# -----------------------------
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        form = PasswordResetForm(data={"email": email})
        if form.is_valid():
            # Send reset email
            form.save(
                subject_template_name="emails/password_reset_subject.txt",
                email_template_name="emails/password_reset_email.html",
                use_https=request.is_secure(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                request=request,
                html_email_template_name="emails/password_reset_email.html"
            )
            return Response({"message": "Password reset email sent if the email exists."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# Reset Password (Confirm via Token)
# -----------------------------
class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"error": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)