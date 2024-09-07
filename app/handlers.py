from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import logging

import app.keyboards as kb
import app.database.requests as rq
from utils.text_for_bots import *
from app.states import TestStates
from utils.data import words, options_main

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

router = Router()
# Хранение ID сообщений пользователя
user_message_ids = {}

async def send_or_edit_message(bot, user_id, user_message_id, text, reply_markup):
    """
    Отправка нового сообщения или редактирование существующего.
    """
    try:
        if user_message_id:
            # Редактирование существующего сообщения
            await bot.edit_message_text(
                chat_id=user_id, 
                message_id=user_message_id, 
                text=text, 
                reply_markup=reply_markup, 
                parse_mode=ParseMode.HTML
            )
        else:
            # Отправка нового сообщения и сохранение его ID
            sent_message = await bot.send_message(
                user_id, 
                text, 
                reply_markup=reply_markup, 
                parse_mode=ParseMode.HTML
            )
            user_message_ids[user_id] = sent_message.message_id
    except Exception as e:
        # Логирование ошибок
        logging.error(f"Error editing or sending message: {e}")
    
@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработка команды /start. Отправляет стартовое сообщение.
    """
    user_id = message.from_user.id
    create = await rq.set_user(user_id, message.from_user.full_name)
    formatted_message = start_messages.format(name=message.from_user.full_name) if create else "✍️ <b>Егэ русский язык</b>"

    sent_message = await message.bot.send_message(
        chat_id=user_id,
        text=formatted_message,
        reply_markup=await kb.main_menu(),
        parse_mode=ParseMode.HTML
    )
    user_message_ids[user_id] = sent_message.message_id  

    await message.delete() 
    
@router.message(Command(commands='help'))
async def cmd_help(message: Message):
    """
    Обработка команды /help. Отправляет сообщение с помощью.
    """
    await message.delete()
    await message.answer(f'{help_messages}')

@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    """
    Функция отправки на меню категорий (Ударение, Словарные слова и т.д.)
    """
    await callback.answer()
    category_name = callback.data.split('_')[1]
    text = f"{options_main.get(category_name)}\n\nКоличество ошибок: {await rq.get_user_mistake_count(callback.from_user.id, category_name)}"

    await send_or_edit_message(callback.message.bot, callback.from_user.id, user_message_ids.get(callback.from_user.id), text, await kb.button_categories(category_name))

@router.callback_query(F.data == 'go_main')
async def go_main(callback: CallbackQuery):
    """
    Функция отправки на главное меню
    """
    await send_or_edit_message(callback.message.bot, callback.from_user.id, user_message_ids.get(callback.from_user.id), "✍️ <b>Егэ русский язык</b>", await kb.main_menu())
    await callback.answer()

@router.callback_query(F.data.startswith('start_'))
async def start_test(callback: CallbackQuery, state: FSMContext):
    """
    Функция для запуска тестирования на основе выбранной категории.
    """
    try:
        category = callback.data.split('_')[1]
        
        # Получение данных для теста
        words1, words_dop = words.get(category, ([], [])) 
        
        if not words1 or not words_dop:
            await callback.message.answer(
                "Тест не может быть запущен, так как нет данных."
            )
            return

        # Обновление состояния
        await state.update_data(
            category=category, 
            used_words=[], 
            current_pair=[], 
            words=words1,
            words_dop=words_dop
        )

        await state.set_state(TestStates.answering_question)

        # Отправка следующего вопроса
        await send_next_question(callback.message, state)
    
    except Exception as e:
        # Логирование ошибки
        logging.error(f"Ошибка при запуске теста: {e}")
        await callback.message.answer(
            "⚠️ Произошла ошибка при запуске теста. Пожалуйста, попробуйте снова позже."
        )

@router.callback_query(F.data.startswith('error_'))
async def start_error_correction(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для начала исправления ошибок.
    """
    try:
        category = callback.data.split('_')[1]
        
        # Получение ошибок пользователя
        errors = await rq.get_user_mistakes(callback.from_user.id, category)

        # Проверка наличия ошибок
        if not errors:
            await callback.message.edit_text(
                "👍 У вас нет ошибок для проработки.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"close_{category}")]
                    ]
                )
            )
            return

        # Подготовка данных для проработки ошибок
        all_paronyms_error = [error.get('all_paronyms', []) for error in errors] if category == 'paronyms' else []
        words_error = [error.get('words', []) for error in errors]
        words_dop_error = [error.get('words_dop', []) for error in errors]

        # Обновление состояния
        await state.update_data(
            category=category,
            used_words=[],
            current_pair=[],
            words=words_error,
            words_dop=words_dop_error,
            all_paronyms=all_paronyms_error,
            is_error_correction=True
        )

        await state.set_state(TestStates.answering_question)

        # Отправка следующего вопроса
        await send_next_question(callback.message, state)

    except Exception as e:
        # Логирование ошибки
        logging.error(f"Ошибка в start_error_correction: {e}")
        await callback.message.edit_text(
            "⚠️ Произошла ошибка при начале исправления ошибок.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"close_{category}")]
                ]
            )
        )

async def send_next_question(message: Message, state: FSMContext, result_message: str = ''):
    """
    Создание следующего вопроса.
    """
    try:
        data = await state.get_data()
        category_name = data.get('category')

        # Проверяем, завершены ли слова
        if not data.get('words') or not data.get('words_dop'):
            finish_message = (
                "💫 Проработка ошибок завершена!" 
                if data.get('is_error_correction') 
                else "✅ Тест завершен, все слова пройдены!"
            )
            text = f"{options_main.get(category_name, '')}\n\n{finish_message}"
            await message.edit_text(text, reply_markup=await kb.button_categories(category_name))
            await state.clear()
            return

        # Выбор пары слов
        word_pair = random.choice(list(zip(data['words'], data['words_dop'])))
        words, words_dop = word_pair
        
        if category_name == 'paronyms':
            if not data.get('is_error_correction'):
                data['words'].remove(words)
                data['words_dop'].remove(words_dop)
                correct_paronym = random.choice(words)
                correct_explanation = words_dop[words.index(correct_paronym)]
            else:
                word_index = data['words'].index(words)
                correct_paronym = words
                words = data['all_paronyms'][word_index]
                correct_explanation = words_dop

            data['current_pair'] = correct_paronym
            data['paronyms'] = words
            data['correct_explanation'] = correct_explanation

            # Создание кнопок ответа
            answer_buttons = [
                InlineKeyboardButton(text=paronym, callback_data=f"paronym_{paronym}") for paronym in words
            ]
            answer_buttons.append(InlineKeyboardButton(text="🔙 Завершить", callback_data=f"close_{data['category']}"))

            keyboard = InlineKeyboardMarkup(inline_keyboard=[[button] for button in answer_buttons])
            result_message = f"{result_message}\n\nВыберите правильное слово:\n\n{correct_explanation}" if result_message else f"Выберите правильное слово:\n\n{correct_explanation}"

        else:
            data['current_pair'] = (words, words_dop)

            # Создание кнопок ответа
            answer_buttons = [
                InlineKeyboardButton(text=word, callback_data="correct" if word == words else "wrong")
                for word in random.sample([words, words_dop], 2)
            ]
            answer_buttons.append(InlineKeyboardButton(text="🔙 Завершить", callback_data=f"close_{data['category']}"))

            keyboard = InlineKeyboardMarkup(inline_keyboard=[answer_buttons])
            result_message = "Выберите верный ответ: " if not result_message else result_message

        await state.update_data(data)
        await message.edit_text(result_message, reply_markup=keyboard)

    except Exception as e:
        # Логирование ошибки
        logging.error(f"Ошибка в send_next_question: {e}")
        result_message = "⚠️ Произошла ошибка при создании следующего вопроса."
        await message.edit_text(result_message)

@router.callback_query(F.data.in_(['correct', 'wrong']))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает ответы пользователя на вопросы.
    Удаляет или сохраняет ошибку в зависимости от правильности ответа.
    """
    data = await state.get_data()
    correct_word, wrong_word = data.get('current_pair', (None, None))

    try:
        if callback.data == "correct":
            if data.get('is_error_correction'):
                # Удаляем слово и его объяснение из данных и базы данных
                data['words'].remove(correct_word)
                data['words_dop'].remove(wrong_word)
                await rq.remove_user_mistake(callback.from_user.id, data['category'], correct_word)
            result_message = "✅ Верно!"
        else:
            result_message = f"❌ Неверно, правильный ответ: {correct_word}"
            if not data.get('is_error_correction'):
                # Сохраняем ошибку в базе данных
                await rq.save_user_mistake(
                    callback.from_user.id, 
                    data['category'], 
                    wrong_word=wrong_word,
                    correct_word=correct_word
                )
    except Exception as e:
        # Обработка ошибок, например, логирование
        result_message = "⚠️ Произошла ошибка при обработке ответа."

    await send_next_question(callback.message, state, result_message)

@router.callback_query(F.data.startswith('paronym_'))
async def handle_paronyms_answer(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает ответы пользователя на вопросы по паронимам.
    """
    try:
        data = await state.get_data()

        chosen_paronym = callback.data.split('_')[1]
        correct_paronym = data.get('current_pair')
        correct_explanation = data.get('correct_explanation')

        if chosen_paronym == correct_paronym:
            if data.get('is_error_correction'):
                data['words'].remove(correct_paronym)
                data['words_dop'].remove(correct_explanation)
                data['all_paronyms'].remove(data.get('paronyms'))

                await rq.remove_user_mistake(callback.from_user.id, data['category'], paronym_wrong=correct_paronym)
            result_message = "✅ Верно!"
        else:
            result_message = f"❌ Неверно, правильный ответ: {correct_paronym}"
            if not data.get('is_error_correction'):
                await rq.save_user_mistake(
                    callback.from_user.id, 
                    data['category'], 
                    wrong_word=correct_paronym,
                    all_paronyms=data.get('paronyms'),
                    explanation=correct_explanation
                )

        await send_next_question(callback.message, state, result_message)
    except Exception as e:
        # Логирование ошибки
        logging.error(f"Ошибка в handle_paronyms_answer: {e}")
        result_message = "⚠️ Произошла ошибка при обработке ответа."

        await send_next_question(callback.message, state, result_message)

@router.callback_query(F.data.startswith('close_'))
async def close_test(callback: CallbackQuery, state: FSMContext):
    """
    Закрытие теста и возврат к главному меню
    """
    category_name = callback.data.split('_')[1]
    text = options_main.get(category_name, "")
    user_id = callback.from_user.id
    mistake_count = await rq.get_user_mistake_count(user_id, category_name)
    text = f"{text}\n\n📚 Тест завершен!\n\nКоличество ошибок: {mistake_count}"
    
    await state.clear()
    await callback.message.edit_text(text=text, reply_markup=await kb.button_categories(category_name))