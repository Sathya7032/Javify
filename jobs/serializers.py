from rest_framework import serializers
from .models import JobNotification

class JobNotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobNotification
        fields = ['id', 'title', 'company', 'location', 'experience_level', 'posted_on', 'last_date']

class JobNotificationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobNotification
        fields = '__all__'  # Show all details in detailed view
