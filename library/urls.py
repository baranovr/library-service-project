from rest_framework import routers
from django.urls import path

from backend.library.views import (
    BookViewSet,
    BorrowingViewSet,
    PaymentViewSet
)

router = routers.DefaultRouter()

router.register("books", BookViewSet, basename="books")
router.register("borrowings", BorrowingViewSet, basename="borrowings")
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path(
        "borrowings/<int:pk>/return/",
        BorrowingViewSet.as_view({"post": "return_book"}),
        name="borrowing-return"
    )
] + router.urls

app_name = "library"
