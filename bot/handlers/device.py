import os

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from bot.keyboards.reply import main_menu
from database import get_db
from database.models import Device
from database.models import User

router = Router()


# States
class AddDevice(StatesGroup):
    device_id = State()
    password = State()


@router.message(F.text == "📲 Register Device")
async def start_add_device(msg: Message, state: FSMContext):
    await msg.answer("📟 Enter the Device ID of the device:")
    await state.set_state(AddDevice.device_id)


@router.message(AddDevice.device_id)
async def enter_device_id(msg: Message, state: FSMContext):
    await state.update_data(device_id=msg.text.strip())
    await msg.answer("🔑 Enter the device password:")
    await state.set_state(AddDevice.password)


@router.message(AddDevice.password)
async def verify_and_add_device(msg: Message, state: FSMContext):
    data = await state.get_data()
    device_id = data.get("device_id")
    password = msg.text.strip()
    user_tg_id = msg.from_user.id

    db: Session = next(get_db())

    # Get the current user
    user = db.query(User).filter_by(tg_id=user_tg_id).first()
    if not user:
        await msg.answer("❌ You are not registered.")
        await state.clear()
        return

    # Find the device
    device = db.query(Device).filter_by(device_id=device_id, password=password).first()

    if not device:
        await msg.answer("❌ Device not found. Check the ID and password.")
        await state.clear()
        return

    if device.user_id is not None:
        await msg.answer("⚠️ This device is already linked to another user.")
        await state.clear()
        return

    # Link the device
    device.user_id = user.id

    db.commit()

    await msg.answer(
        f"✅ Device <code>{device.device_id}</code> successfully added!\n"
        f"You can now manage it.",
        reply_markup=main_menu
    )
    await state.clear()


PREMIUM_PRICE = LabeledPrice(label="💎 Premium Plan", amount=500000)  # 5000 сум


@router.message(F.text == "💳 Subscription Plan")
async def handle_tariff(msg: Message):
    db: Session = next(get_db())

    user = db.query(User).filter_by(tg_id=msg.from_user.id).first()
    if not user:
        await msg.answer("❌ You are not registered.")
        return

    if user.subscription == "Premium":
        text = (
            f"👤 <b>Your Profile</b>\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"📛 <b>Name:</b> {user.name or '—'}\n"
            f"💼 <b>Subscription Plan:</b> <code>{user.subscription}</code>\n"
        )
        await msg.answer(text, parse_mode="HTML")
    else:
        token = os.getenv("CLICK_PAY_TOKEN")
        if not token:
            await msg.answer("❌ Error: Payment token not found.")
            return

        await msg.answer_invoice(
            title="💎 Premium Plan",
            description="Grants access to SMS sending, calls, and other features.",
            provider_token=token,
            currency="UZS",
            prices=[PREMIUM_PRICE],
            start_parameter="premium_sub",
            payload="premium_payment"
        )


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def payment_success(msg: Message):
    if msg.successful_payment.invoice_payload != "premium_payment":
        return

    db: Session = next(get_db())

    user = db.query(User).filter_by(tg_id=msg.from_user.id).first()
    if not user:
        await msg.answer("❌ User not found.")
        return

    user.subscription = "Premium"
    db.commit()

    await msg.answer("✅ Congratulations! You have successfully purchased the Premium plan.\nNow you have access to extended functionality.")


# Product data
PRODUCT = {
    "photo": "url",  # Insert the device image URL
    "name": "Device X",
    "price": 10000
}

# ⚠️ ATTENTION: This is temporary storage. Data will be lost when the bot restarts.
# For production, use a database or FSMContext.
user_carts = {}  # user_id -> quantity


# =========================================================
# 🛠️ Helper functions for keyboards
# =========================================================

def get_product_keyboard(count: int, in_cart: bool) -> InlineKeyboardMarkup:
    """Creates a keyboard for the product page."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="-", callback_data="decrease"),
        InlineKeyboardButton(text=str(count), callback_data="count"),
        InlineKeyboardButton(text="+", callback_data="increase"),
    )
    builder.row(InlineKeyboardButton(text="Add to Cart", callback_data="add_to_cart"))
    if in_cart:
        builder.row(InlineKeyboardButton(text="Cart", callback_data="cart"))
    return builder.as_markup()


def get_cart_keyboard() -> InlineKeyboardMarkup:
    """Creates a keyboard for the cart page."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Clear Cart", callback_data="clear_cart"),
        InlineKeyboardButton(text="Proceed to Checkout", callback_data="checkout")
    )
    return builder.as_markup()

# =========================================================
# 🛒 Handlers for product purchase
# =========================================================

@router.message(F.text == "🛍 Buy Device")
async def buy_device(message: Message):
    """Handler for the 'Buy Device' button."""
    count = 1
    in_cart = message.from_user.id in user_carts and user_carts[message.from_user.id] > 0
    keyboard = get_product_keyboard(count, in_cart)

    await message.answer_photo(
        photo=PRODUCT["photo"],
        caption=f"{PRODUCT['name']}\nPrice: {PRODUCT['price']} sum",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "increase")
async def increase_count(call: CallbackQuery):
    """Increases the product quantity."""
    count = 1
    kb = call.message.reply_markup.inline_keyboard
    try:
        count_text = kb[0][1].text
        count = int(count_text)
    except (IndexError, ValueError):
        pass

    count += 1
    in_cart = call.from_user.id in user_carts and user_carts[call.from_user.id] > 0
    keyboard = get_product_keyboard(count, in_cart)
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data == "decrease")
async def decrease_count(call: CallbackQuery):
    """Decreases the product quantity and prevents error when count = 1."""
    count = 1
    kb = call.message.reply_markup.inline_keyboard
    try:
        count_text = kb[0][1].text
        count = int(count_text)
    except (IndexError, ValueError):
        pass

    if count > 1:
        count -= 1
        in_cart = call.from_user.id in user_carts and user_carts[call.from_user.id] > 0
        keyboard = get_product_keyboard(count, in_cart)
        await call.message.edit_reply_markup(reply_markup=keyboard)
    else:
        # Send a notification message so the user knows why nothing happened
        await call.answer("Quantity cannot be less than 1.", show_alert=True)

    # Always answer the callback
    await call.answer()


@router.callback_query(F.data == "add_to_cart")
async def add_to_cart(call: CallbackQuery):
    """Adds the product to the cart."""
    kb = call.message.reply_markup.inline_keyboard
    count = 1
    try:
        count_text = kb[0][1].text
        count = int(count_text)
    except (IndexError, ValueError):
        pass

    if count < 1:
        await call.answer("Quantity cannot be less than 1.", show_alert=True)
        return

    user_id = call.from_user.id
    was_cart_empty = user_id not in user_carts or user_carts[user_id] == 0

    user_carts[user_id] = user_carts.get(user_id, 0) + count

    if was_cart_empty:
        # Update the keyboard only if the cart was empty
        keyboard = get_product_keyboard(count, True)
        await call.message.edit_reply_markup(reply_markup=keyboard)
        await call.answer(f"Added to cart: {count} pc(s).")
    else:
        # Just answer the callback without changing the message
        await call.answer(f"Added to cart: {count} pc(s). (total {user_carts[user_id]} pc(s))")

@router.callback_query(F.data == "cart")
async def show_cart(call: CallbackQuery):
    """Shows the cart content."""
    count = user_carts.get(call.from_user.id, 0)
    if count == 0:
        await call.answer("Your cart is empty.", show_alert=True)
        return

    total_price = count * PRODUCT["price"]
    text = (f"Your cart:\n"
            f"{PRODUCT['name']} — {count} pc(s).\n"
            f"Total price: {total_price} sum")
    keyboard = get_cart_keyboard()
    await call.message.answer(text, reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery):
    """Handler for the 'Proceed to Checkout' button."""
    count = user_carts.get(call.from_user.id, 0)
    if count == 0:
        await call.answer("Your cart is empty.", show_alert=True)
        return

    user_carts[call.from_user.id] = 0
    await call.message.answer("Thank you for your order! We will contact you shortly.")
    await call.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    """Handler for the 'Clear Cart' button."""
    user_id = call.from_user.id
    if user_id in user_carts:
        del user_carts[user_id]
        await call.message.answer("🗑️ Your cart has been cleared.")
    else:
        await call.answer("Your cart is already empty.", show_alert=True)

    # Update the keyboard if necessary
    await call.message.delete() # Delete the old message with the cart
    await call.answer()