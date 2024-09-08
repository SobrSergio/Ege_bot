import logging
import asyncio
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError

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
            await callback.message.edit_text("✍️ Введите сообщение для отправки всем пользователям:")
            await state.set_state(AdminStates.waiting_for_broadcast_message)
        else:
            await callback.message.edit_text("❌ Вы не администратор.", reply_markup=await kb.main_menu())
    except Exception as e:
        logger.error(f"Ошибка при проверке администратора для пользователя {callback.from_user.id}: {e}")

@router.message(AdminStates.waiting_for_broadcast_message)
async def broadcast_message(message: Message, state: FSMContext):
    """
    Отправляет полученное сообщение всем пользователям.
    """
    try:
        users = await rq.get_all_users()  # Получаем список всех пользователей

        async def send_message(user_id):
            try:
                await message.bot.send_message(user_id, message.text)
            except TelegramForbiddenError as e:
                if "bot was blocked by the user" in str(e):
                    logger.warning(f"Бот заблокирован пользователем {user_id}")
                elif "user is deactivated" in str(e):
                    logger.warning(f"Пользователь {user_id} деактивирован")
                
                await rq.delete_user_by_tg_id(user_id)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

        # Параллельная отправка сообщений
        await asyncio.gather(*[send_message(user_id) for user_id in users])

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
            await callback.message.edit_text(f"📊 В боте сейчас {user_count} пользователей.", reply_markup=await kb.admin_menu())
        else:
            await callback.message.edit_text("❌ Вы не администратор.", reply_markup=await kb.main_menu())
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Ошибка при получении статистики для пользователя {callback.from_user.id}: {e}")
