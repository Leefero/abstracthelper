-- Создаем базу данных если не существует
CREATE DATABASE smart_support_bot 
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Подключаемся к созданной базе данных
\c smart_support_bot;

-- Создаем расширение для UUID если не существует
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Таблица пользователей
-- ============================================
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    is_bot BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    
    -- Индексы для быстрого поиска
    INDEX idx_users_username (username),
    INDEX idx_users_created_at (created_at),
    INDEX idx_users_last_active (last_active_at)
);

COMMENT ON TABLE users IS 'Пользователи Telegram-бота';
COMMENT ON COLUMN users.id IS 'Telegram ID пользователя (используется как первичный ключ)';
COMMENT ON COLUMN users.role IS 'Роль пользователя в системе';

-- ============================================
-- Таблица категорий мер поддержки
-- ============================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(255) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    order_index INTEGER DEFAULT 0,
    
    -- Индексы
    INDEX idx_categories_slug (slug),
    INDEX idx_categories_parent (parent_id),
    INDEX idx_categories_order (order_index),
    
    -- Ограничения
    CONSTRAINT unique_category_name UNIQUE (name)
);

COMMENT ON TABLE categories IS 'Категории мер государственной поддержки';
COMMENT ON COLUMN categories.slug IS 'URL-слаг для SEO и фильтрации';

-- ============================================
-- Таблица мер поддержки
-- ============================================
CREATE TABLE support_measures (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    conditions TEXT,
    support_size VARCHAR(500),
    deadline VARCHAR(255),
    contacts TEXT,
    link VARCHAR(1000),
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_to DATE,
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы
    INDEX idx_measures_title (title),
    INDEX idx_measures_category (category_id),
    INDEX idx_measures_active (is_active),
    INDEX idx_measures_dates (valid_from, valid_to),
    INDEX idx_measures_tags USING GIN (tags),
    
    -- Ограничения
    CONSTRAINT check_valid_dates CHECK (valid_from <= valid_to OR valid_to IS NULL)
);

COMMENT ON TABLE support_measures IS 'Меры государственной поддержки бизнеса';
COMMENT ON COLUMN support_measures.tags IS 'Теги для семантического поиска (JSON массив)';

-- ============================================
-- Таблица атрибутов мер поддержки
-- ============================================
CREATE TABLE measure_attributes (
    id SERIAL PRIMARY KEY,
    measure_id INTEGER NOT NULL REFERENCES support_measures(id) ON DELETE CASCADE,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_value TEXT NOT NULL,
    data_type VARCHAR(50) DEFAULT 'text',
    order_index INTEGER DEFAULT 0,
    
    -- Индексы
    INDEX idx_attributes_measure (measure_id),
    INDEX idx_attributes_name (attribute_name),
    INDEX idx_attributes_order (order_index),
    
    -- Ограничения
    CONSTRAINT unique_attribute_per_measure UNIQUE (measure_id, attribute_name)
);

COMMENT ON TABLE measure_attributes IS 'Дополнительные атрибуты мер поддержки';
COMMENT ON COLUMN measure_attributes.data_type IS 'Тип данных атрибута (text, number, date, boolean)';

-- ============================================
-- Таблица запросов пользователей
-- ============================================
CREATE TABLE user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_vector JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    results_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы
    INDEX idx_queries_user (user_id),
    INDEX idx_queries_created (created_at),
    INDEX idx_queries_vector USING GIN (query_vector)
);

COMMENT ON TABLE user_queries IS 'История запросов пользователей';
COMMENT ON COLUMN user_queries.query_vector IS 'Векторное представление запроса для семантического поиска';

-- ============================================
-- Таблица результатов поиска
-- ============================================
CREATE TABLE search_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL REFERENCES user_queries(id) ON DELETE CASCADE,
    measure_id INTEGER NOT NULL REFERENCES support_measures(id) ON DELETE CASCADE,
    relevance_score DECIMAL(5,4) NOT NULL,
    rank_position INTEGER NOT NULL,
    match_details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы
    INDEX idx_results_query (query_id),
    INDEX idx_results_measure (measure_id),
    INDEX idx_results_score (relevance_score),
    INDEX idx_results_position (rank_position),
    
    -- Ограничения
    CONSTRAINT check_relevance_score CHECK (relevance_score >= 0 AND relevance_score <= 1),
    CONSTRAINT unique_result_per_query UNIQUE (query_id, measure_id)
);

COMMENT ON TABLE search_results IS 'Результаты поиска по запросам пользователей';
COMMENT ON COLUMN search_results.relevance_score IS 'Оценка релевантности (0-1)';

-- ============================================
-- Таблица диалогов
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_id UUID REFERENCES user_queries(id) ON DELETE SET NULL,
    selected_measure_id INTEGER REFERENCES support_measures(id) ON DELETE SET NULL,
    current_state VARCHAR(100) DEFAULT 'START',
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    
    -- Индексы
    INDEX idx_conversations_user (user_id),
    INDEX idx_conversations_active (is_active),
    INDEX idx_conversations_state (current_state),
    INDEX idx_conversations_dates (started_at, ended_at),
    
    -- Ограничения
    CONSTRAINT check_end_date CHECK (ended_at IS NULL OR ended_at >= started_at)
);

COMMENT ON TABLE conversations IS 'Диалоги пользователей с ботом';
COMMENT ON COLUMN conversations.current_state IS 'Текущее состояние диалога (START, SEARCH, CONSULT, FEEDBACK)';

-- ============================================
-- Таблица сообщений в диалогах
-- ============================================
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'bot', 'system')),
    message_text TEXT,
    message_data JSONB DEFAULT '{}'::jsonb,
    intent VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы
    INDEX idx_messages_conversation (conversation_id),
    INDEX idx_messages_type (message_type),
    INDEX idx_messages_created (created_at),
    INDEX idx_messages_intent (intent)
);

COMMENT ON TABLE conversation_messages IS 'Сообщения в диалогах пользователей';
COMMENT ON COLUMN conversation_messages.intent IS 'Распознанный интент сообщения (для анализа)';

-- ============================================
-- Таблица обратной связи
-- ============================================
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    feedback_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы
    INDEX idx_feedback_user (user_id),
    INDEX idx_feedback_conversation (conversation_id),
    INDEX idx_feedback_rating (rating),
    INDEX idx_feedback_created (created_at),
    
    -- Ограничения
    CONSTRAINT unique_feedback_per_conversation UNIQUE (conversation_id)
);

COMMENT ON TABLE feedback IS 'Обратная связь от пользователей';
COMMENT ON COLUMN feedback.feedback_data IS 'Дополнительные данные обратной связи (метаданные)';

-- ============================================
-- Триггеры для обновления временных меток
-- ============================================

-- Триггер для обновления updated_at в support_measures
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_support_measures_updated_at 
    BEFORE UPDATE ON support_measures 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Триггер для обновления last_active_at в users
CREATE OR REPLACE FUNCTION update_user_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users 
    SET last_active_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_activity_queries
    AFTER INSERT ON user_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_active();

CREATE TRIGGER update_user_activity_conversations
    AFTER INSERT ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_active();

CREATE TRIGGER update_user_activity_feedback
    AFTER INSERT ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_active();

-- Триггер для подсчета сообщений в диалоге
CREATE OR REPLACE FUNCTION update_conversation_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET message_count = (
        SELECT COUNT(*) 
        FROM conversation_messages 
        WHERE conversation_id = NEW.conversation_id
    )
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_message_count_trigger
    AFTER INSERT ON conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_message_count();

-- ============================================
-- Представления для удобства
-- ============================================

-- Представление для активных мер поддержки
CREATE VIEW active_support_measures AS
SELECT 
    sm.*,
    c.name as category_name,
    c.slug as category_slug
FROM support_measures sm
LEFT JOIN categories c ON sm.category_id = c.id
WHERE sm.is_active = TRUE 
    AND (sm.valid_from IS NULL OR sm.valid_from <= CURRENT_DATE)
    AND (sm.valid_to IS NULL OR sm.valid_to >= CURRENT_DATE);

-- Представление для статистики пользователей
CREATE VIEW user_statistics AS
SELECT 
    u.id,
    u.username,
    u.first_name,
    u.created_at,
    u.last_active_at,
    COUNT(DISTINCT q.id) as query_count,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT f.id) as feedback_count,
    AVG(f.rating) as avg_rating
FROM users u
LEFT JOIN user_queries q ON u.id = q.user_id
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN feedback f ON u.id = f.user_id
GROUP BY u.id, u.username, u.first_name, u.created_at, u.last_active_at;

-- Представление для популярных мер поддержки
CREATE VIEW popular_measures AS
SELECT 
    sm.id,
    sm.title,
    sm.category_id,
    c.name as category_name,
    COUNT(DISTINCT sr.query_id) as search_appearances,
    COUNT(DISTINCT conv.id) as selections_count,
    AVG(sr.relevance_score) as avg_relevance_score
FROM support_measures sm
LEFT JOIN categories c ON sm.category_id = c.id
LEFT JOIN search_results sr ON sm.id = sr.measure_id
LEFT JOIN conversations conv ON sm.id = conv.selected_measure_id
GROUP BY sm.id, sm.title, sm.category_id, c.name
ORDER BY selections_count DESC, search_appearances DESC;

-- ============================================
-- Индексы полнотекстового поиска
-- ============================================

-- Индекс для полнотекстового поиска по названиям и описаниям мер
CREATE INDEX idx_measures_fts ON support_measures 
    USING gin(to_tsvector('russian', title || ' ' || description));

-- Индекс для поиска по тегам
CREATE INDEX idx_measures_tags_search ON support_measures 
    USING gin(tags);

