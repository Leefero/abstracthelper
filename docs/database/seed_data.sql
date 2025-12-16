-- тестовые категории
INSERT INTO categories (name, description, slug, order_index) VALUES
('Финансы', 'Финансовая поддержка бизнеса', 'finance', 1),
('Инновации', 'Поддержка инновационных проектов', 'innovations', 2),
('Экспорт', 'Поддержка экспортной деятельности', 'export', 3),
('Сельское хозяйство', 'Программы для АПК', 'agriculture', 4),
('IT и технологии', 'Поддержка IT-сектора', 'it-tech', 5)
ON CONFLICT (slug) DO NOTHING;

-- Вставляем администратора
INSERT INTO users (id, username, first_name, role) VALUES
(1, 'admin_bot', 'Администратор', 'admin')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- Создание ролей и прав доступа
-- ============================================

-- Создаем роль для приложения (если используется отдельный пользователь БД)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'support_bot_app') THEN
        CREATE ROLE support_bot_app WITH LOGIN PASSWORD 'secure_password_here';
    END IF;
END
$$;

-- Даем права на все таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO support_bot_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO support_bot_app;

-- ============================================
-- Комментарии к базе данных
-- ============================================
COMMENT ON DATABASE smart_support_bot IS 'База данных для Telegram-бота поиска мер господдержки';

-- ============================================
-- Проверка структуры
-- ============================================

-- Выводим список созданных таблиц
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
    (SELECT count(*) FROM information_schema.columns 
     WHERE table_name = t.table_name) as columns_count
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;

-- Выводим информацию об индексах
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
