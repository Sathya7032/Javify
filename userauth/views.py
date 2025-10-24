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
        
class TopicListView(APIView):
    """List topics for a specific level."""
    permission_classes = [AllowAny]

    def get(self, request, level_number):
        level = get_object_or_404(Level, number=level_number)
        topics = level.topics.order_by('order').values('id', 'title', 'explanation', 'video_url', 'order')
        return Response({"level": level.title, "topics": list(topics)})


class SubmitAnswersView(APIView):
    """Submit quiz answers and award XP + coins only once per topic."""
    permission_classes = [IsAuthenticated]  # Only logged-in users can submit

    def post(self, request, topic_id):
        user = request.user
        profile = user.profile
        topic = get_object_or_404(Topic, id=topic_id)
        answers = request.data.get("answers", {})  # {"question_id": "answer"}

        questions = topic.questions.all()
        correct_count = 0

        for q in questions:
            user_answer = str(answers.get(str(q.id), "")).strip().lower()
            correct = str(q.correct_answer).strip().lower()
            if user_answer == correct:
                correct_count += 1

        progress, created = UserProgress.objects.get_or_create(user=user, topic=topic)
        progress.correct_answers = correct_count
        progress.total_questions = questions.count()

        if correct_count == questions.count():
            if not progress.completed:
                # First-time completion: award XP & coins
                progress.mark_completed()
                profile.add_xp(10)
                profile.coins += 5

                # Level up after every 5 completed topics
                total_completed = UserProgress.objects.filter(user=user, completed=True).count()
                if total_completed % 5 == 0:
                    profile.level += 1

                profile.save()

                return Response({
                    "message": "✅ All answers correct! Topic completed. XP & coins awarded.",
                    "xp": profile.xp,
                    "coins": profile.coins,
                    "level": profile.level
                }, status=status.HTTP_200_OK)
            else:
                # Already completed before
                return Response({
                    "message": "✅ All answers correct! Topic was already completed. XP & coins already awarded."
                }, status=status.HTTP_200_OK)

        else:
            progress.save()
            return Response({
                "message": f"❌ You got {correct_count}/{questions.count()} correct. Try again!"
            }, status=status.HTTP_200_OK)

        
# -----------------------------
# 1️⃣ List all levels
# -----------------------------
class LevelListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        levels = Level.objects.all().order_by('number')
        serializer = LevelSerializer(levels, many=True)
        return Response(serializer.data)


# -----------------------------
# 2️⃣ List all topics under a level
# -----------------------------
class TopicListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, level_id):
        level = get_object_or_404(Level, id=level_id)
        topics = level.topics.order_by('order')
        serializer = TopicSerializer(topics, many=True)
        return Response({
            "level_id": level.id,
            "level_number": level.number,
            "level_title": level.title,
            "topics": serializer.data
        })


# -----------------------------
# 3️⃣ List all questions under a topic
# -----------------------------
class QuestionListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id)
        questions = topic.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response({
            "topic_id": topic.id,
            "topic_title": topic.title,
            "questions": serializer.data
        })
    
class CodingTopicListView(APIView):
    """
    Get all coding topics
    """
    def get(self, request):
        topics = CodingTopic.objects.all().order_by('name')  # Order alphabetically
        serializer = CodingTopicSerializer(topics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

# List problems under a specific topic
class CodingProblemListAPIView(generics.ListAPIView):
    serializer_class = CodingProblemListSerializer

    def get_queryset(self):
        topic_id = self.kwargs['topic_id']
        return CodingProblem.objects.filter(topic__id=topic_id).order_by('sno')

# Detailed view of a single problem
class CodingProblemDetailAPIView(generics.RetrieveAPIView):
    queryset = CodingProblem.objects.all()
    serializer_class = CodingProblemDetailSerializer

class UserProgressView(APIView):
    """
    Get all topics' progress for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_qs = UserProgress.objects.filter(user=user).select_related("topic", "topic__level")
        
        data = [
            {
                "level_id": p.topic.level.id,
                "level_number": p.topic.level.number,
                "level_title": p.topic.level.title,
                "topic_id": p.topic.id,
                "topic_title": p.topic.title,
                "completed": p.completed,
                "correct_answers": p.correct_answers,
                "total_questions": p.total_questions,
                "date_completed": p.date_completed,
            }
            for p in progress_qs
        ]

        return Response({"user": user.username, "progress": data}, status=status.HTTP_200_OK)
