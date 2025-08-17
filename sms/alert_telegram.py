# sms/alert_telegram.py
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from fastapi import APIRouter, HTTPException
from pyrogram import Client
from sqlalchemy.orm import Session

from database import get_db
from database.models import Device, PhoneNumber, User

router = APIRouter(tags=["TELEGRAM"])

pyro_app = Client(
    "alert_sender",
    api_id="ид",
    api_hash="хеш",
    bot_token='токен'
)

# ✅ Specify your bot's token
AI_BOT_TOKEN = "токен"
aiobot = Bot(token=AI_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))


# --- Helper function to get common data ---
def get_alert_data(device_connect: str, db: Session):
    device = db.query(Device).filter_by(device_connect=device_connect).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    user = db.query(User).filter_by(id=device.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Owner not found")

    phone_numbers = db.query(PhoneNumber).filter_by(device_connect=device_connect).all()

    return device, user, phone_numbers


# --- Send alert via Pyrogram ---
@router.post("/send-alert-pyrogram")
async def send_alert_pyr(device_connect: str):
    db: Session = next(get_db())
    device, user, phone_numbers = get_alert_data(device_connect, db)

    alert_text = (
        f"🚨 <b>Alert!</b>\n"
        f"📟 Device: <code>{device.device_id}</code>\n"
        f"Check as soon as possible."
    )

    results = []

    for p in phone_numbers:
        if p.tg_id:
            try:
                await pyro_app.send_message(chat_id=p.tg_id, text=alert_text)
                results.append({"tg_id": p.tg_id, "status": "sent"})
            except Exception as e:
                results.append({"tg_id": p.tg_id, "status": f"error: {str(e)}"})

    if user.tg_id:
        try:
            await pyro_app.send_message(chat_id=user.tg_id, text=alert_text)
            results.append({"tg_id": user.tg_id, "status": "sent (owner)"})
        except Exception as e:
            results.append({"tg_id": user.tg_id, "status": f"owner error: {str(e)}"})

    return {
        "status": "ok",
        "method": "pyrogram",
        "alerts": results,
        "phones": [p.phone for p in phone_numbers]
    }


# --- Send alert via Aiogram ---
@router.post("/send-alert-aiogram")
async def send_alert_aiogram(device_connect: str):
    db: Session = next(get_db())
    device, user, phone_numbers = get_alert_data(device_connect, db)

    alert_text = (
        f"🚨 <b>Alert!</b>\n"
        f"📟 Device: <code>{device.device_id}</code>\n"
        f"Check as soon as possible."
    )

    results = []

    for p in phone_numbers:
        if p.tg_id:
            try:
                await aiobot.send_message(chat_id=p.tg_id, text=alert_text)
                results.append({"tg_id": p.tg_id, "status": "sent"})
            except Exception as e:
                pass
    # Also send to the owner
    if user.tg_id:
        try:
            await aiobot.send_message(chat_id=user.tg_id, text=alert_text)
            results.append({"tg_id": user.tg_id, "status": "sent (owner)"})
        except Exception as e:
            results.append({"tg_id": user.tg_id, "status": f"owner error: {str(e)}"})

    return {
        "status": "ok",
        "method": "aiogram",
        "alerts": results,
        "phones": [p.phone for p in phone_numbers]
    }
