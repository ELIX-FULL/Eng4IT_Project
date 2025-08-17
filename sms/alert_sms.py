from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import httpx

from database import get_db
from database.models import PhoneNumber

sms_router = APIRouter(tags=["SMS"])

BASE_URL = "https://notify.eskiz.uz/api"
ESKIZ_EMAIL = "email"  # замените на ваш email
ESKIZ_PASSWORD = "password"  # замените на ваш пароль


async def get_eskiz_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data={"email": "email eskiz", "password": "password eskiz"}
        )
        print(response.status_code)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль Eskiz")
        response.raise_for_status()
        return response.json()["data"]["token"]


async def eskiz_send_sms(token: str, phone: str, message: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "mobile_phone": phone,
            "message": message,
            "from": "4546"
        }
        response = await client.post(f"{BASE_URL}/message/sms/send", data=data, headers=headers)
        return response.status_code, response.json()


@sms_router.post("/send-sms")
async def send_alert_sms_to_device_numbers(
    device_connect: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    token = await get_eskiz_token()

    phones = db.query(PhoneNumber).filter_by(device_connect=device_connect).all()
    if not phones:
        raise HTTPException(status_code=404, detail="Номера не найдены для указанного device_connect")

    results = []

    for phone in phones:
        status_code, response_data = await eskiz_send_sms(token, "number", message)
        results.append({
            "phone": phone.phone,
            "status": status_code,
            "response": response_data
        })

    return {
        "sent": len(results),
        "details": results
    }
