from celery import shared_task

import django.utils.timezone

from library.models import Borrowing
from library.send_notifications import send_telegram_notification


@shared_task
def check_overdue_borrowings():
    now = timezone.now()
    borrowing = Borrowing.objects.filter(
        expected_return_date__lte=now, actual_return_date__isnull=True
    )
    message = (
        "OVERDUE BOOK NOTICE❗️\n"
        f"User👤: {borrowing.user.username}\n"
        f"Book📖: {borrowing.book}\n"
        f"Expected return date📆: {borrowing.expected_return_date}\n"
    )
    send_telegram_notification(message)
