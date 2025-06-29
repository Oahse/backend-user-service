# tasks.py
from celery import Celery
from core.utils.messages.email import send_activation_email
import asyncio
from core.config import settings

celery_app = Celery('worker', broker=str(settings.REDIS_URL) )

@celery_app.task
def send_email_celery(to_email: str,activation_link: str,from_email: str,from_password: str):
    asyncio.run(send_activation_email( 
                              to_email=to_email, 
                              activation_link=activation_link,
                              from_email=from_email,
                              from_password=from_password)
                              )
def enqueue_email_task(to_email: str,activation_link: str,from_email: str,from_password: str):
    send_email_celery.delay(to_email,activation_link,from_email,from_password)