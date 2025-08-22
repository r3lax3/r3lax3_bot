"""
Admin entry commands and state setup
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.states.admin import AdminSG
from src.keyboards.inline import get_admin_main_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("admin"))
async def admin_entry(message: Message, is_admin: bool, language: str, state: FSMContext):
    if not is_admin:
        return
    await message.answer("Admin Panel" if language == "en" else "Админ-панель", reply_markup=get_admin_main_keyboard(language))
    await state.set_state(AdminSG.STATE_ADMIN_MAIN)


