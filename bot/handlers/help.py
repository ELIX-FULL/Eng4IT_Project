from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.reply import help_menu, main_menu

router = Router()


@router.message(F.text == "❓ Help")
async def help_handler(msg: Message):
    await msg.answer(
        "ℹ️ Select what you are interested in:",
        reply_markup=help_menu
    )


@router.message(F.text == "💳 Subscription Plans")
async def tariffs_handler(msg: Message):
    await msg.answer(
        "💳 <b>Available Subscription Plans:</b>\n\n"
        "🔹 <b>Basic</b> — free\n"
        "🔹 <b>Premium</b> — inquire with @...",
    )


@router.message(F.text == "➕ Register Device")
async def register_device_instruction(msg: Message):
    await msg.answer(
        "🛠 To register a device, go to the menu and select 'Add device', then enter the *Device ID* and *Password* printed on the bracelet.",
        parse_mode="Markdown"
    )


@router.message(F.text == "📩 @LaunchX_uz")
async def contact_support(msg: Message):
    await msg.answer("📬 Support: @...")


@router.message(F.text == "🔙 Back")
async def back_to_main(msg: Message):
    await msg.answer("🔙 Returning to the main menu.", reply_markup=main_menu)