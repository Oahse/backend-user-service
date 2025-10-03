from tasks import send_email_async
from core.config import settings
from core.utils.redis import redis_client
from fastapi import BackgroundTasks
import secrets
import string

from datetime import datetime, timedelta

class OTPManager:
    def _generate_otp(self, length: int = 6) -> tuple[str, datetime]:
        otp = ''.join(secrets.choice(string.digits) for _ in range(length))
        expiry_time = datetime.utcnow() + timedelta(minutes=10)
        return otp, expiry_time
    
    def is_otp_valid(self, input_otp: str, actual_otp: str, expiry_time: datetime) -> bool:
        now = datetime.utcnow()
        return input_otp == actual_otp and now <= expiry_time
    
otp_manager = OTPManager()

general_context = {
                "company_name": "Banwee",
                "current_year": f'{datetime.utcnow().year}',
                "logo_url": "https://cdn.jsdelivr.net/gh/Oahse/media@main/banwe_logo_green.png",
                "unsubscribe_url": "https://example.com/unsubscribe",
                "privacy_policy_url": "https://example.com/privacy",
                "social_links": {
                    "facebook": "https://facebook.com/banwee",
                    "twitter": "https://twitter.com/banwee",
                    "instagram": "https://instagram.com/banwee"
                }
            }


class EmailService:
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

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
            context=context
        )

    async def _send_password_reset_otp(self, full_name:str, email: str, background_tasks: BackgroundTasks) -> None:
        otp = otp_manager._generate_otp()
        await redis_client.setex(f"password_reset_otp:{email}", 600, otp)
        context = general_context.copy()
        context.update({"customer_name":full_name,"password_reset_otp": otp})
        await self._send_email_task(
            to_email=email,
            mail_type="password_reset",
            background_tasks=background_tasks,
            context=context
        )

    async def _send_email_change_confirmation(self, full_name:str, user_id: str, new_email: str, token: str, background_tasks: BackgroundTasks) -> None:
        await redis_client.setex(f"email_change_confirmation:{user_id}", 600, token)
        context = general_context.copy()
        context.update({
            "customer_name":full_name,
            "confirmation_link": f"https://banwee.pages.dev/confirm-email-change?token={token}&user_id={user_id}" 
        })
        
        await self._send_email_task(
            to_email=new_email,
            mail_type="email_change",
            background_tasks=background_tasks,
            context=context
        )

    async def _send_order_confirmation(self, full_name:str, email: str, order_data: dict, background_tasks: BackgroundTasks):
        context = general_context.copy()
        context["customer_name"]=full_name
        context.update(order_data)

        await self._send_email_task(
            to_email=email,
            mail_type="order_confirmation",
            background_tasks=background_tasks,
            context=order_data
        )

    async def _send_review_request(self, full_name:str, email: str, product_name: str, background_tasks: BackgroundTasks):
        context = general_context.copy()
        context.update({
            "customer_name": full_name,
            "product_name": product_name
        })
        await self._send_email_task(
            to_email=email,
            mail_type="review_request",
            background_tasks=background_tasks,
            context=context
        )

    async def _send_cart_abandonment(self, full_name:str, email: str, cart_items: list, background_tasks: BackgroundTasks):
        context = general_context.copy()
        context.update({
            "customer_name": full_name,
            "cart_items": cart_items
        })
        await self._send_email_task(
            to_email=email,
            mail_type="cart_abandonment",
            background_tasks=background_tasks,
            context=context
        )

    async def _send_back_in_stock(self, full_name:str, email: str, product_name: str, background_tasks: BackgroundTasks):
        context = general_context.copy()
        context.update({
            "customer_name": full_name,
            "product_name": product_name
        })
        await self._send_email_task(
            to_email=email,
            mail_type="back_in_stock",
            background_tasks=background_tasks,
            context = context
            
        )
    
    async def _send_verification_otp(self, full_name:str, email: str, background_tasks: BackgroundTasks) -> None:
        otp, expiry = otp_manager._generate_otp()

        await redis_client.setex(f"email_otp:{email}", 600, otp)

        context = general_context.copy()
        context.update({
            "customer_name": full_name,
            "otp_code": otp,  # Your generated OTP
            "expiry_time": expiry  # Format datetime nicely for email
        })

        await self._send_email_task(
            to_email=email,
            mail_type="activation",
            background_tasks=background_tasks,
            context = context

        )

    
