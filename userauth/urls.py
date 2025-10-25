from django.urls import path, include
from .views import *

urlpatterns = [
    path('accounts/', include('allauth.urls')),  # Social login callback
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", EmailLoginView.as_view(), name="email-login"),
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),  # Social login endpoint
    path('profile/', ProfileView.as_view(), name='profile'),  # User profile
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
   
    path("", include("tutorials.urls")),

     path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    
]