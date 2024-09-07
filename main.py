import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app import admin_handlers
from app import handlers
from app.database.models import async_main

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv(override=True)
    bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())


    dp.include_router(admin_handlers.router)
    dp.include_router(handlers.router)

    await async_main()

    try:
        logger.info("Запуск бота")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Бот выключен.')
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
