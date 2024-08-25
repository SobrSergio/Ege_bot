from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton





async def main_menu():
    keyboard = [
        [InlineKeyboardButton(text='📢 Ударения', callback_data=f'category_accents')],
        [InlineKeyboardButton(text='✏️ Словарные слова', callback_data=f'category_dictionary'), 
         InlineKeyboardButton(text='📚 Морф. нормы', callback_data=f'category_norms')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard )


async def button_categories(callback_data):
    keyboard = [
        [InlineKeyboardButton(text='🖍️ Ошибки', callback_data=f'error_{callback_data}'),
        InlineKeyboardButton(text='🚀 Начать', callback_data=f'start_{callback_data}')], 
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data=f"go_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def admin_menu():
    keyboard = [
        [InlineKeyboardButton(text='💬 Отправить @everyone сообщение', callback_data=f'everyone')],
        [InlineKeyboardButton(text='📊 Статистика', callback_data=f'statistics')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)