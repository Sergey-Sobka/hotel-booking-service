from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.views import UserRegisterView, UserProfileView

app_name = "users"

urlpatterns = [
    path("", UserRegisterView.as_view(), name="register"),
    path("me/", UserProfileView.as_view(), name="me"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
