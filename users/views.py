from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.serializers import UserProfileSerializer, UserRegisterSerializer

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="Creates a new guest account with email-based authentication.",
    )
)
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (AllowAny,)


@extend_schema_view(
    get=extend_schema(
        summary="Get current user profile info",
        description="Retrieves the profile details of the currently logged-in user.",
    ),
    put=extend_schema(
        summary="Update current user profile (Full)",
        description="Updates all editable fields of the authenticated user's profile.",
    ),
    patch=extend_schema(
        summary="Update current user profile (Partial)",
        description="Partially updates editable fields "
        "of the authenticated user's profile.",
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
