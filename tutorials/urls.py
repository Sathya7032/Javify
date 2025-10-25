from django.urls import path, include
from .views import *

urlpatterns = [
    path('levels/<int:level_number>/topic/', TopicListView.as_view(), name='topics-list'),
    path('topics/<int:topic_id>/submit/', SubmitAnswersView.as_view(), name='submit-answers'),


    path('levels/', LevelListView.as_view(), name='level-list'),
    path('levels/<int:level_id>/topics/', TopicListView.as_view(), name='topic-list'),
    path('topics/<int:topic_id>/questions/', QuestionListView.as_view(), name='question-list'),

    path('topics/', CodingTopicListView.as_view(), name='coding-topic-list'),
    # List problems under a topic
    path('topics/<int:topic_id>/problems/', CodingProblemListAPIView.as_view(), name='problem-list'),

    # Detail of a specific problem
    path('problems/<int:pk>/', CodingProblemDetailAPIView.as_view(), name='problem-detail'),

     
    path("user/progress/", UserProgressView.as_view(), name="user-progress"),

 ]