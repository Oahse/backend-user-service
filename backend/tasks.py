# tasks.py
import asyncio
from celery import Celery
from asgiref.sync import async_to_sync
from core.config import settings
from core.utils.messages.email import send_email

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task(bind=True, max_retries=3)
def send_email_async(self, to_email, from_email, from_password, mail_type, context={}):
    try:
        send_email(
            to_email=to_email,
            from_email=from_email,
            from_password=from_password,
            mail_type=mail_type,
            context=context
        )
    except Exception as exc:
        print(f"❌ Failed to send email: {exc}")
        self.retry(exc=exc, countdown=30)
