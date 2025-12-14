from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config.settings import settings

import logging

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я — {settings.BOT_NAME}, ваш умный помощник по мерам государственной поддержки бизнеса.\n\n"
        "📋 **Что я умею:**\n"
        "• Искать меры поддержки по вашему запросу\n"
        "• Давать детальные консультации по выбранной мере\n"
        "• Отвечать на вопросы о требованиях, документах и условиях\n\n"
        "💡 **Как начать работу?**\n"
        "Просто опишите вашу ситуацию или задайте вопрос в свободной форме.\n\n"
        "Например: *«Хочу открыть кафе, какие есть программы поддержки?»*"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown"
    )


# Создаем обработчик команды /start
start_handler = CommandHandler("start", start_command)
