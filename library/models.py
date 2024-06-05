from django.db import models

from library_service import settings


class Book(models.Model):
    HARD = "HARD"
    SOFT = "SOFT"
    COVER_CHOICES = [
        (HARD, "Hard"),
        (SOFT, "Soft"),
    ]
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    cover = models.CharField(
        max_length=4, choices=COVER_CHOICES, default=SOFT
    )
    inventory = models.PositiveIntegerField(default=0)
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} - {self.author}"


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["borrow_date"]
        unique_together = [["borrow_date", "user"]]

    def __str__(self):
        return f"{self.borrow_date} - {self.user}"


class Payment(models.Model):
    PENDING = "PENDING"
    PAID = "PAID"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PAID, "Paid"),
    ]
    PAYMENT = "PAYMENT"
    FINE = "FINE"
    TYPE_CHOICES = [
        (PAYMENT, "Payment"),
        (FINE, "Fine"),
    ]
    status = models.CharField(
        max_length=7, choices=STATUS_CHOICES, default=PENDING
    )
    type = models.CharField(
        max_length=7, choices=TYPE_CHOICES, default=PAYMENT
    )
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE)
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["status"]
        unique_together = [["borrowing", "session_url"]]

    def __str__(self):
        return f"{self.borrowing} - {self.status}"
