from tasks import send_email_async
from core.config import settings
from core.utils.redis import redis_client
from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
import secrets,string, re

class EmailService:
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks
    
    def _generate_otp(self, length: int = 6) -> str:
        return ''.join(secrets.choice(string.digits) for _ in range(length))

    async def _send_email_task(
        self,
        to_email: str,
        mail_type: str,
        background_tasks: BackgroundTasks,
        context: dict
    ):
        background_tasks.add_task(
            send_email_async.delay,
            to_email=to_email,
            from_email=settings.SMTP_USER,
            from_password=settings.SMTP_PASSWORD,
            mail_type=mail_type,
            **context
        )

    async def _send_password_reset_otp(self, email: str, background_tasks: BackgroundTasks) -> None:
        otp = self._generate_otp()
        await redis_client.setex(f"password_reset_otp:{email}", 600, otp)
        await self._send_email_task(
            to_email=email,
            mail_type="password_reset",
            background_tasks=background_tasks,
            context={"reset_link": otp}
        )

    async def _send_email_change_confirmation(self, new_email: str, token: str, background_tasks: BackgroundTasks) -> None:
        await redis_client.setex(f"email_change_confirmation:{new_email}", 600, token)
        await self._send_email_task(
            to_email=new_email,
            mail_type="email_change",
            background_tasks=background_tasks,
            context={"token": token}
        )

    async def _send_order_confirmation(self, email: str, order_data: dict, background_tasks: BackgroundTasks):
        await self._send_email_task(
            to_email=email,
            mail_type="order_confirmation",
            background_tasks=background_tasks,
            context=order_data
        )

    async def _send_review_request(self, email: str, product_name: str, background_tasks: BackgroundTasks):
        await self._send_email_task(
            to_email=email,
            mail_type="review_request",
            background_tasks=background_tasks,
            context={"product_name": product_name}
        )

    async def _send_cart_abandonment(self, email: str, cart_items: list, background_tasks: BackgroundTasks):
        await self._send_email_task(
            to_email=email,
            mail_type="cart_abandonment",
            background_tasks=background_tasks,
            context={"cart_items": cart_items}
        )

    async def _send_back_in_stock(self, email: str, product_name: str, background_tasks: BackgroundTasks):
        await self._send_email_task(
            to_email=email,
            mail_type="back_in_stock",
            background_tasks=background_tasks,
            context={"product_name": product_name}
        )
    
    async def _send_verification_otp(self, email: str, background_tasks: BackgroundTasks) -> None:
        otp = self._generate_otp()
        await redis_client.setex(f"email_otp:{email}", 600, otp)
        await self._send_email_task(
            to_email=email,
            mail_type="activation",
            background_tasks=background_tasks,
            context={"activation_link": otp}
        )

    
