from rest_framework import routers


from library.views import (
    BookViewSet,
    BorrowingViewSet,
    PaymentViewSet
)

router = routers.DefaultRouter()

router.register("books", BookViewSet, basename="books")
router.register("borrowings", BorrowingViewSet, basename="borrowings")
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = router.urls

app_name = "library"
