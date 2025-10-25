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
