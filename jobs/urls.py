from django.urls import path
from .views import JobNotificationListAPIView, JobNotificationDetailAPIView

urlpatterns = [
    path('jobs/', JobNotificationListAPIView.as_view(), name='job-list'),
    path('jobs/<int:id>/', JobNotificationDetailAPIView.as_view(), name='job-detail'),
]
