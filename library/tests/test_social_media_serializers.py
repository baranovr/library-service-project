from django.test import TestCase
from django.contrib.auth import get_user_model

from library.models import Book, Borrowing
from library.serializers import (
    BookSerializer,
    BorrowingSerializer,
    PaymentSerializer
)


class BookSerializerTest(TestCase):
    def setUp(self):
        self.book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": Book.HARD,
            "inventory": 10,
            "daily_fee": 1.50
        }
        self.book = Book.objects.create(**self.book_data)

    def test_book_serializer(self):
        serializer = BookSerializer(instance=self.book)
        self.assertEqual(serializer.data["title"], self.book_data["title"])
        self.assertEqual(serializer.data["author"], self.book_data["author"])
        self.assertEqual(serializer.data["cover"], self.book_data["cover"])
        self.assertEqual(
            serializer.data["inventory"], self.book_data["inventory"]
        )
        self.assertEqual(
            str(float(serializer.data["daily_fee"])),
            str(self.book_data["daily_fee"])
        )


class BorrowingSerializerTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass",
            email="email@example.com"
        )
        self.book = Book.objects.create(
            title="Test Book", author="Test Author"
        )
        self.borrowing_data = {
            "borrow_date": "2023-06-01T10:00:00+00:00",
            "expected_return_date": "2023-06-08T10:00:00+00:00",
            "book_id": self.book.id,
            "user_id": self.user.id
        }

    def test_borrowing_serializer(self):
        serializer = BorrowingSerializer(data=self.borrowing_data)
        self.assertTrue(serializer.is_valid())
        borrowing = serializer.save()
        self.assertEqual(
            borrowing.borrow_date.isoformat(),
            self.borrowing_data["borrow_date"]
        )
        self.assertEqual(
            borrowing.expected_return_date.isoformat(),
            self.borrowing_data["expected_return_date"]
        )
        self.assertEqual(borrowing.book.id, self.borrowing_data["book_id"])
        self.assertEqual(borrowing.user.id, self.borrowing_data["user_id"])


class PaymentSerializerTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass",
            email="email@example.com"
        )
        self.book = Book.objects.create(
            title="Test Book", author="Test Author"
        )
        self.borrowing = Borrowing.objects.create(
            borrow_date="2023-06-01T11:00:00+00:00",
            expected_return_date="2023-06-08T11:00:00+00:00",
            book=self.book,
            user=self.user
        )
        self.payment_data = {
            "borrowing_id": self.borrowing.id,
            "session_url": "https://example.com/session",
            "session_id": "test_session_id",
            "money_to_pay": 10.50
        }

    def test_payment_serializer(self):
        serializer = PaymentSerializer(data=self.payment_data)
        self.assertTrue(serializer.is_valid())
        payment = serializer.save()
        self.assertEqual(
            payment.borrowing.id, self.payment_data["borrowing_id"]
        )
        self.assertEqual(
            payment.session_url, self.payment_data["session_url"]
        )
        self.assertEqual(
            payment.session_id, self.payment_data["session_id"]
        )
        self.assertEqual(
            payment.money_to_pay, self.payment_data["money_to_pay"]
        )
