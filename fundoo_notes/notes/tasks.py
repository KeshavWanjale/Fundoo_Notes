from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from loguru import logger


@shared_task
def send_reminder_email(note_title,email):
    try:
        body=f"Reminder for Note: {note_title}"
        subject = f"Reminder"
        send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        )
    except Exception as e:
        logger.info("Note not found")