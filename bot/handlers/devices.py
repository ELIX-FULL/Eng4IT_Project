from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from bot.keyboards.reply import main_menu
from database import get_db
from database.models import User, Device, PhoneNumber

router = Router()


class DeviceStates(StatesGroup):
    view_devices = State()
    device_details = State()


class AddPhoneStates(StatesGroup):
    input_phone = State()
    input_tg = State()


def format_password(pw: str):
    if len(pw) <= 4:
        return '*' * len(pw)
    half = len(pw) // 2
    return pw[:half] + '*' * (len(pw) - half)

@router.message(F.text == "🆔 My ID")
async def show_my_id(msg: Message):
    await msg.answer(f"🆔 Your Telegram ID: <code>{msg.from_user.id}</code>", parse_mode="HTML")


@router.message(F.text == "📟 My Devices")
async def show_my_devices(msg: Message, state: FSMContext):
    db: Session = next(get_db())

    user = db.query(User).filter_by(tg_id=msg.from_user.id).first()
    if not user:
        await msg.answer("⚠️ You are not registered. Send /start")
        return

    devices = db.query(Device).filter_by(user_id=user.id).all()

    if not devices:
        await msg.answer("📭 You don't have any added devices yet.")
        return

    builder = InlineKeyboardBuilder()
    for dev in devices:
        builder.button(
            text=f"📟 {dev.device_id}",
            callback_data=f"device_{dev.id}"
        )
    builder.adjust(1)

    await msg.answer("📟 Your devices:", reply_markup=builder.as_markup())
    await state.set_state(DeviceStates.view_devices)


@router.callback_query(F.data.startswith("device_"))
async def show_device_details(callback: CallbackQuery, state: FSMContext):
    try:
        device_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Invalid ID", show_alert=True)
        return

    db: Session = next(get_db())
    device = db.query(Device).filter_by(id=device_id).first()

    if not device:
        await callback.message.answer("❌ Device not found.")
        await callback.answer()
        return

    password_masked = format_password(str(device.password))

    text = (
        f"📟 <b>Device ID:</b> <code>{device.device_id}</code>\n"
        f"🔐 <b>Password:</b> <code>{password_masked}</code>\n"
        f"🔗 <b>Connection Code:</b> <code>{device.device_connect}</code>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Phone Number", callback_data=f"addph_{device.id}")
    builder.button(text="📱 Show Phone Numbers", callback_data=f"showph_{device.id}")
    builder.button(text="📣 Add Alert Device", callback_data=f"addal_{device.id}")
    builder.button(text="⬅️ Back", callback_data="back_main")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
    await state.set_state(DeviceStates.device_details)


@router.callback_query(F.data == "back_main")
async def go_back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("🔙 Main menu", reply_markup=main_menu)
    await callback.answer()
    await state.clear()


@router.callback_query(F.data.startswith("addph_"))
async def start_adding_phone(callback: CallbackQuery, state: FSMContext):
    device_id = int(callback.data.split("_")[1])
    await state.update_data(device_id=device_id)
    await callback.message.answer("📱 Enter the phone number for emergency notifications:")
    await callback.answer()
    await state.set_state(AddPhoneStates.input_phone)


@router.message(AddPhoneStates.input_phone)
async def save_phone(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    data = await state.get_data()
    device_id = data.get("device_id")

    db: Session = next(get_db())
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        await msg.answer("❌ Device not found.")
        await state.clear()
        return

    await state.update_data(phone=phone, device_connect=device.device_connect)

    await msg.answer(
        "<b>ATTENTION:</b>\n\n"
        "📨 Ask the person who will receive the alerts to do the following:\n\n"
        "1. Go to <b>@..</b>\n"
        "2. Register if they are not already registered\n"
        "3. Click the <b>🆔 My ID</b> button and send you their Telegram ID\n\n"
        "After that, send that ID here.",
        parse_mode="HTML"
    )
    await state.set_state(AddPhoneStates.input_tg)


@router.message(AddPhoneStates.input_tg)
async def save_telegram_id(msg: Message, state: FSMContext):
    data = await state.get_data()
    db: Session = next(get_db())

    phone = data.get("phone")
    device_connect = data.get("device_connect")
    try:
        tg_id = int(msg.text)
    except ValueError:
        await msg.answer("❌ Invalid Telegram ID. Please enter a valid number.")
        return

    new_phone = PhoneNumber(phone=phone, device_connect=device_connect, tg_id=tg_id)
    db.add(new_phone)
    db.commit()

    await msg.answer(
        f"✅ Phone number <b>{phone}</b> added with Telegram ID <code>{tg_id}</code> to device <code>{device_connect}</code>.",
        reply_markup=main_menu,
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data.startswith("showph_"))
async def show_device_phones(callback: CallbackQuery):
    try:
        device_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Invalid ID", show_alert=True)
        return

    db: Session = next(get_db())
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        await callback.answer("❌ Device not found.", show_alert=True)
        return

    phone_numbers = db.query(PhoneNumber).filter_by(device_connect=device.device_connect).all()

    builder = InlineKeyboardBuilder()

    if phone_numbers:
        for phone in phone_numbers:
            builder.button(text=str(phone.phone), callback_data="noop")
    else:
        builder.button(text="No numbers added", callback_data="noop")

    builder.button(text="⬅️ Back", callback_data=f"device_{device_id}")
    builder.adjust(1)

    await callback.message.edit_text(
        f"📱 <b>Device Phone Number List:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()