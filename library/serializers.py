from django.contrib.auth import get_user_model
from rest_framework import serializers

from library.models import Book, Borrowing, Payment

from user.serializers import UserSerializer


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        )


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        )


class BookDetailSerializer(serializers.ModelSerializer):
    borrowings = serializers.SerializerMethodField()

    def get_borrowings(self, obj):
        borrowings = Borrowing.objects.filter(book=obj)
        return BorrowingSerializer(borrowings, many=True).data

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
            "borrowings",
        )


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source="book", write_only=True
    )
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), source="user", write_only=True
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "book_id",
            "user",
            "user_id"
        )


class BorrowingListSerializer(BorrowingSerializer):
    user = UserSerializer(source="username", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "user",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingSerializer(read_only=True)
    borrowing_id = serializers.PrimaryKeyRelatedField(
        queryset=Borrowing.objects.all(), source="borrowing", write_only=True
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "borrowing_id",
            "session_url",
            "session_id",
            "money_to_pay"
        )
