from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class JobNotification(models.Model):
    EXPERIENCE_LEVEL_CHOICES = [
        ('FRESHER', 'Fresher'),
        ('EXPERIENCED', 'Experienced'),
        ('ALL', 'All Levels'),
    ]

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='ALL')
    posted_on = models.DateField(auto_now_add=True)
    last_date = models.DateField(blank=True, null=True)
    description = CKEditor5Field('Description', config_name='extends')
    requirements = CKEditor5Field('Requirements', config_name='extends')
    apply_link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-posted_on']

    def __str__(self):
        return f"{self.title} at {self.company}"
