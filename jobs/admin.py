# jobs/admin.py
from django.contrib import admin
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import JobNotification

# ------------------------------
# Admin Form with CKEditor5
# ------------------------------
class JobNotificationAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditor5Widget(config_name='extends'))
    requirements = forms.CharField(widget=CKEditor5Widget(config_name='extends'))

    class Meta:
        model = JobNotification
        fields = '__all__'


# ------------------------------
# Admin Panel Configuration
# ------------------------------
@admin.register(JobNotification)
class JobNotificationAdmin(admin.ModelAdmin):
    form = JobNotificationAdminForm

    # Display these columns in the list view
    list_display = (
        'title',
        'company',
        'experience_level',
        'location',
        'posted_on',
        'last_date',
        'is_active',
    )

    # Make title clickable
    list_display_links = ('title',)

    # Filters on right sidebar
    list_filter = ('experience_level', 'location', 'is_active', 'posted_on')

    # Searchable fields
    search_fields = ('title', 'company', 'description', 'requirements', 'location')

    # Default ordering
    ordering = ('-posted_on',)

    # Make some fields readonly
    readonly_fields = ('posted_on',)

    # Field grouping in the detail view
    fieldsets = (
        ('Job Details', {
            'fields': ('title', 'company', 'experience_level', 'location', 'apply_link', 'is_active', 'posted_on', 'last_date')
        }),
        ('Content', {
            'fields': ('description', 'requirements')
        }),
    )
