import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import router
from app.admin_handlers import router_admin
from app.database.models import async_main





async def main():
    load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.include_router(router_admin)
    await async_main()
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        print("Запуск бота")
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен.')