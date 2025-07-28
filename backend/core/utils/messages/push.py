# Firebase Cloud Messaging (FCM)
import asyncio
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("path/to/your-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

async def push(id: str, to_user_id: str, title: str, body: str, type: str, token: str, data: dict = {}):
    # Simulate sending notification asynchronously
    print(f"Pushing notification {id} to {to_user_id}")
    # await your actual async send logic here
    data['type'] = type
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {'type': type},
    )

    response = await messaging.send(message)
    print(f"Notification sent: {response}")

def send_push(id: str, to_user_id: str, title: str, body: str, type: str, token: str, data: dict = {}):
    # If you're inside a running event loop (e.g., FastAPI), use this instead:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If inside an async context (like FastAPI), schedule push task
        asyncio.create_task(push(id, to_user_id, title, body, type, token, data))
    else:
        # Otherwise, run it synchronously (blocking) as entry point
        asyncio.run(push(id, to_user_id, title, body, type, token, data))