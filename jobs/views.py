from rest_framework import generics
from .models import JobNotification
from .serializers import JobNotificationListSerializer, JobNotificationDetailSerializer
from rest_framework.permissions import AllowAny

class JobNotificationListAPIView(generics.ListAPIView):
    """
    List all active job notifications.
    """
    queryset = JobNotification.objects.filter(is_active=True)
    serializer_class = JobNotificationListSerializer
    permission_classes = [AllowAny]

class JobNotificationDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve detailed info about a single job notification.
    """
    queryset = JobNotification.objects.filter(is_active=True)
    serializer_class = JobNotificationDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
