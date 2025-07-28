# tasks.py
from celery import Celery
from core.config import settings
from core.utils.messages.email import send_email

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task
def send_email_async(to_email: str, from_email: str, from_password: str, mail_type: str, **kwargs):
    print(f"Sending email to {to_email}: {mail_type}\n")
    send_email(
        to_email=to_email,
        from_email=from_email,
        from_password=from_password,
        mail_type=mail_type,
        **kwargs
    )
