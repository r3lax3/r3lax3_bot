"""
Основной файл бота
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from redis.asyncio import Redis

from src.bot.config import config
from src.clients.backend_api import api_client
from src.i18n.translations import translations

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    logger.info("Starting R3lax3 Bot...")
    
    # Инициализация Redis
    redis = Redis.from_url(config.fsm_storage_url)
    storage = RedisStorage(redis=redis, prefix=config.redis_key_prefix)
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)
    
    # Регистрация middleware
    from src.bot.middleware import LanguageMiddleware, ErrorHandlingMiddleware, RateLimitMiddleware
    from src.storage.redis_helper import RedisHelper
    
    redis_helper = RedisHelper(redis)
    
    dp.message.middleware(LanguageMiddleware(redis_helper))
    dp.callback_query.middleware(LanguageMiddleware(redis_helper))
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())
    dp.message.middleware(RateLimitMiddleware(redis_helper))
    dp.callback_query.middleware(RateLimitMiddleware(redis_helper))
    
    # Регистрация роутеров
    from src.routers import user, subscriptions, payments, history
    dp.include_router(user.router)
    dp.include_router(subscriptions.router)
    dp.include_router(payments.router)
    dp.include_router(history.router)
    
    # TODO: Добавить остальные роутеры
    # from src.routers import admin, subscriptions, payments, history
    # dp.include_router(admin.router)
    # dp.include_router(subscriptions.router)
    # dp.include_router(payments.router)
    # dp.include_router(history.router)
    
    # Обработчик ошибок
    @dp.errors()
    async def errors_handler(update, exception):
        logger.error(f"Exception while handling {update}: {exception}")
    
    try:
        logger.info("Bot started successfully")
        
        if config.use_long_polling:
            # Запуск long polling
            await dp.start_polling(bot)
        else:
            # Запуск webhook (будет добавлено позже)
            logger.info("Webhook mode not implemented yet")
            return
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()
        await redis.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
