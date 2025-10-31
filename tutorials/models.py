from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

# --- Level Model ---
class Level(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    xp_reward = models.PositiveIntegerField(default=50)       # XP after completing all topics
    coin_reward = models.PositiveIntegerField(default=20)     # Coins after completing all topics
    required_topics = models.PositiveIntegerField(default=5)  # How many topics user must complete to finish this level

    def __str__(self):
        return f"Level {self.number}: {self.title}"

    def is_completed_by(self, user):
        """Check if user completed all topics in this level."""
        completed_count = UserProgress.objects.filter(
            user=user, topic__level=self, completed=True
        ).count()
        return completed_count >= self.required_topics


# --- Topic Model ---
class Topic(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    explanation = CKEditor5Field('Explanation', config_name='extends')
    video_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.title} (Level {self.level.number})"


# --- Question Model ---
class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice'),
        ('OUTPUT', 'Output Guess'),
        ('FILL', 'Fill in the Blanks'),
    ]
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    question_text = models.TextField()
    options = models.JSONField(blank=True, null=True)
    correct_answer = models.TextField()

    def __str__(self):
        return f"{self.question_text[:50]}... ({self.question_type})"


# --- CodingTopic Model ---
class CodingTopic(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# --- CodingProblem Model ---
class CodingProblem(models.Model):
    topic = models.ForeignKey(CodingTopic, on_delete=models.CASCADE, related_name="problems")
    sno = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    explanation = CKEditor5Field('Explanation', config_name='extends', default=' ')
    code_snippet = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['topic', 'sno']
        unique_together = ('topic', 'sno')

    def __str__(self):
        return f"{self.topic.name} - {self.sno}: {self.title}"


# --- User Progress ---
class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    date_completed = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'topic')

    def mark_completed(self):
        self.completed = True
        self.date_completed = timezone.now()
        self.save()


# --- Track Level Completion ---
class UserLevelCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_levels')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    date_completed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'level')

    def __str__(self):
        return f"{self.user.username} - Level {self.level.number} completed"
