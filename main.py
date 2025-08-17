import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot.handlers import start, device, help, devices
from database import Base, engine
from sms.alert_sms import sms_router
from sms.alert_telegram import router as alert_router
from sms.app_api import router as app_router

load_dotenv()

# ==== FastAPI App ====
app = FastAPI(title="TapSafe API", docs_url='/api')

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5050",
    "http://127.0.0.1:5050",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sms_router, prefix="/sms")
app.include_router(alert_router, prefix="/telegram")
app.include_router(app_router, prefix="/app")
# app.include_router(whatsapp_router, prefix="/whatsapp")

# ==== Telegram Bot Setup ====
bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
dp.include_routers(start.router)
dp.include_router(device.router)
dp.include_router(help.router)
dp.include_router(devices.router)


# ==== Объединённый запуск FastAPI и Telegram ====
@app.on_event("startup")
async def on_startup():
    # Создание таблиц
    Base.metadata.create_all(bind=engine)
    # if not pyro_app.is_connected:
    #     await pyro_app.start()

    # Запуск бота в фоне
    asyncio.create_task(dp.start_polling(bot))

#
# @app.on_event("shutdown")
# async def shutdown_event():
#     if pyro_app.is_connected:
#         await pyro_app.stop()
