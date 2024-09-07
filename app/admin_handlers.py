import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.database.requests as rq
from utils.text_for_bots import *
from app.states import AdminStates

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command(commands='admin'))
async def admin_menu(message: Message):
    """
    Обработка команды /admin. Проверяет, является ли пользователь администратором и отправляет соответствующее сообщение.
    """
    await message.delete()
    try:
        if await rq.is_admin(message.from_user.id):
            await message.answer("🥷 Вы вошли в панель администрации.", reply_markup=await kb.admin_menu())
        else:
            await message.answer("❌ Вы не администратор.", reply_markup=await kb.main_menu())
    except Exception as e:
        logger.error(f"Ошибка проверки администратора для пользователя {message.from_user.id}: {e}")

@router.callback_query(F.data == 'everyone')
async def everyone_message(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс отправки сообщения всем пользователям. Запрашивает сообщение от администратора.
    """
    await callback.answer()
    try:
        if await rq.is_admin(callback.from_user.id):
            await callback.message.answer("✍️ Введите сообщение для отправки всем пользователям:")
            await state.set_state(AdminStates.waiting_for_broadcast_message)
        else:
            await callback.message.answer("❌ Вы не администратор.", reply_markup=await kb.main_menu())
    except Exception as e:
        logger.error(f"Ошибка при проверке администратора для пользователя {callback.from_user.id}: {e}")

@router.message(AdminStates.waiting_for_broadcast_message)
async def broadcast_message(message: Message, state: FSMContext):
    """
    Отправляет полученное сообщение всем пользователям.
    """
    try:
        users = await rq.get_all_users()
        for user_id in users:
            try:
                await message.bot.send_message(user_id, message.text)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        await message.answer("💌 Сообщение отправлено всем пользователям!", reply_markup=await kb.admin_menu())
    except Exception as e:
        logger.error(f"Ошибка при рассылке сообщения: {e}")
    finally:
        await state.clear()  # Очистка состояния после завершения рассылки

@router.callback_query(F.data == 'statistics')
async def statistics(callback: CallbackQuery):
    """
    Отправляет статистику о количестве пользователей бота.
    """
    await callback.answer()
    try:
        if await rq.is_admin(callback.from_user.id):
            user_count = await rq.get_user_count()
            await callback.message.answer(f"📊 В боте сейчас {user_count} пользователей.", reply_markup=await kb.admin_menu())
        else:
            await callback.message.answer("❌ Вы не администратор.", reply_markup=await kb.main_menu())
    except Exception as e:
        logger.error(f"Ошибка при получении статистики для пользователя {callback.from_user.id}: {e}")
