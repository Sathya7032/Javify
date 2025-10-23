from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    xp = models.IntegerField(default=10)       # Default signup bonus XP
    level = models.IntegerField(default=1)     # Starting level
    coins = models.IntegerField(default=5)     # Default signup coins
    avatar = models.URLField(blank=True, null=True)  # Profile picture URL (from Google or custom)

    def __str__(self):
        return f"{self.user.username} - Level {self.level}"

    def add_xp(self, amount):
        """Increase XP and level up if threshold crossed."""
        self.xp += amount
        # Simple example: Level up every 100 XP
        while self.xp >= self.level * 100:
            self.level += 1
        self.save()

# --- Level Model ---
class Level(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Level {self.number}: {self.title}"


# --- Topic Model ---
class Topic(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    explanation = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=1)  # Order within level

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
    options = models.JSONField(blank=True, null=True)  # For MCQs: ["A", "B", "C", "D"]
    correct_answer = models.TextField()  # Store correct text or answer key

    def __str__(self):
        return f"{self.question_text[:50]}... ({self.question_type})"


# --- User Progress Model ---
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

# --- Topic Model ---
class CodingTopic(models.Model):
    name = models.CharField(max_length=200, unique=True)  # e.g., "Conditional Statements"
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- Coding Problem Model ---
class CodingProblem(models.Model):
    topic = models.ForeignKey(CodingTopic, on_delete=models.CASCADE, related_name="problems")
    sno = models.PositiveIntegerField()  # Serial number for ordering
    title = models.CharField(max_length=255)
    description =   models.TextField();        # CKEditor rich-text description
    code_snippet = models.TextField(blank=True, null=True)  # Code snippet field
    video_url = models.URLField(blank=True, null=True)      # Optional video URL
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['topic', 'sno']
        unique_together = ('topic', 'sno')

    def __str__(self):
        return f"{self.topic.name} - {self.sno}: {self.title}"