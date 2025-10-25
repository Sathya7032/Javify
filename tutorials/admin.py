from django.contrib import admin
from .models import *
# Register your models here.

# --- Inline for Topics under Level ---
class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ('title', 'order', 'video_url')

# --- Level Admin ---
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'description')
    inlines = [TopicInline]
    search_fields = ('title',)
    ordering = ('number',)


# --- Inline for Questions under Topic ---
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('question_text', 'question_type', 'options', 'correct_answer')


# --- Topic Admin ---
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'order')
    list_filter = ('level',)
    search_fields = ('title', 'explanation')
    inlines = [QuestionInline]
    ordering = ('level__number', 'order')


# --- Question Admin ---
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'topic', 'question_type')
    list_filter = ('question_type', 'topic__level')
    search_fields = ('question_text',)
    ordering = ('topic__order',)


# --- UserProgress Admin ---
@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'completed', 'correct_answers', 'total_questions', 'date_completed')
    list_filter = ('completed', 'topic__level')
    search_fields = ('user__username', 'topic__title')
    ordering = ('-date_completed',)

# --- Inline for problems inside topic admin (optional) ---
class CodingProblemInline(admin.TabularInline):
    model = CodingProblem
    extra = 0
    fields = ('sno', 'title', 'video_url', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('sno',)
    show_change_link = True

# --- Topic Admin ---
@admin.register(CodingTopic)
class CodingTopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    inlines = [CodingProblemInline]

# --- Problem Admin ---
@admin.register(CodingProblem)
class CodingProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'sno', 'created_at')
    list_filter = ('topic',)
    search_fields = ('title', 'description', 'code_snippet')
    ordering = ('topic', 'sno')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('topic', 'sno', 'title', 'description', 'code_snippet', 'video_url')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )