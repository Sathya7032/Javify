from rest_framework import serializers
from .models import *

# -----------------------------
# Question Serializer
# -----------------------------
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_type', 'question_text', 'options', 'correct_answer']


# -----------------------------
# Topic Serializer
# -----------------------------
class TopicSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'title', 'explanation', 'video_url', 'order', 'questions_count']


# -----------------------------
# Level Serializer
# -----------------------------
class LevelSerializer(serializers.ModelSerializer):
    topics_count = serializers.IntegerField(source='topics.count', read_only=True)

    class Meta:
        model = Level
        fields = ['id', 'number', 'title', 'description', 'topics_count']

class CodingTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingTopic
        fields = ['id', 'name', 'description', 'created_at']

# Serializer for the problem list (summary)
class CodingProblemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingProblem
        fields = ['id', 'title', 'created_at']

# Serializer for detailed problem view
class CodingProblemDetailSerializer(serializers.ModelSerializer):
    topic = serializers.StringRelatedField()  # Returns topic name

    class Meta:
        model = CodingProblem
        fields = ['id', 'topic', 'sno', 'title', 'description', 'code_snippet', 'video_url', 'created_at']
