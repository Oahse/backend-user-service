from fastapi import APIRouter, HTTPException, BackgroundTasks
from services.notification import NotificationService
from schemas.notification import NotificationCreate, TelegramNotificationCreate
from typing import Optional
from core.utils.response import Response  # your custom response function

router = APIRouter(prefix='/api/v1/notify', tags=["Notification"])


@router.post("/sms")
async def send_sms_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks
):
    service = NotificationService(background_tasks)
    result, error = await service.send_sms_message(
        to_user_id=notification.to_user_id,
        body=notification.body,
        token=notification.token,
        data=notification.data,
        title=notification.title
    )
    if error:
        raise HTTPException(status_code=500, detail=error)
    return Response(data=None, success=True, message=result, code=200)


@router.post("/push")
async def send_push_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks
):
    service = NotificationService(background_tasks)
    result, error = await service.send_push_message(
        to_user_id=notification.to_user_id,
        body=notification.body,
        token=notification.token,
        data=notification.data,
        title=notification.title
    )
    if error:
        raise HTTPException(status_code=500, detail=error)
    return Response(data=None, success=True, message=result, code=200)


@router.post("/telegram")
async def send_telegram_message(
    notification: TelegramNotificationCreate,
    background_tasks: BackgroundTasks
):
    service = NotificationService(background_tasks)
    result, error = await service.send_telegram_message(
        chat_id=notification.chat_id,
        text=notification.text,
        photo_path=notification.photo_path,
        document_path=notification.document_path,
        photo_caption=notification.photo_caption,
        document_caption=notification.document_caption
    )
    if error:
        raise HTTPException(status_code=500, detail=error)
    return Response(data=None, success=True, message=result, code=200)


@router.post("/whatsapp")
async def send_whatsapp_message(
    to_phone_number: str,
    message: str,
    media_url: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    service = NotificationService(background_tasks)
    result, error = await service.send_whatsapp_message(
        to_phone_number=to_phone_number,
        message=message,
        media_url=media_url
    )
    if error:
        raise HTTPException(status_code=500, detail=error)
    return Response(data=None, success=True, message=result, code=200)
