from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.database.requests as rq
from utils.text_for_bots import *
from app.states import TestStates, AdminStates

import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.data import words, options_main





router = Router()
user_message_ids = {}

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    create = await rq.set_user(user_id, message.from_user.full_name)
    formatted_message = start_messages.format(name=message.from_user.full_name) if create else "✍️ <b>Егэ русский язык</b>"

    # Получаем ID последнего сообщения пользователя, если оно есть
    user_message_id = user_message_ids.get(user_id)
    
    if user_message_id:
        try:
            # Пытаемся обновить текст существующего сообщения
            await message.bot.edit_message_text(
                chat_id=user_id,
                message_id=user_message_id,
                text=formatted_message,
                reply_markup=await kb.main_menu(),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            # Если не удалось обновить сообщение, отправляем новое
            sent_message = await message.answer(formatted_message, reply_markup=await kb.main_menu())
            user_message_ids[user_id] = sent_message.message_id
    else:
        # Если у пользователя нет сохраненного сообщения, отправляем новое
        sent_message = await message.answer(formatted_message, reply_markup=await kb.main_menu())
        user_message_ids[user_id] = sent_message.message_id

    # Удаляем команду /start
    await message.delete()


@router.message(Command(commands='help'))
async def cmd_help(message: Message):
    await message.delete()
    await message.answer(f'{help_messages}')


@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    await callback.answer()
    category_name = callback.data.split('_')[1]
    text = options_main.get(category_name)
    
    user_id = callback.from_user.id
    mistake_count = await rq.get_user_mistake_count(user_id, category_name)
    text = f"{text}\n\nКоличество ошибок: {mistake_count}"
    
    # Изменяем сообщение, если его ID есть в хранилище
    user_message_id = user_message_ids.get(callback.from_user.id)
    if user_message_id:
        try:
            await callback.message.edit_text(
                f'{text}',
                reply_markup=await kb.button_categories(category_name),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error editing message: {e}")
    else:
        await callback.message.answer(f'{text}', reply_markup=await kb.button_categories(category_name))


@router.callback_query(F.data == 'go_main')
async def go_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_message_id = user_message_ids.get(user_id)
    
    if user_message_id:
        try:
            await callback.message.edit_text(
                "✍️ <b>Егэ русский язык</b>",
                reply_markup=await kb.main_menu(),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error editing message: {e}")
    else:
        sent_message = await callback.message.answer(
            "✍️ <b>Егэ русский язык</b>",
            reply_markup=await kb.main_menu(),
            parse_mode=ParseMode.HTML
        )
        user_message_ids[user_id] = sent_message.message_id

    await callback.answer()


@router.callback_query(F.data.startswith('start_'))
async def start_test(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[1]
    correct_words, wrong_words = words[category]
    await state.update_data(category=category, used_words=[], current_pair=[], \
        correct_words=correct_words, wrong_words=wrong_words)

    await state.set_state(TestStates.answering_question)
    await send_next_question(callback.message, state, result_message='')


@router.callback_query(F.data.startswith('error_'))
async def start_error_correction(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[1]
    errors = await rq.get_user_mistakes(callback.from_user.id, category)

    if not errors:
        await callback.message.edit_text("👍 У вас нет ошибок для проработки.", reply_markup=await kb.button_categories(category))
        return

    correct_words = [error['correct_word'] for error in errors]
    wrong_words = [error['wrong_word'] for error in errors]

    await state.update_data(category=category, used_words=[], current_pair=[], \
        correct_words=correct_words, wrong_words=wrong_words, is_error_correction=True)

    await state.set_state(TestStates.answering_question)
    await send_next_question(callback.message, state, result_message='')


async def send_next_question(message, state: FSMContext, result_message: str):
    data = await state.get_data()
    if not data['correct_words']:
        category_name = data['category']
        text = options_main.get(category_name)
        finish_message = "💫 Проработка ошибок завершена!" if data.get('is_error_correction') else "✅ Тест завершен, все слова пройдены!"
        text = f"{text}\n\n{finish_message}"
        await message.edit_text(text, reply_markup=await kb.button_categories(category_name))
        await state.clear()
        return

    word_pair = random.choice(list(zip(data['correct_words'], data['wrong_words'])))
    correct_word, wrong_word = word_pair
    
    if not data.get('is_error_correction'):
        data['correct_words'].remove(correct_word)
        data['wrong_words'].remove(wrong_word)

    data['current_pair'] = (correct_word, wrong_word)
    await state.update_data(data)

    answer_buttons = [
        InlineKeyboardButton(text=correct_word, callback_data="correct"),
        InlineKeyboardButton(text=wrong_word, callback_data="wrong"),
    ]
    random.shuffle(answer_buttons)
    answer_buttons.append(InlineKeyboardButton(text="🔙 Завершить", callback_data=f"close_{data['category']}"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        answer_buttons[:2],
        answer_buttons[2:]
    ])
    
    if result_message == '':
        result_message = "Выберите верный ответ: "
    await message.edit_text(result_message, reply_markup=keyboard)


@router.callback_query(F.data.in_(['correct', 'wrong']))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    correct_word, wrong_word = data['current_pair']

    if callback.data == "correct":
        if data.get('is_error_correction'):
            data['correct_words'].remove(correct_word)
            data['wrong_words'].remove(wrong_word)
            await rq.remove_user_mistake(callback.from_user.id, data['category'], correct_word)
        result_message = "✅ Верно!"
    else:
        result_message = f"❌ Неверно, правильный ответ: {correct_word}"
        if not data.get('is_error_correction'):
            await rq.save_user_mistake(callback.from_user.id, data['category'], correct_word, wrong_word)
        
    await send_next_question(callback.message, state, result_message)


@router.callback_query(F.data.startswith('close_'))
async def close_test(callback: CallbackQuery, state: FSMContext):
    
    category_name = callback.data.split('_')[1]
    text = options_main.get(category_name)
    user_id = callback.from_user.id
    mistake_count = await rq.get_user_mistake_count(user_id, category_name)
    text = f"{text}\n\n📚 Тест завершен!"
    text = f"{text}\n\nКоличество ошибок: {mistake_count}"
    
    await state.clear()
    await callback.message.edit_text(text=text, reply_markup=await kb.button_categories(category_name))