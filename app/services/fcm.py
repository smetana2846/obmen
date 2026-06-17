import firebase_admin
from firebase_admin import messaging
from firebase_admin import credentials
from app.core.config import settings
from typing import Optional

try:
    firebase_admin.get_app()
except ValueError:
    if settings.FCM_SERVER_KEY:
        cred = credentials.Certificate(settings.FCM_SERVER_KEY)
        firebase_admin.initialize_app(cred)

async def send_push_notification(firebase_token: str, title: str, body: str, data: Optional[dict] = None):
    if not firebase_token:
        return
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=firebase_token,
            data=data
        )
        await messaging.send(message)
    except Exception as e:
        print(f"Failed to send notification: {e}")