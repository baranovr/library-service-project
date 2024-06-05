from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import CreateUserViewSet, UserProfileView

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register"),
    path("me/", UserProfileView.as_view(), name="me"),
    path("token/", TokenObtainPairView.as_view(), name="create-token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh-token"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

app_name = "user"
