import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackContext, 
    CallbackQueryHandler
)

from bot.conversation.states import ConversationState
from data.dataset_manager import dataset_manager

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /start - начало диалога
    
    Returns:
        ConversationState.START - переход в состояние ожидания запроса
    """
    user = update.effective_user
    
    # Проверяем загружен ли датасет
    dataset_info = dataset_manager.get_dataset_info()
    dataset_status = "✅" if dataset_info.get('status') == 'loaded' else "⚠️"
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я — ваш умный помощник по мерам государственной поддержки бизнеса.\n"
        f"{dataset_status} База мер поддержки: {dataset_info.get('rows', 0)} записей\n\n"
        "🔍 **Как я могу помочь?**\n"
        "Просто опишите свою ситуацию, и я найду подходящие меры поддержки.\n\n"
        "📝 **Примеры запросов:**\n"
        "• \"Хочу открыть кафе, какие есть программы?\"\n"
        "• \"Ищу поддержку для сельского хозяйства\"\n"
        "• \"Какие есть гранты для ИП?\"\n\n"
        "⬇️ *Опишите ваш запрос ниже...*"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Примеры запросов", callback_data="show_examples")],
            [InlineKeyboardButton("📊 Статистика базы", callback_data="show_stats")]
        ])
    )
    
    # Очищаем данные предыдущего диалога
    context.user_data.clear()
    
    return ConversationState.START.value


async def handle_user_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка запроса пользователя в состоянии START
    
    Returns:
        ConversationState.SEARCH - переход к поиску и отображению результатов
    """
    user_query = update.message.text.strip()
    user = update.effective_user
    
    if not user_query:
        await update.message.reply_text(
            "Пожалуйста, опишите ваш запрос. Например: \"Какие есть программы поддержки малого бизнеса?\""
        )
        return ConversationState.START.value
    
    logger.info(f"Пользователь {user.id} ({user.username}): '{user_query}'")
    
    # Сохраняем запрос в контексте
    context.user_data['user_query'] = user_query
    context.user_data['query_timestamp'] = update.message.date
    
    # Имитируем поиск (заглушка для следующей задачи)
    # В задаче 2.3 здесь будет реальный поиск
    mock_results = [
        {"id": 1, "title": "Грант для начинающих предпринимателей", "match_score": 0.95},
        {"id": 2, "title": "Субсидия на открытие бизнеса", "match_score": 0.87},
        {"id": 3, "title": "Льготный кредит для малого бизнеса", "match_score": 0.78}
    ]
    
    context.user_data['search_results'] = mock_results
    
    # Отправляем сообщение о начале поиска
    search_message = await update.message.reply_text(
        f"🔍 Ищу подходящие меры поддержки по запросу:\n\"{user_query[:100]}{'...' if len(user_query) > 100 else ''}\"\n\n"
        "⏳ *Обрабатываю запрос...*",
        parse_mode="Markdown"
    )
    
    # Сохраняем ID сообщения для возможного редактирования
    context.user_data['search_message_id'] = search_message.message_id
    
    # Имитация обработки (задержка для реалистичности)
    import asyncio
    await asyncio.sleep(1)
    
    # Переходим к отображению результатов
    return await show_search_results(update, context)


async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отображение результатов поиска
    
    Returns:
        ConversationState.SEARCH - остаемся в состоянии отображения результатов
    """
    user_query = context.user_data.get('user_query', '')
    search_results = context.user_data.get('search_results', [])
    
    if not search_results:
        await update.message.reply_text(
            "😕 По вашему запросу не найдено подходящих мер поддержки.\n\n"
            "Попробуйте изменить формулировку или уточнить запрос.\n"
            "Например: \"поддержка для сельского хозяйства\" или \"гранты для ИП\""
        )
        return ConversationState.START.value
    
    # Формируем сообщение с результатами
    results_text = f"✅ Нашёл {len(search_results)} подходящих мер по запросу:\n\"{user_query[:80]}{'...' if len(user_query) > 80 else ''}\"\n\n"
    
    for i, result in enumerate(search_results, 1):
        results_text += f"{i}. **{result['title']}**\n"
        if 'description' in result:
            results_text += f"   {result['description'][:100]}...\n"
        results_text += f"   📊 Совпадение: {result.get('match_score', 0)*100:.0f}%\n\n"
    
    results_text += "👇 *Выберите наиболее подходящий вариант:*"
    
    # Создаем инлайн-кнопки для выбора результата
    keyboard = []
    for i, result in enumerate(search_results, 1):
        keyboard.append([
            InlineKeyboardButton(
                f"{i}. {result['title'][:30]}{'...' if len(result['title']) > 30 else ''}",
                callback_data=f"select_result_{result['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Новый поиск", callback_data="new_search"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_search")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем или обновляем сообщение с результатами
    if 'search_message_id' in context.user_data:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['search_message_id'],
                text=results_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Не удалось обновить сообщение: {e}")
            await update.message.reply_text(results_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(results_text, parse_mode="Markdown", reply_markup=reply_markup)
    
    return ConversationState.SEARCH.value


async def handle_result_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка выбора результата пользователем
    
    Returns:
        ConversationState.CONSULT - переход к детальной консультации
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("select_result_"):
        result_id = int(callback_data.split("_")[2])
        
        # Находим выбранный результат
        search_results = context.user_data.get('search_results', [])
        selected_result = next((r for r in search_results if r['id'] == result_id), None)
        
        if selected_result:
            context.user_data['selected_result'] = selected_result
            
            # Заглушка для детальной информации (будет в задаче 3.1)
            await query.edit_message_text(
                f"✅ Вы выбрали: **{selected_result['title']}**\n\n"
                f"📋 *Подготовка детальной информации...*\n\n"
                f"💡 Вы можете задавать вопросы по этой мере поддержки.\n"
                f"Например: \"Какие документы нужны?\" или \"Какой размер поддержки?\"\n\n"
                "⬇️ *Задайте ваш вопрос ниже...*",
                parse_mode="Markdown"
            )
            
            # Возвращаем состояние CONSULT (будет реализовано в задаче 3.1)
            # Пока вернемся в SEARCH
            return ConversationState.SEARCH.value
    
    elif callback_data == "new_search":
        await query.edit_message_text(
            "🔄 Начинаем новый поиск.\n\n"
            "⬇️ *Опишите ваш запрос ниже...*",
            parse_mode="Markdown"
        )
        return ConversationState.START.value
    
    elif callback_data == "cancel_search":
        await query.edit_message_text(
            "❌ Поиск отменен.\n\n"
            "Используйте /start для начала нового диалога.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    return ConversationState.SEARCH.value


async def handle_callback_examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для кнопки примеров запросов"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_examples":
        examples_text = (
            "📝 **Примеры запросов для поиска:**\n\n"
            "• \"Ищу гранты для открытия малого бизнеса\"\n"
            "• \"Какая есть поддержка для сельского хозяйства?\"\n"
            "• \"Программы для ИП в сфере услуг\"\n"
            "• \"Хочу получить субсидию на оборудование\"\n"
            "• \"Поддержка экспорта для производителей\"\n"
            "• \"Льготные кредиты для стартапов\"\n"
            "• \"Меры поддержки в IT-сфере\"\n\n"
            "💡 *Чем конкретнее запрос, тем точнее результаты!*"
        )
        
        await query.message.reply_text(examples_text, parse_mode="Markdown")
    
    elif query.data == "show_stats":
        dataset_info = dataset_manager.get_dataset_info()
        
        if dataset_info.get('status') == 'loaded':
            stats_text = (
                "📊 **Статистика базы мер поддержки:**\n\n"
                f"• Всего записей: {dataset_info.get('rows', 0)}\n"
                f"• Категорий: {len(set(dataset_info.get('categories', [])))}\n"
                f"• Последнее обновление: {dataset_info.get('last_loaded', 'неизвестно')}\n\n"
                f"📂 *Колонки в базе:*\n{', '.join(dataset_info.get('column_names', []))}"
            )
        else:
            stats_text = "⚠️ База данных не загружена или пуста."
        
        await query.message.reply_text(stats_text, parse_mode="Markdown")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды отмены /cancel"""
    await update.message.reply_text(
        "❌ Диалог прерван.\n\n"
        "Используйте /start для начала нового поиска."
    )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    return ConversationHandler.END


def setup_conversation_handler() -> ConversationHandler:
    """
    Создание и настройка ConversationHandler
    
    Returns:
        Настроенный ConversationHandler
    """
    logger.info("Настройка ConversationHandler...")
    
    # Создаем ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        
        states={
            ConversationState.START.value: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_query),
                CallbackQueryHandler(handle_callback_examples, pattern="^(show_examples|show_stats)$")
            ],
            
            ConversationState.SEARCH.value: [
                CallbackQueryHandler(handle_result_selection)
            ],
        },
        
        fallbacks=[
            CommandHandler('cancel', cancel_command),
            CommandHandler('start', start_command)
        ],
        
        # Настройки ConversationHandler
        allow_reentry=True,  # Разрешаем повторный вход в диалог
        per_chat=True,       # Отдельный диалог для каждого чата
        per_user=True,       # Отдельный диалог для каждого пользователя
        per_message=False,   # Не привязываем к сообщениям
    )
    
    logger.info(f"ConversationHandler настроен с состояниями: {[s.name for s in ConversationState]}")
    return conversation_handler
