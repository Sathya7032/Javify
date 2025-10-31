from django.contrib import admin
from .models import *
from django_ckeditor_5.widgets import CKEditor5Widget
# ---------------------------------
# 🔹 INLINE: Topics under Level
# ---------------------------------
class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ('title', 'order', 'video_url')
    ordering = ('order',)


# ---------------------------------
# 🔹 LEVEL ADMIN
# ---------------------------------
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'num_topics', 'xp_reward', 'coin_reward', 'required_topics')
    list_editable = ('xp_reward', 'coin_reward', 'required_topics')
    search_fields = ('title',)
    ordering = ('number',)
    inlines = [TopicInline]

    fieldsets = (
        (None, {
            'fields': ('number', 'title', 'description')
        }),
        ('Rewards & Requirements', {
            'fields': ('xp_reward', 'coin_reward', 'required_topics'),
            'classes': ('collapse',),
        }),
    )

    # ✅ Add this method
    def num_topics(self, obj):
        """Return how many topics belong to this level."""
        return obj.topics.count()

    num_topics.short_description = "Topics"


# ---------------------------------
# 🔹 INLINE: Questions under Topic
# ---------------------------------
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('question_text', 'question_type', 'options', 'correct_answer')
    ordering = ('id',)


# ---------------------------------
# 🔹 TOPIC ADMIN
# ---------------------------------
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'order')
    list_filter = ('level',)
    search_fields = ('title', 'explanation')
    ordering = ('level__number', 'order')
    inlines = [QuestionInline]

    fieldsets = (
        (None, {
            'fields': ('level', 'title', 'explanation', 'video_url', 'order')
        }),
    )

    # Replace the 'explanation' field with CKEditor widget
    formfield_overrides = {
        models.TextField: {'widget': CKEditor5Widget(config_name='extends')}
    }

# ---------------------------------
# 🔹 QUESTION ADMIN
# ---------------------------------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'topic', 'question_type')
    list_filter = ('question_type', 'topic__level')
    search_fields = ('question_text',)
    ordering = ('topic__order',)


# ---------------------------------
# 🔹 USER PROGRESS ADMIN
# ---------------------------------
@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'completed', 'correct_answers', 'total_questions', 'date_completed')
    list_filter = ('completed', 'topic__level')
    search_fields = ('user__username', 'topic__title')
    ordering = ('-date_completed',)
    readonly_fields = ('date_completed',)


# ---------------------------------
# 🔹 USER LEVEL COMPLETION ADMIN
# ---------------------------------
@admin.register(UserLevelCompletion)
class UserLevelCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'date_completed')
    list_filter = ('level',)
    search_fields = ('user__username', 'level__title')
    ordering = ('-date_completed',)
    readonly_fields = ('date_completed',)


# ---------------------------------
# 💻 CODING SECTION ADMIN
# ---------------------------------
class CodingProblemInline(admin.TabularInline):
    model = CodingProblem
    extra = 0
    fields = ('sno', 'title', 'video_url', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('sno',)
    show_change_link = True


@admin.register(CodingTopic)
class CodingTopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    inlines = [CodingProblemInline]
    readonly_fields = ('created_at',)

# --- CODING PROBLEM ADMIN ---
@admin.register(CodingProblem)
class CodingProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'sno', 'created_at')
    list_filter = ('topic',)
    search_fields = ('title', 'explanation', 'code_snippet')
    ordering = ('topic', 'sno')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('topic', 'sno', 'title', 'explanation', 'code_snippet', 'video_url')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    # Replace the 'explanation' field with CKEditor widget
    formfield_overrides = {
        models.TextField: {'widget': CKEditor5Widget(config_name='extends')}
    }
