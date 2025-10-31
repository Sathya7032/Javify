from django.urls import path
from .views import (
    # Level & Topic Views
    LevelListView,
    TopicListView,
    QuestionListView,
    SubmitAnswersView,

    # User Progress
    UserProgressView,
    UserLevelProgressView,

    # Coding Section
    CodingTopicListView,
    CodingProblemListAPIView,
    CodingProblemDetailAPIView,
)

urlpatterns = [
    # ---------------------------------
    # 📘 LEVELS & TOPICS
    # ---------------------------------
    path('levels/', LevelListView.as_view(), name='level-list'),
    path('levels/<int:level_id>/topics/', TopicListView.as_view(), name='topic-list'),
    path('topics/<int:topic_id>/questions/', QuestionListView.as_view(), name='question-list'),
    path('topics/<int:topic_id>/submit/', SubmitAnswersView.as_view(), name='submit-answers'),

    # ---------------------------------
    # 👤 USER PROGRESS
    # ---------------------------------
    path('user/progress/', UserProgressView.as_view(), name='user-progress'),
    path('user/levels/', UserLevelProgressView.as_view(), name='user-level-progress'),

    # ---------------------------------
    # 💻 CODING SECTION
    # ---------------------------------
    path('coding/topics/', CodingTopicListView.as_view(), name='coding-topic-list'),
    path('coding/topics/<int:topic_id>/problems/', CodingProblemListAPIView.as_view(), name='coding-problem-list'),
    path('coding/problems/<int:pk>/', CodingProblemDetailAPIView.as_view(), name='coding-problem-detail'),
]
