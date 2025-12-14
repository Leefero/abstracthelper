import logging
from telegram.ext import Application

from config.settings import settings
from bot.handlers.start_handler import start_handler


def setup_logging() -> None:
    """Настройка логирования"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.LOG_LEVEL)
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def create_application() -> Application:
    """Создание и настройка приложения бота"""
    
    if not settings.is_valid:
        logging.error("BOT_TOKEN не установлен. Добавьте его в .env файл")
        raise ValueError("BOT_TOKEN не установлен")
    
    # Создаем Application
    application = Application.builder().token(settings.BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(start_handler)
    
    logging.info(f"Бот {settings.BOT_NAME} инициализирован")
    return application


async def main() -> None:
    """Основная функция запуска бота"""
    
    setup_logging()
    
    try:
        app = create_application()
        
        logging.info("Бот запущен. Нажмите Ctrl+C для остановки...")
        
        # Запускаем бота
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        # Бесконечный цикл
        await app.idle()
        
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
