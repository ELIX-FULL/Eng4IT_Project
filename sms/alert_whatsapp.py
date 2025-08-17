import urllib.parse

import httpx
from fastapi import APIRouter, Body

whatsapp_router = APIRouter(tags=["WHATSAPP"])

CALLMEBOT_APIKEY = "callme api key"  # замените на реальный ключ, полученный от бота


async def send_whatsapp(message: str):
    """
    Отправка WhatsApp сообщения через CallMeBot API
    """

    encoded_message = urllib.parse.quote(message)
    url = (
        f"https://api.callmebot.com/whatsapp.php?"
        f"phone=+number&text={encoded_message}&apikey=Apikey"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=15)
        return response.status_code, response.text


@whatsapp_router.post("/send-whatsapp")
async def send_alert_whatsapp_to_device_numbers(message: str = Body(..., embed=True)):
    """
    Отправляет сообщение в WhatsApp всем номерам,
    которые связаны с указанным device_connect
    """

    results = []
    status_code, response_text = await send_whatsapp(message)
    results.append({
        "status": status_code,
        "response": response_text
    })


    return {
        "sent": len(results),
        "details": results
    }
