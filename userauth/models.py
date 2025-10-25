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



