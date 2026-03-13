from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel


class NotificationIn(BaseModel):
    recipient: str
    message: str


class NotificationOut(NotificationIn):
    id: int
    created_at: datetime


app = FastAPI(title="Notification Service")

_notifications: List[NotificationOut] = []
_id_counter = 1


@app.post("/notifications", response_model=NotificationOut, tags=["notifications"])
async def create_notification(payload: NotificationIn) -> NotificationOut:
    global _id_counter
    notif = NotificationOut(
        id=_id_counter,
        recipient=payload.recipient,
        message=payload.message,
        created_at=datetime.utcnow(),
    )
    _id_counter += 1
    _notifications.append(notif)
    return notif


@app.get("/notifications", response_model=List[NotificationOut], tags=["notifications"])
async def list_notifications() -> List[NotificationOut]:
    return _notifications


@app.get("/")
async def root():
    return {"message": "Notification Service. Use /notifications to create or list."}

