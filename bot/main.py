import logging
from telegram.ext import Application

from config.settings import settings
from data.dataset_manager import dataset_manager
from bot.conversation.handlers import setup_conversation_handler  # <-- НОВОЕ


def setup_logging() -> None:
    """Настройка логирования"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.LOG_LEVEL)
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def load_dataset() -> bool:
    """Загрузка датасета мер поддержки"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Начало загрузки датасета мер поддержки...")
        
        # Конфигурируем менеджер в зависимости от источника данных
        dataset_manager.data_source = settings.DATA_SOURCE
        
        # Загружаем датасет
        if settings.DATA_SOURCE == 'google_sheets':
            success = dataset_manager.load_dataset(
                sheet_id=settings.GOOGLE_SHEET_ID,
                sheet_name=settings.GOOGLE_SHEET_NAME
            )
        else:  # local
            success = dataset_manager.load_dataset(
                filepath=settings.LOCAL_DATASET_PATH
            )
        
        if success:
            info = dataset_manager.get_dataset_info()
            logger.info(f"Датасет успешно загружен. Записей: {info['rows']}, Колонок: {info['columns']}")
            
            # Логируем сэмпл данных для проверки
            sample = dataset_manager.get_sample_data(2)
            if sample:
                logger.debug(f"Сэмпл данных: {sample}")
            
            return True
        else:
            logger.error("Не удалось загрузить датасет")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при загрузке датасета: {e}")
        return False


def create_application() -> Application:
    """Создание и настройка приложения бота"""
    
    if not settings.is_valid:
        logging.error("BOT_TOKEN не установлен. Добавьте его в .env файл")
        raise ValueError("BOT_TOKEN не установлен")
    
    # Загружаем датасет перед созданием приложения
    if not load_dataset():
        logging.warning("Датасет не загружен, но продолжаем запуск бота")
    
    # Создаем Application
    application = Application.builder().token(settings.BOT_TOKEN).build()
    
    # Настраиваем ConversationHandler
    conversation_handler = setup_conversation_handler()
    application.add_handler(conversation_handler)
    
    logging.info(f"Бот {settings.BOT_NAME} инициализирован с ConversationHandler")
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
