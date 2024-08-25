from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.database.requests as rq
from utils.text_for_bots import *
from app.states import AdminStates


router_admin = Router()


@router_admin.message(Command(commands='admin'))
async def admin_menu(message: Message):
    await message.delete()
    if await rq.is_admin(message.from_user.id):
        await message.answer("🥷 Вы вошли в панель администрации.", reply_markup=await kb.admin_menu())
    else:
        await message.answer("❌ Вы не администратор.", reply_markup=await kb.main_menu())


@router_admin.callback_query(F.data == 'everyone')
async def everyone_message(callback: CallbackQuery, state: FSMContext):
    if await rq.is_admin(callback.from_user.id):
        await callback.message.answer("✍️ Введите сообщение для отправки всем пользователям:")
        await state.set_state(AdminStates.waiting_for_broadcast_message)
    else:
        await callback.message.answer("❌ Вы не администратор.", reply_markup=await kb.main_menu())


@router_admin.message(AdminStates.waiting_for_broadcast_message)
async def broadcast_message(message: Message, state: FSMContext):
    users = await rq.get_all_users()
    for user_id in users:
        try:
            await message.bot.send_message(user_id, message.text)
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    await state.clear()
    await message.answer("💌 Сообщение отправлено всем пользователям!", reply_markup=await kb.admin_menu())
   
    
@router_admin.callback_query(F.data == 'statistics')
async def statistics(callback: CallbackQuery):
    if await rq.is_admin(callback.from_user.id):
        user_count = await rq.get_user_count()
        await callback.message.answer(f"📊 В боте сейчас {user_count} пользователей.", reply_markup=await kb.admin_menu())
    else:
        await callback.message.answer("❌ Вы не администратор.", reply_markup=await kb.main_menu())