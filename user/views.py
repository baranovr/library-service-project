from rest_framework import generics, permissions

from user.serializers import UserSerializer, UserProfileSerializer


class CreateUserViewSet(generics.CreateAPIView):
    serializer_class = UserSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
