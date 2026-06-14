from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.serializers import UserProfileSerializer, UserRegisterSerializer

User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (AllowAny,)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
