from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import (
    Level,
    Topic,
    UserProgress,
    UserLevelCompletion,
    CodingTopic,
    CodingProblem,
)
from .serializers import (
    LevelSerializer,
    TopicSerializer,
    QuestionSerializer,
    CodingTopicSerializer,
    CodingProblemListSerializer,
    CodingProblemDetailSerializer,
)


# -----------------------------
# 1️⃣ List all Levels
# -----------------------------
class LevelListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all available levels with their XP/coin rewards.
        """
        levels = Level.objects.all().order_by('number')
        serializer = LevelSerializer(levels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# -----------------------------
# 2️⃣ List all Topics under a Level
# -----------------------------
class TopicListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, level_id):
        """
        Get all topics that belong to a specific level.
        """
        level = get_object_or_404(Level, id=level_id)
        topics = level.topics.order_by('order')
        serializer = TopicSerializer(topics, many=True)
        return Response({
            "level_id": level.id,
            "level_number": level.number,
            "level_title": level.title,
            "required_topics": level.required_topics,
            "topics": serializer.data
        }, status=status.HTTP_200_OK)


# -----------------------------
# 3️⃣ List all Questions under a Topic
# -----------------------------
class QuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, topic_id):
        """
        Get all questions for a specific topic.
        """
        topic = get_object_or_404(Topic, id=topic_id)
        questions = topic.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response({
            "topic_id": topic.id,
            "topic_title": topic.title,
            "questions": serializer.data
        }, status=status.HTTP_200_OK)


# -----------------------------
# 4️⃣ Coding Topics and Problems
# -----------------------------
class CodingTopicListView(APIView):
    """
    Get all coding topics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        topics = CodingTopic.objects.all().order_by('name')
        serializer = CodingTopicSerializer(topics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CodingProblemListAPIView(generics.ListAPIView):
    """
    List all coding problems under a specific topic.
    """
    serializer_class = CodingProblemListSerializer

    def get_queryset(self):
        topic_id = self.kwargs['topic_id']
        return CodingProblem.objects.filter(topic__id=topic_id).order_by('sno')


class CodingProblemDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve details for a single coding problem.
    """
    queryset = CodingProblem.objects.all()
    serializer_class = CodingProblemDetailSerializer


# -----------------------------
# 5️⃣ Submit Answers + Rewards
# -----------------------------
class SubmitAnswersView(APIView):
    """
    Submit quiz answers for a topic, update progress, 
    and reward XP + coins for topics and levels.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, topic_id):
        user = request.user
        profile = user.profile  # Must exist in UserProfile model
        topic = get_object_or_404(Topic, id=topic_id)
        level = topic.level
        answers = request.data.get("answers", {})

        questions = topic.questions.all()
        correct_count = 0

        # ✅ Check answers
        for q in questions:
            user_answer = str(answers.get(str(q.id), "")).strip().lower()
            correct = str(q.correct_answer).strip().lower()
            if user_answer == correct:
                correct_count += 1

        progress, _ = UserProgress.objects.get_or_create(user=user, topic=topic)
        progress.correct_answers = correct_count
        progress.total_questions = questions.count()

        # ✅ All answers correct
        if correct_count == questions.count():
            if not progress.completed:
                progress.mark_completed()
                profile.add_xp(10)  # Topic XP
                profile.coins += 5  # Topic coins

                # ✅ Check if level completed
                if level.is_completed_by(user):
                    if not UserLevelCompletion.objects.filter(user=user, level=level).exists():
                        UserLevelCompletion.objects.create(user=user, level=level)
                        profile.add_xp(level.xp_reward)
                        profile.coins += level.coin_reward

                        # 🔓 Unlock next level
                        next_level = Level.objects.filter(number=level.number + 1).first()
                        if next_level:
                            profile.unlocked_level = next_level.number
                            profile.save()

                profile.save()

                return Response({
                    "message": f"✅ Topic '{topic.title}' completed successfully!",
                    "xp": profile.xp,
                    "coins": profile.coins,
                    "unlocked_level": getattr(profile, "unlocked_level", None),
                }, status=status.HTTP_200_OK)

            else:
                return Response({
                    "message": "✅ Topic already completed earlier."
                }, status=status.HTTP_200_OK)

        # ❌ Some answers incorrect
        else:
            progress.save()
            return Response({
                "message": f"❌ You got {correct_count}/{questions.count()} correct. Try again!"
            }, status=status.HTTP_200_OK)


# -----------------------------
# 6️⃣ User Progress (All Topics)
# -----------------------------
class UserProgressView(APIView):
    """
    Get topic-wise progress for authenticated user.
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

        return Response({
            "user": user.username,
            "progress": data
        }, status=status.HTTP_200_OK)

# -----------------------------
# 7️⃣ User Level Progress View
# -----------------------------
class UserLevelProgressView(APIView):
    """
    Get completion status for each level.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile
        levels = Level.objects.all().order_by('number')
        data = []

        # Get user's current unlocked level from profile
        current_unlocked_level = getattr(profile, "unlocked_level", 1)
        
        for level in levels:
            completed = level.is_completed_by(user)
            
            # ✅ FIX: Level is unlocked if:
            # 1. It's the first level (level 1 is always unlocked)
            # 2. User's unlocked_level is >= current level number
            # 3. OR if the previous level is completed
            unlocked = (
                level.number == 1 or 
                current_unlocked_level >= level.number or
                self.is_previous_level_completed(user, level)
            )
            
            data.append({
                "level_id": level.id,
                "level_number": level.number,
                "level_title": level.title,
                "xp_reward": level.xp_reward,
                "coin_reward": level.coin_reward,
                "required_topics": level.required_topics,
                "completed": completed,
                "unlocked": unlocked
            })

        return Response({
            "user": user.username,
            "levels": data
        }, status=status.HTTP_200_OK)

    def is_previous_level_completed(self, user, current_level):
        """Check if the previous level is completed"""
        if current_level.number == 1:
            return True  # First level has no previous level
            
        try:
            previous_level = Level.objects.get(number=current_level.number - 1)
            return previous_level.is_completed_by(user)
        except Level.DoesNotExist:
            return False