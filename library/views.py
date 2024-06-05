import stripe

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from library.models import Book, Borrowing, Payment
from library.serializers import (
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BorrowingSerializer,
    PaymentSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

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


class BorrowingView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.validated_data["book"]

        if book.inventory > 0:
            book.inventory -= 1
            book.save()
            self.perform_create(serializer)
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

            queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset

    @action(detail=True, methods=["POST"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        book = borrowing.book

        if borrowing.actual_return_date is None:
            borrowing.actual_return_date = timezone.now().date()
            borrowing.save()
            book.inventory += 1
            book.save()
            return Response({"detail": "Book returned successfully"})

        return Response(status=status.HTTP_400_BAD_REQUEST)


class PaymentViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

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
