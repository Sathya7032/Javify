from django.contrib import admin
from .models import *

# --- Profile Admin ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'xp', 'level', 'coins')
    search_fields = ('user__username', 'user__email')
    list_filter = ('level',)
    ordering = ('-xp',)
