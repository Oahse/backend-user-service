from fastapi import BackgroundTasks
from typing import Optional, Tuple, Dict, Any
from core.utils.messages.push import send_push
from core.utils.messages.sms import send_sms
from core.utils.messages.whatsapp import whatapp_bot
from core.utils.messages.telegram import TelegramBotHandler as tbot


class NotificationService:
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    async def send_sms_message(
        self,
        to_user_id: str,
        body: str,
        token: str,
        data: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """Enqueue SMS message sending in background tasks."""
        if data is None:
            data = {}
        try:
            self.background_tasks.add_task(
                send_sms,
                to_user_id=to_user_id,
                title=title,
                body=body,
                token=token,
                data=data
            )
            return "SMS enqueued successfully", None
        except Exception as e:
            return None, f"Failed to enqueue SMS message: {str(e)}"
        
    async def send_push_message(
        self,
        to_user_id: str,
        body: str,
        token: str,
        data: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """Enqueue push notification sending in background tasks."""
        if data is None:
            data = {}
        try:
            self.background_tasks.add_task(
                send_push,
                to_user_id=to_user_id,
                title=title,
                body=body,
                token=token,
                data=data
            )
            return "Push notification enqueued successfully", None
        except Exception as e:
            return None, f"Failed to enqueue push notification: {str(e)}"

    async def send_telegram_message(
        self,
        chat_id: int,
        text: Optional[str] = None,
        photo_path: Optional[str] = None,
        document_path: Optional[str] = None,
        photo_caption: Optional[str] = None,
        document_caption: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """Enqueue Telegram message sending in background tasks."""
        try:
            self.background_tasks.add_task(
                tbot.send,
                chat_id=chat_id,
                text=text,
                photo_path=photo_path,
                document_path=document_path,
                photo_caption=photo_caption,
                document_caption=document_caption
            )
            return "Telegram message enqueued successfully", None
        except Exception as e:
            return None, f"Failed to enqueue Telegram message: {str(e)}"

    async def send_whatsapp_message(
        self,
        to_phone_number: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Enqueue WhatsApp message sending in background tasks (placeholder)."""
        try:
            # Uncomment and implement your WhatsApp sending logic here
            self.background_tasks.add_task(whatapp_bot.send_whatsapp, to_phone_number=to_phone_number, message=message, media_url=media_url)
            return "WhatsApp message enqueued successfully", None
        except Exception as e:
            return None, f"Failed to enqueue WhatsApp message: {str(e)}"
