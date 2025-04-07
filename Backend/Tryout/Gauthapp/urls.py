from django.urls import path
from .views import GoogleLoginAPI

urlpatterns = [
    path('google-login/', GoogleLoginAPI.as_view(), name='google_login'),
]