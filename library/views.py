import stripe

from django.utils import timezone

from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from library.send_notifications import send_telegram_notification

from library.models import Book, Borrowing, Payment
from library.serializers import (
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BorrowingSerializer,
    PaymentSerializer,
    BorrowingListSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            return [permissions.AllowAny()]
        else:
            return [permissions.IsAdminUser()]

    def get_queryset(self):
        title = self.request.query_params.get("title", None)
        author = self.request.query_params.get("author", None)
        cover = self.request.query_params.get("cover", None)

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if author:
            queryset = queryset.filter(author__icontains=author)

        if cover:
            queryset = queryset.filter(cover__icontains=cover)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer

        if self.action == "retrieve":
            return BookDetailSerializer

        return BookSerializer


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_permissions(self):
        if self.action == "list":
            return [permissions.AllowAny()]
        elif self.action == "destroy":
            return [permissions.IsAdminUser()]
        else:
            return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.validated_data["book"]

        if book.inventory > 0:
            book.inventory -= 1
            book.save()
            borrowing = serializer.save()

            message = (
                f"BOOK BORROWING 📖\n"
                f"\n"
                f"New borrowing created ✅:\n"
                f"User👤:  {borrowing.user.username}\n"
                f"Book📖:  {borrowing.book.title}\n"
            )
            send_telegram_notification(message)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user_id", None)
        is_active = self.request.query_params.get("is_active", None)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active is not None:
            is_active = is_active.lower() == "true"
            if is_active:
                queryset = queryset.filter(actual_return_date__isnull=True)
            else:
                queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        return BorrowingSerializer

    @action(detail=True, methods=["POST"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date:
            return Response(
                {"detail": "Book already returned"},
                status=status.HTTP_400_BAD_REQUEST
            )

        borrowing.actual_return_date = timezone.now()
        borrowing.save()

        book = borrowing.book
        book.inventory += 1
        book.save()

        message = (
            f"BOOK RETURNED ↩️\n"
            f"\n"
            f"Book returned successfully ✅:\n"
            f"User👤:  {borrowing.user.username}\n"
            f"Book📖:  {borrowing.book.title}\n"
        )
        send_telegram_notification(message)

        return Response(
            {"detail": "Book returned successfully"},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            self.perform_destroy(borrowing)

            message = (
                f"BOOK DELETED ❌\n"
                f"\n"
                f"Book has been deleted successfully ✅:\n"
                f"User👤:  {borrowing.user.username}\n"
                f"Book📖:  {borrowing.book.title}\n"
            )
            send_telegram_notification(message)

            return Response(
                {"detail": "Book has been deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(status=status.HTTP_400_BAD_REQUEST)


class PaymentViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(payment.money_to_pay * 100),
                    "product_data": {
                        "name": f"Payment for Borrowing #{
                        payment.borrowing.id
                        }",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.build_absolute_uri("/api/payments/success/"),
            cancel_url=request.build_absolute_uri("/api/payments/cancel/"),
        )

        payment.session_url = session.url
        payment.session_id = session.id
        payment.save()

        return Response(
            {"session_url": session.url}, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"])
    def success(self, request):
        session_id = request.query_params.get("session_id")

        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                payment = Payment.objects.get(session_id=session_id)
                payment.status = Payment.PAID
                payment.save()

                send_telegram_notification.delay(
                    f"Payment successful: {payment.user.username} "
                    f"paid for borrowing #{payment.borrowing.id}"
                )
                return Response({"message": "Payment successful"})
            except (stripe.error.InvalidRequestError, Payment.DoesNotExist):
                pass

        return Response(
            {"message": "Invalid payment session"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=["get"])
    def cancel(self, request):
        return Response({"message": "Payment canceled"})
