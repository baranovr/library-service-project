from django.contrib.auth import get_user_model
from django.test import TestCase

from library.models import Book, Borrowing, Payment

from datetime import datetime, timedelta


class BaseTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            email="email@example.com",
            first_name="Test",
            last_name="User",
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author"
        )
        self.borrowing = Borrowing.objects.create(
            borrow_date=datetime.now(),
            expected_return_date=datetime.now() + timedelta(days=7),
            book=self.book,
            user=self.user
        )


class BookModelTest(BaseTestCase):
    def test_book_creation(self):
        book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.HARD,
            inventory=10,
            daily_fee=1.50
        )
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.author, "Test Author")
        self.assertEqual(book.cover, Book.HARD)
        self.assertEqual(book.inventory, 10)
        self.assertEqual(book.daily_fee, 1.50)

    def test_book_str_representation(self):
        book = Book.objects.create(
            title="Test Book",
            author="Test Author"
        )
        self.assertEqual(str(book), "Test Book - Test Author")


class BorrowingModelTest(BaseTestCase):
    def test_borrowing_creation(self):
        borrow_date = datetime.now()
        expected_return_date = borrow_date + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            borrow_date=borrow_date,
            expected_return_date=expected_return_date,
            book=self.book,
            user=self.user
        )
        self.assertEqual(borrowing.borrow_date, borrow_date)
        self.assertEqual(borrowing.expected_return_date, expected_return_date)
        self.assertIsNone(borrowing.actual_return_date)
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.user, self.user)

    def test_borrowing_str_representation(self):
        borrow_date = datetime.now()
        borrowing = Borrowing.objects.create(
            borrow_date=borrow_date,
            expected_return_date=borrow_date + timedelta(days=7),
            book=self.book,
            user=self.user
        )
        self.assertEqual(str(borrowing), f"{borrow_date} - {self.user}")


class PaymentModelTest(BaseTestCase):
    def test_payment_creation(self):
        payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com/session",
            session_id="test_session_id",
            money_to_pay=10.50
        )
        self.assertEqual(payment.status, Payment.PENDING)
        self.assertEqual(payment.type, Payment.PAYMENT)
        self.assertEqual(payment.borrowing, self.borrowing)
        self.assertEqual(payment.session_url, "https://example.com/session")
        self.assertEqual(payment.session_id, "test_session_id")
        self.assertEqual(payment.money_to_pay, 10.50)

    def test_payment_str_representation(self):
        payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="https://example.com/session",
            session_id="test_session_id",
            money_to_pay=10.50
        )
        self.assertEqual(str(payment), f"{self.borrowing} - {Payment.PENDING}")
