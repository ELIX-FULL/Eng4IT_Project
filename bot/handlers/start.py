from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from database import get_db
from database.models import User
from bot.keyboards.reply import main_menu

router = Router()

# Registration states
class Registration(StatesGroup):
    name = State()


@router.message(F.text == "/start")
async def start_registration(msg: Message, state: FSMContext):
    db: Session = next(get_db())

    # Check: user already exists
    existing_user = db.query(User).filter_by(tg_id=msg.from_user.id).first()
    if existing_user:
        await msg.answer(
            f"👋 Welcome back, {existing_user.name}!",
            reply_markup=main_menu
        )
        await state.clear()
        return

    await msg.answer("👋 Welcome!\n\nPlease enter your name:")
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def complete_registration(msg: Message, state: FSMContext):
    name = msg.text.strip()
    db: Session = next(get_db())

    # Re-check
    existing_user = db.query(User).filter_by(tg_id=msg.from_user.id).first()
    if existing_user:
        await msg.answer("⚠️ You are already registered.", reply_markup=main_menu)
        await state.clear()
        return

    # Create new user
    new_user = User(
        tg_id=msg.from_user.id,
        name=name,
        subscription='basic'
    )
    db.add(new_user)
    db.commit()

    await msg.answer(
        f"✅ Registration complete, {name}!\n\n"
        f"You can now add a device manually through the menu.",
        reply_markup=main_menu
    )
    await state.clear()